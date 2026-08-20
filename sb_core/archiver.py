# sb_core/archiver.py
import os
import struct
import zlib
import hashlib
import tempfile
import shutil
from typing import Callable, Optional

from .constants import (
    MAGIC_HEADER,
    MAGIC_FOOTER,
    DEFAULT_BLOCK_SIZE,
    AlgorithmID,
    CompressionMode,
)
from .engines import get_engine_by_id
from .manifest import ArchiveManifest, FileEntry, scan_target, file_data_generator
from .preprocessors import ZipStreamPreprocessor
from .optimizer import BlockOptimizer

class SBArchiver:
    """Motor de archivado y compresión Super Binary (.sb) con arquitectura Streaming de bajo consumo de RAM."""
    def __init__(
        self,
        mode: CompressionMode = CompressionMode.EXTREME,
        block_size: int = DEFAULT_BLOCK_SIZE
    ):
        self.mode = mode
        self.block_size = block_size
        self.optimizer = BlockOptimizer(mode=mode)

    def compress(
        self,
        source_path: str,
        output_sb_path: str,
        progress_cb: Optional[Callable[[str, int, int, str], None]] = None
    ) -> dict:
        source_path = os.path.abspath(source_path)
        base_dir = os.path.dirname(source_path) if os.path.isfile(source_path) else source_path
        
        file_paths = scan_target(source_path)
        if not file_paths:
            raise ValueError(f"No se encontraron archivos en: {source_path}")

        total_files = len(file_paths)
        entries: list[FileEntry] = []
        current_offset = 0
        total_orig_bytes = 0
        total_uncompressed_size = 0
        
        temp_blocks_file = tempfile.NamedTemporaryFile(delete=False)
        temp_blocks_path = temp_blocks_file.name
        temp_blocks_file.close()

        solid_sha256_hasher = hashlib.sha256()
        block_buffer = bytearray()
        blocks_count = 0
        
        try:
            with open(temp_blocks_path, "wb") as b_out:
                for idx, file_p in enumerate(file_paths):
                    try:
                        entry, stream_payload = file_data_generator(file_p, base_dir, current_offset)
                    except Exception:
                        continue

                    entries.append(entry)
                    current_offset += len(stream_payload)
                    total_orig_bytes += entry.size
                    total_uncompressed_size += len(stream_payload)
                    solid_sha256_hasher.update(stream_payload)

                    block_buffer.extend(stream_payload)

                    while len(block_buffer) >= self.block_size:
                        chunk = bytes(block_buffer[: self.block_size])
                        block_buffer = block_buffer[self.block_size :]

                        block_crc = zlib.crc32(chunk) & 0xFFFFFFFF
                        alg_id, comp_chunk = self.optimizer.optimize_block(chunk)
                        
                        b_out.write(struct.pack(">BIII", alg_id, len(chunk), len(comp_chunk), block_crc))
                        b_out.write(comp_chunk)
                        blocks_count += 1

                        if progress_cb:
                            progress_cb("compressed_block", blocks_count, 0, AlgorithmID(alg_id).name)

                    if progress_cb and (idx % 50 == 0 or idx == total_files - 1):
                        progress_cb("scanned", idx + 1, total_files, entry.path)

                # Procesar remanente
                if len(block_buffer) > 0 or blocks_count == 0:
                    chunk = bytes(block_buffer)
                    block_crc = zlib.crc32(chunk) & 0xFFFFFFFF
                    alg_id, comp_chunk = self.optimizer.optimize_block(chunk)
                    
                    b_out.write(struct.pack(">BIII", alg_id, len(chunk), len(comp_chunk), block_crc))
                    b_out.write(comp_chunk)
                    blocks_count += 1
                    block_buffer.clear()

            # 2. Empaquetado de Metadatos y Manifiesto
            manifest = ArchiveManifest(
                version=1,
                block_size=self.block_size,
                total_uncompressed_size=total_uncompressed_size,
                files=entries,
            )
            manifest_raw = manifest.to_json_bytes()
            manifest_alg, manifest_comp = self.optimizer.optimize_block(manifest_raw)
            solid_sha256 = solid_sha256_hasher.digest()

            # 3. Ensamblado final del archivo .sb
            os.makedirs(os.path.dirname(os.path.abspath(output_sb_path)), exist_ok=True)
            with open(output_sb_path, "wb") as final_out:
                # Header
                final_out.write(MAGIC_HEADER)
                final_out.write(struct.pack(">BII", manifest_alg, len(manifest_raw), len(manifest_comp)))
                final_out.write(manifest_comp)

                # Transferencia de bloques comprimidos
                with open(temp_blocks_path, "rb") as b_in:
                    shutil.copyfileobj(b_in, final_out, length=1024 * 1024)

                # Footer
                final_out.write(struct.pack(">I", blocks_count))
                final_out.write(solid_sha256)
                final_out.write(MAGIC_FOOTER)

        finally:
            if os.path.exists(temp_blocks_path):
                os.remove(temp_blocks_path)

        output_size = os.path.getsize(output_sb_path)
        base_size = total_orig_bytes if total_orig_bytes > 0 else total_uncompressed_size
        ratio = (output_size / base_size * 100) if base_size > 0 else 0

        return {
            "uncompressed_size": base_size,
            "compressed_size": output_size,
            "ratio_percent": ratio,
            "savings_percent": 100 - ratio if base_size > 0 else 0,
            "files_count": len(entries),
            "blocks_count": blocks_count,
        }

    def decompress(
        self,
        sb_path: str,
        destination_dir: str,
        progress_cb: Optional[Callable[[str, int, int, str], None]] = None
    ) -> ArchiveManifest:
        sb_path = os.path.abspath(sb_path)
        destination_dir = os.path.abspath(destination_dir)

        with open(sb_path, "rb") as f:
            header = f.read(len(MAGIC_HEADER))
            if header != MAGIC_HEADER:
                raise ValueError("Archivo .sb no válido o cabecera corrupta.")

            manifest_meta = f.read(struct.calcsize(">BII"))
            manifest_alg, manifest_raw_len, manifest_comp_len = struct.unpack(">BII", manifest_meta)
            manifest_comp = f.read(manifest_comp_len)

            manifest_engine = get_engine_by_id(AlgorithmID(manifest_alg))
            manifest_raw = manifest_engine.decompress(manifest_comp)
            manifest = ArchiveManifest.from_json_bytes(manifest_raw)

            temp_solid_file = tempfile.NamedTemporaryFile(delete=False)
            temp_solid_path = temp_solid_file.name
            temp_solid_file.close()

            solid_sha256_hasher = hashlib.sha256()
            try:
                with open(temp_solid_path, "wb") as solid_out:
                    decompressed_total = 0
                    while True:
                        block_meta_raw = f.read(struct.calcsize(">BIII"))
                        if len(block_meta_raw) < struct.calcsize(">BIII"):
                            break
                        
                        f.seek(-struct.calcsize(">BIII"), os.SEEK_CUR)
                        current_pos = f.tell()
                        remaining_bytes = f.read()
                        if len(remaining_bytes) == struct.calcsize(">I") + 32 + len(MAGIC_FOOTER):
                            total_blocks, solid_sha256 = struct.unpack(">I32s", remaining_bytes[:struct.calcsize(">I32s")])
                            footer_magic = remaining_bytes[-len(MAGIC_FOOTER):]
                            if footer_magic == MAGIC_FOOTER:
                                break
                        
                        f.seek(current_pos)
                        block_meta_raw = f.read(struct.calcsize(">BIII"))
                        alg_id, uncomp_len, comp_len, block_crc = struct.unpack(">BIII", block_meta_raw)
                        compressed_block = f.read(comp_len)

                        engine = get_engine_by_id(AlgorithmID(alg_id))
                        decompressed_block = engine.decompress(compressed_block)

                        if (zlib.crc32(decompressed_block) & 0xFFFFFFFF) != block_crc:
                            raise ValueError(f"Error de integridad CRC32 en bloque comprimido con {AlgorithmID(alg_id).name}")

                        solid_out.write(decompressed_block)
                        solid_sha256_hasher.update(decompressed_block)
                        decompressed_total += len(decompressed_block)
                        
                        if progress_cb:
                            progress_cb("decompressed_block", decompressed_total, manifest.total_uncompressed_size, AlgorithmID(alg_id).name)

                if solid_sha256_hasher.digest() != solid_sha256:
                    raise ValueError("Fallo de verificación SHA256: el contenido del archivo .sb está alterado.")

                total_files = len(manifest.files)
                with open(temp_solid_path, "rb") as solid_in:
                    for idx, entry in enumerate(manifest.files):
                        solid_in.seek(entry.stream_offset)
                        raw_stream_slice = solid_in.read(entry.payload_len)

                        if entry.is_expanded_zip:
                            final_file_data = ZipStreamPreprocessor.rebuild_archive(entry.recipe.encode("utf-8"), raw_stream_slice)
                        else:
                            final_file_data = raw_stream_slice

                        out_file_path = os.path.join(destination_dir, entry.path)
                        os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
                        with open(out_file_path, "wb") as out_f:
                            out_f.write(final_file_data)

                        try:
                            os.utime(out_file_path, (entry.mtime, entry.mtime))
                        except Exception:
                            pass

                        if progress_cb and (idx % 50 == 0 or idx == total_files - 1):
                            progress_cb("extracted", idx + 1, total_files, entry.path)

            finally:
                if os.path.exists(temp_solid_path):
                    os.remove(temp_solid_path)

        return manifest

    def inspect(self, sb_path: str) -> ArchiveManifest:
        with open(sb_path, "rb") as f:
            header = f.read(len(MAGIC_HEADER))
            if header != MAGIC_HEADER:
                raise ValueError("Archivo .sb no válido o cabecera corrupta.")

            manifest_meta = f.read(struct.calcsize(">BII"))
            manifest_alg, manifest_raw_len, manifest_comp_len = struct.unpack(">BII", manifest_meta)
            manifest_comp = f.read(manifest_comp_len)

            manifest_engine = get_engine_by_id(AlgorithmID(manifest_alg))
            manifest_raw = manifest_engine.decompress(manifest_comp)
            return ArchiveManifest.from_json_bytes(manifest_raw)

    def extract_single_or_selected(
        self,
        sb_path: str,
        destination_dir: str,
        selected_paths: Optional[list[str]] = None
    ) -> list[str]:
        """Extrae únicamente los archivos seleccionados a destino."""
        temp_extract = tempfile.mkdtemp(prefix="sb_ext_")
        extracted_list = []
        try:
            manifest = self.decompress(sb_path, temp_extract)
            target_set = set(selected_paths) if selected_paths else {e.path for e in manifest.files}
            
            for entry in manifest.files:
                if entry.path in target_set:
                    src_f = os.path.join(temp_extract, entry.path)
                    dst_f = os.path.join(destination_dir, os.path.basename(entry.path))
                    os.makedirs(os.path.dirname(dst_f), exist_ok=True)
                    shutil.copy2(src_f, dst_f)
                    extracted_list.append(dst_f)
        finally:
            shutil.rmtree(temp_extract, ignore_errors=True)
        return extracted_list

    def delete_files_from_archive(self, sb_path: str, paths_to_delete: list[str]) -> dict:
        """Elimina archivos del archivo .sb recomprimiendo el contenido restante."""
        temp_dir = tempfile.mkdtemp(prefix="sb_del_")
        temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".sb")
        temp_out_path = temp_out.name
        temp_out.close()

        try:
            self.decompress(sb_path, temp_dir)
            del_set = set(paths_to_delete)

            for rel_p in del_set:
                full_p = os.path.join(temp_dir, rel_p)
                if os.path.isfile(full_p):
                    os.remove(full_p)
                elif os.path.isdir(full_p):
                    shutil.rmtree(full_p, ignore_errors=True)

            stats = self.compress(temp_dir, temp_out_path)
            shutil.move(temp_out_path, sb_path)
            return stats
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if os.path.exists(temp_out_path):
                os.remove(temp_out_path)

    def add_files_to_archive(self, sb_path: str, new_items: list[str]) -> dict:
        """Agrega nuevos archivos o carpetas a un archivo .sb existente."""
        temp_dir = tempfile.mkdtemp(prefix="sb_add_")
        temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".sb")
        temp_out_path = temp_out.name
        temp_out.close()

        try:
            if os.path.exists(sb_path) and os.path.getsize(sb_path) > 0:
                self.decompress(sb_path, temp_dir)

            for item in new_items:
                if not os.path.exists(item):
                    continue
                name = os.path.basename(item)
                target = os.path.join(temp_dir, name)
                if os.path.isdir(item):
                    if os.path.exists(target):
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)

            stats = self.compress(temp_dir, temp_out_path)
            shutil.move(temp_out_path, sb_path)
            return stats
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if os.path.exists(temp_out_path):
                os.remove(temp_out_path)

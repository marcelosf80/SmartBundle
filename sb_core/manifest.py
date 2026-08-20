# sb_core/manifest.py
import json
import os
import zlib
from dataclasses import dataclass
from typing import List, Generator

from .preprocessors import ZipStreamPreprocessor

@dataclass
class FileEntry:
    path: str              # Ruta relativa dentro del archivo .sb
    size: int              # Tamaño original del archivo en bytes
    payload_len: int       # Tamaño desempaquetado en el flujo continuo
    mtime: float           # Timestamp de modificación
    mode: int              # Permisos POSIX / Windows
    crc32: int             # Checksum CRC32 del archivo original
    stream_offset: int     # Desplazamiento global en el flujo continuo
    is_expanded_zip: bool = False
    recipe: str = ""

@dataclass
class ArchiveManifest:
    version: int
    block_size: int
    total_uncompressed_size: int
    files: List[FileEntry]

    def to_json_bytes(self) -> bytes:
        compact_files = [
            [
                f.path,
                f.size,
                f.payload_len,
                int(f.mtime),
                f.mode,
                f.crc32,
                f.stream_offset,
                1 if f.is_expanded_zip else 0,
                f.recipe
            ]
            for f in self.files
        ]
        data = {
            "v": self.version,
            "b": self.block_size,
            "s": self.total_uncompressed_size,
            "f": compact_files
        }
        return json.dumps(data, separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_json_bytes(cls, raw: bytes) -> "ArchiveManifest":
        data = json.loads(raw.decode("utf-8"))
        files = []
        for row in data["f"]:
            is_zip = bool(row[7]) if len(row) > 7 else False
            recipe = row[8] if len(row) > 8 else ""
            files.append(FileEntry(
                path=row[0],
                size=row[1],
                payload_len=row[2],
                mtime=float(row[3]),
                mode=row[4],
                crc32=row[5],
                stream_offset=row[6],
                is_expanded_zip=is_zip,
                recipe=recipe
            ))
        return cls(
            version=data["v"],
            block_size=data["b"],
            total_uncompressed_size=data["s"],
            files=files
        )

def scan_target(target_path: str) -> List[str]:
    """Escanea recursivamente archivos manteniendo orden determinista."""
    target_path = os.path.abspath(target_path)
    if os.path.isfile(target_path):
        return [target_path]
    
    file_list = []
    for root, _, files in os.walk(target_path):
        for f in sorted(files):
            file_list.append(os.path.join(root, f))
    return file_list

def file_data_generator(file_path: str, base_dir: str, current_offset: int) -> tuple[FileEntry, bytes]:
    """Lee y procesa un archivo individual de forma eficiente para streaming."""
    stat = os.stat(file_path)
    with open(file_path, "rb") as f:
        raw_content = f.read()

    rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
    crc = zlib.crc32(raw_content) & 0xFFFFFFFF

    is_expanded, recipe_json_bytes, stream_payload = ZipStreamPreprocessor.expand_archive(raw_content)
    recipe_str = recipe_json_bytes.decode("utf-8") if is_expanded else ""

    entry = FileEntry(
        path=rel_path,
        size=len(raw_content),
        payload_len=len(stream_payload),
        mtime=stat.st_mtime,
        mode=stat.st_mode,
        crc32=crc,
        stream_offset=current_offset,
        is_expanded_zip=is_expanded,
        recipe=recipe_str
    )
    return entry, stream_payload

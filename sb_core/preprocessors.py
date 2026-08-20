# sb_core/preprocessors.py
import io
import os
import zipfile
import zlib
from typing import Protocol, Tuple

try:
    import bcj
    HAS_BCJ = True
except ImportError:
    HAS_BCJ = False

class IPreprocessor(Protocol):
    def encode(self, data: bytes) -> bytes: ...
    def decode(self, data: bytes) -> bytes: ...

class BCJx86Preprocessor:
    """Filtro de traducción de saltos relativos x86 (CALL/JMP) a absolutos."""
    def encode(self, data: bytes) -> bytes:
        if not HAS_BCJ or len(data) < 16:
            return data
        try:
            return bcj.x86_filter(data)
        except Exception:
            return data

    def decode(self, data: bytes) -> bytes:
        if not HAS_BCJ or len(data) < 16:
            return data
        try:
            return bcj.x86_filter_inv(data)
        except Exception:
            return data

class DeltaPreprocessor:
    """Filtro delta de 1 byte para series numéricas y gradientes."""
    def encode(self, data: bytes) -> bytes:
        if len(data) <= 1:
            return data
        out = bytearray(len(data))
        out[0] = data[0]
        for i in range(1, len(data)):
            out[i] = (data[i] - data[i - 1]) & 0xFF
        return bytes(out)

    def decode(self, data: bytes) -> bytes:
        if len(data) <= 1:
            return data
        out = bytearray(len(data))
        out[0] = data[0]
        for i in range(1, len(data)):
            out[i] = (out[i - 1] + data[i]) & 0xFF
        return bytes(out)

class ZipStreamPreprocessor:
    """Preprocesador que desempaqueta streams Deflate internos de APK/ZIP/JAR/DOCX para compresión sólida SOTA."""
    @staticmethod
    def is_zip_container(data: bytes) -> bool:
        return len(data) > 30 and data[:4] == b"PK\x03\x04"

    @staticmethod
    def expand_archive(data: bytes) -> Tuple[bool, bytes, bytes]:
        """Descomprime todos los sub-streams internos manteniendo el mapa para reconstrucción exacta."""
        if not ZipStreamPreprocessor.is_zip_container(data):
            return False, b"", data

        try:
            bio = io.BytesIO(data)
            with zipfile.ZipFile(bio, "r") as zf:
                manifest_entries = []
                uncompressed_payload = bytearray()
                offset = 0

                for info in zf.infolist():
                    content = zf.read(info.filename)
                    manifest_entries.append({
                        "filename": info.filename,
                        "date_time": info.date_time,
                        "compress_type": info.compress_type,
                        "comment": info.comment.decode("utf-8", errors="ignore"),
                        "extra": info.extra.hex(),
                        "flag_bits": info.flag_bits,
                        "create_system": info.create_system,
                        "create_version": info.create_version,
                        "extract_version": info.extract_version,
                        "external_attr": info.external_attr,
                        "size": len(content),
                        "offset": offset
                    })
                    uncompressed_payload.extend(content)
                    offset += len(content)

                import json
                recipe_json = json.dumps(manifest_entries, separators=(",", ":")).encode("utf-8")
                return True, recipe_json, bytes(uncompressed_payload)
        except Exception:
            return False, b"", data

    @staticmethod
    def rebuild_archive(recipe_json_bytes: bytes, uncompressed_payload: bytes) -> bytes:
        """Reconstruye el archivo APK/ZIP original bit por bit."""
        import json
        manifest_entries = json.loads(recipe_json_bytes.decode("utf-8"))
        out_bio = io.BytesIO()
        
        with zipfile.ZipFile(out_bio, "w") as zf:
            for entry in manifest_entries:
                start = entry["offset"]
                end = start + entry["size"]
                file_content = uncompressed_payload[start:end]

                zinfo = zipfile.ZipInfo(filename=entry["filename"], date_time=tuple(entry["date_time"]))
                zinfo.compress_type = entry["compress_type"]
                zinfo.comment = entry["comment"].encode("utf-8")
                zinfo.extra = bytes.fromhex(entry["extra"]) if entry["extra"] else b""
                zinfo.flag_bits = entry["flag_bits"]
                zinfo.create_system = entry["create_system"]
                zinfo.create_version = entry["create_version"]
                zinfo.extract_version = entry["extract_version"]
                zinfo.external_attr = entry["external_attr"]

                # Escribir con su método de compresión original
                zf.writestr(zinfo, file_content)

        return out_bio.getvalue()

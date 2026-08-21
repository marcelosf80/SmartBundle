# sb_core/engines.py
import lzma
from typing import Protocol

import brotli
import zstandard as zstd
import pyppmd

from .constants import AlgorithmID
from .preprocessors import BCJx86Preprocessor, DeltaPreprocessor

class ICompressionEngine(Protocol):
    algorithm_id: AlgorithmID
    def compress(self, data: bytes) -> bytes: ...
    def decompress(self, data: bytes) -> bytes: ...

class PassthroughEngine:
    algorithm_id = AlgorithmID.PASSTHROUGH
    def compress(self, data: bytes) -> bytes: return data
    def decompress(self, data: bytes) -> bytes: return data

class ZstdUltraEngine:
    algorithm_id = AlgorithmID.ZSTD_ULTRA
    def __init__(self, level: int = 12):
        self.level = level
        self.cctx = zstd.ZstdCompressor(level=self.level, threads=-1)
        self.dctx = zstd.ZstdDecompressor()

    def compress(self, data: bytes) -> bytes:
        return self.cctx.compress(data)

    def decompress(self, data: bytes) -> bytes:
        return self.dctx.decompress(data)

class BrotliMaxEngine:
    algorithm_id = AlgorithmID.BROTLI_MAX
    def __init__(self, quality: int = 8):
        self.quality = quality

    def compress(self, data: bytes) -> bytes:
        return brotli.compress(data, quality=self.quality, lgwin=22)

    def decompress(self, data: bytes) -> bytes:
        return brotli.decompress(data)

class Lzma2ExtremeEngine:
    algorithm_id = AlgorithmID.LZMA2_EXTREME
    def __init__(self, preset: int = 6):
        self.preset = preset

    def compress(self, data: bytes) -> bytes:
        filters = [{
            "id": lzma.FILTER_LZMA2,
            "preset": self.preset,
            "dict_size": 16 * 1024 * 1024,
        }]
        return lzma.compress(data, format=lzma.FORMAT_RAW, filters=filters)

    def decompress(self, data: bytes) -> bytes:
        filters = [{"id": lzma.FILTER_LZMA2, "dict_size": 16 * 1024 * 1024}]
        return lzma.decompress(data, format=lzma.FORMAT_RAW, filters=filters)

class BcjLzma2Engine:
    algorithm_id = AlgorithmID.BCJ_LZMA2
    def __init__(self, preset: int = 6):
        self.bcj = BCJx86Preprocessor()
        self.lzma_engine = Lzma2ExtremeEngine(preset=preset)

    def compress(self, data: bytes) -> bytes:
        transformed = self.bcj.encode(data)
        return self.lzma_engine.compress(transformed)

    def decompress(self, data: bytes) -> bytes:
        decompressed_lzma = self.lzma_engine.decompress(data)
        return self.bcj.decode(decompressed_lzma)

class PpmdTextEngine:
    algorithm_id = AlgorithmID.PPMD_TEXT
    def __init__(self, max_order: int = 6, mem_size: int = 8 * 1024 * 1024):
        self.max_order = max_order
        self.mem_size = mem_size

    def compress(self, data: bytes) -> bytes:
        return pyppmd.compress(data, max_order=self.max_order, mem_size=self.mem_size)

    def decompress(self, data: bytes) -> bytes:
        return pyppmd.decompress(data, max_order=self.max_order, mem_size=self.mem_size)

class DeltaLzma2Engine:
    algorithm_id = AlgorithmID.DELTA_LZMA2
    def __init__(self, preset: int = 6):
        self.delta = DeltaPreprocessor()
        self.lzma_engine = Lzma2ExtremeEngine(preset=preset)

    def compress(self, data: bytes) -> bytes:
        transformed = self.delta.encode(data)
        return self.lzma_engine.compress(transformed)

    def decompress(self, data: bytes) -> bytes:
        decompressed_lzma = self.lzma_engine.decompress(data)
        return self.delta.decode(decompressed_lzma)

def get_engine_by_id(alg_id: AlgorithmID) -> ICompressionEngine:
    mapping = {
        AlgorithmID.PASSTHROUGH: PassthroughEngine,
        AlgorithmID.ZSTD_ULTRA: ZstdUltraEngine,
        AlgorithmID.BROTLI_MAX: BrotliMaxEngine,
        AlgorithmID.LZMA2_EXTREME: Lzma2ExtremeEngine,
        AlgorithmID.BCJ_LZMA2: BcjLzma2Engine,
        AlgorithmID.PPMD_TEXT: PpmdTextEngine,
        AlgorithmID.DELTA_LZMA2: DeltaLzma2Engine,
    }
    engine_cls = mapping.get(alg_id)
    if not engine_cls:
        raise ValueError(f"Algoritmo ID no soportado: {alg_id}")
    return engine_cls()

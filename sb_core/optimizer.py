# sb_core/optimizer.py
import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple

from .constants import AlgorithmID, CompressionMode
from .engines import (
    ICompressionEngine,
    PassthroughEngine,
    ZstdUltraEngine,
    BrotliMaxEngine,
    Lzma2ExtremeEngine,
    BcjLzma2Engine,
    PpmdTextEngine,
    DeltaLzma2Engine,
)

class BlockOptimizer:
    """Optimizador competitivo de ultra alto rendimiento."""
    def __init__(self, mode: CompressionMode = CompressionMode.BALANCED):
        self.mode = mode
        zstd_lvl = 7 if mode == CompressionMode.FAST else (12 if mode == CompressionMode.BALANCED else 16)
        brotli_q = 6 if mode == CompressionMode.FAST else (8 if mode == CompressionMode.BALANCED else 9)
        lzma_p = 4 if mode == CompressionMode.FAST else (6 if mode == CompressionMode.BALANCED else 7)

        self.engines: dict[AlgorithmID, ICompressionEngine] = {
            AlgorithmID.PASSTHROUGH: PassthroughEngine(),
            AlgorithmID.ZSTD_ULTRA: ZstdUltraEngine(level=zstd_lvl),
            AlgorithmID.BROTLI_MAX: BrotliMaxEngine(quality=brotli_q),
            AlgorithmID.LZMA2_EXTREME: Lzma2ExtremeEngine(preset=lzma_p),
            AlgorithmID.BCJ_LZMA2: BcjLzma2Engine(preset=lzma_p),
            AlgorithmID.PPMD_TEXT: PpmdTextEngine(),
            AlgorithmID.DELTA_LZMA2: DeltaLzma2Engine(preset=lzma_p),
        }

    @staticmethod
    def calculate_entropy(data: bytes) -> float:
        if not data:
            return 0.0
        # Muestra rápida de 16 KB para cálculo instantáneo (0.1ms)
        sample = data[:16384] if len(data) > 16384 else data
        n = len(sample)
        counts = Counter(sample)
        return -sum((c / n) * math.log2(c / n) for c in counts.values())

    @staticmethod
    def is_text_like(data: bytes) -> bool:
        sample = data[:4096]
        if not sample:
            return False
        printable = sum(1 for b in sample if 32 <= b <= 126 or b in (9, 10, 13))
        return (printable / len(sample)) > 0.85

    @staticmethod
    def is_executable(data: bytes) -> bool:
        if len(data) >= 4:
            if data[:2] == b"MZ" or data[:4] == b"\x7fELF":
                return True
            if data[:4] in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe"):
                return True
        return False

    def _compress_worker(self, alg_id: AlgorithmID, data: bytes) -> Tuple[AlgorithmID, bytes]:
        try:
            compressed = self.engines[alg_id].compress(data)
            return alg_id, compressed
        except Exception:
            return alg_id, data + b"\xff" * 100

    def optimize_block(self, data: bytes) -> Tuple[AlgorithmID, bytes]:
        if not data:
            return AlgorithmID.PASSTHROUGH, b""

        # Evitar re-comprimir datos con entropía casi máxima (> 7.98)
        if self.calculate_entropy(data) > 7.98:
            return AlgorithmID.PASSTHROUGH, data

        if self.mode == CompressionMode.FAST:
            fast_engine = self.engines[AlgorithmID.ZSTD_ULTRA]
            compressed = fast_engine.compress(data)
            if len(compressed) < len(data):
                return AlgorithmID.ZSTD_ULTRA, compressed
            return AlgorithmID.PASSTHROUGH, data

        if self.mode == CompressionMode.BALANCED:
            if self.is_text_like(data):
                candidates = [AlgorithmID.ZSTD_ULTRA, AlgorithmID.BROTLI_MAX]
            elif self.is_executable(data):
                candidates = [AlgorithmID.ZSTD_ULTRA, AlgorithmID.BCJ_LZMA2]
            else:
                candidates = [AlgorithmID.ZSTD_ULTRA]
        else: # EXTREME
            if self.is_text_like(data):
                candidates = [AlgorithmID.BROTLI_MAX, AlgorithmID.PPMD_TEXT, AlgorithmID.ZSTD_ULTRA]
            elif self.is_executable(data):
                candidates = [AlgorithmID.BCJ_LZMA2, AlgorithmID.ZSTD_ULTRA]
            else:
                candidates = [AlgorithmID.LZMA2_EXTREME, AlgorithmID.ZSTD_ULTRA]

        best_id = AlgorithmID.PASSTHROUGH
        best_data = data
        best_size = len(data)

        if len(candidates) == 1:
            alg_id, comp_data = self._compress_worker(candidates[0], data)
            if len(comp_data) < best_size:
                return alg_id, comp_data
            return AlgorithmID.PASSTHROUGH, data

        with ThreadPoolExecutor(max_workers=len(candidates)) as executor:
            futures = [executor.submit(self._compress_worker, cid, data) for cid in candidates]
            for future in as_completed(futures):
                alg_id, comp_data = future.result()
                if len(comp_data) < best_size:
                    best_size = len(comp_data)
                    best_id = alg_id
                    best_data = comp_data

        return best_id, best_data

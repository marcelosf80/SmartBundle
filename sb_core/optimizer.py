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
    """Optimizador competitivo multihilo que selecciona el menor tamaño en bytes por bloque."""
    def __init__(self, mode: CompressionMode = CompressionMode.EXTREME):
        self.mode = mode
        self.engines: dict[AlgorithmID, ICompressionEngine] = {
            AlgorithmID.PASSTHROUGH: PassthroughEngine(),
            AlgorithmID.ZSTD_ULTRA: ZstdUltraEngine(level=22 if mode == CompressionMode.EXTREME else 19),
            AlgorithmID.BROTLI_MAX: BrotliMaxEngine(),
            AlgorithmID.LZMA2_EXTREME: Lzma2ExtremeEngine(),
            AlgorithmID.BCJ_LZMA2: BcjLzma2Engine(),
            AlgorithmID.PPMD_TEXT: PpmdTextEngine(),
            AlgorithmID.DELTA_LZMA2: DeltaLzma2Engine(),
        }

    @staticmethod
    def calculate_entropy(data: bytes) -> float:
        if not data:
            return 0.0
        n = len(data)
        counts = Counter(data)
        return -sum((c / n) * math.log2(c / n) for c in counts.values())

    @staticmethod
    def is_text_like(data: bytes) -> bool:
        sample = data[:8192]
        if not sample:
            return False
        printable = sum(1 for b in sample if 32 <= b <= 126 or b in (9, 10, 13))
        return (printable / len(sample)) > 0.85

    @staticmethod
    def is_executable(data: bytes) -> bool:
        # Detección de cabeceras MZ (PE/Windows), ELF (Linux) o Mach-O (macOS)
        if len(data) >= 4:
            if data[:2] == b"MZ":
                return True
            if data[:4] == b"\x7fELF":
                return True
            if data[:4] in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe"):
                return True
        return False

    def _compress_worker(self, alg_id: AlgorithmID, data: bytes) -> Tuple[AlgorithmID, bytes]:
        try:
            compressed = self.engines[alg_id].compress(data)
            return alg_id, compressed
        except Exception:
            return alg_id, data + b"\xff" * 100  # Penalizar en caso de error

    def optimize_block(self, data: bytes) -> Tuple[AlgorithmID, bytes]:
        if not data:
            return AlgorithmID.PASSTHROUGH, b""

        # Si los datos tienen entropía casi máxima (> 7.98), son aleatorios o ya comprimidos
        entropy = self.calculate_entropy(data)
        if entropy > 7.98:
            return AlgorithmID.PASSTHROUGH, data

        if self.mode == CompressionMode.FAST:
            fast_engine = self.engines[AlgorithmID.ZSTD_ULTRA]
            compressed = fast_engine.compress(data)
            if len(compressed) < len(data):
                return AlgorithmID.ZSTD_ULTRA, compressed
            return AlgorithmID.PASSTHROUGH, data

        if self.mode == CompressionMode.BALANCED:
            if self.is_text_like(data):
                candidates = [AlgorithmID.BROTLI_MAX, AlgorithmID.PPMD_TEXT, AlgorithmID.ZSTD_ULTRA]
            elif self.is_executable(data):
                candidates = [AlgorithmID.BCJ_LZMA2, AlgorithmID.LZMA2_EXTREME]
            else:
                candidates = [AlgorithmID.LZMA2_EXTREME, AlgorithmID.ZSTD_ULTRA]
        else:
            # MODO EXTREME: Competencia abierta entre todos los motores SOTA
            if self.is_text_like(data):
                candidates = [
                    AlgorithmID.PPMD_TEXT,
                    AlgorithmID.BROTLI_MAX,
                    AlgorithmID.LZMA2_EXTREME,
                    AlgorithmID.ZSTD_ULTRA,
                ]
            elif self.is_executable(data):
                candidates = [
                    AlgorithmID.BCJ_LZMA2,
                    AlgorithmID.LZMA2_EXTREME,
                    AlgorithmID.ZSTD_ULTRA,
                ]
            else:
                candidates = [
                    AlgorithmID.LZMA2_EXTREME,
                    AlgorithmID.BCJ_LZMA2,
                    AlgorithmID.DELTA_LZMA2,
                    AlgorithmID.BROTLI_MAX,
                    AlgorithmID.PPMD_TEXT,
                    AlgorithmID.ZSTD_ULTRA,
                ]

        best_id = AlgorithmID.PASSTHROUGH
        best_data = data
        best_size = len(data)

        # Ejecución paralela multihilo para evaluar simultáneamente los candidatos
        with ThreadPoolExecutor(max_workers=len(candidates)) as executor:
            futures = [executor.submit(self._compress_worker, cid, data) for cid in candidates]
            for future in as_completed(futures):
                alg_id, comp_data = future.result()
                if len(comp_data) < best_size:
                    best_size = len(comp_data)
                    best_id = alg_id
                    best_data = comp_data

        return best_id, best_data

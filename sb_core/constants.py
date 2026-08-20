# sb_core/constants.py
from enum import IntEnum

MAGIC_HEADER = b"SB\x01\x00"
MAGIC_FOOTER = b"E\x01BS"

DEFAULT_BLOCK_SIZE = 16 * 1024 * 1024  # 16 MB solid blocks

class AlgorithmID(IntEnum):
    PASSTHROUGH = 0x00
    ZSTD_ULTRA = 0x01
    BROTLI_MAX = 0x02
    LZMA2_EXTREME = 0x03
    BCJ_LZMA2 = 0x04
    PPMD_TEXT = 0x05
    DELTA_LZMA2 = 0x06

class CompressionMode(IntEnum):
    FAST = 1      # Zstd Level 3 / Fast routing
    BALANCED = 2  # Heuristic selection (Zstd 19, Brotli 11, LZMA2 6)
    EXTREME = 3   # Competitive brute-force (tries all top engines per block and keeps smallest)

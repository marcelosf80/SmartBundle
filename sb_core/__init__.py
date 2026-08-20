# sb_core/__init__.py
from .constants import AlgorithmID, CompressionMode, MAGIC_HEADER, MAGIC_FOOTER
from .manifest import ArchiveManifest, FileEntry
from .archiver import SBArchiver

__version__ = "1.0.0"
__all__ = [
    "SBArchiver",
    "ArchiveManifest",
    "FileEntry",
    "AlgorithmID",
    "CompressionMode",
]

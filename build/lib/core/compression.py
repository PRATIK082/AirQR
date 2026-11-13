"""Compression service (Zstandard). Skip already-compressed formats."""
import os

SKIP_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mkv",
                   ".avi", ".mov", ".mp3", ".aac", ".ogg", ".flac", ".zip",
                   ".7z", ".gz", ".bz2", ".xz", ".rar", ".apk", ".exe", ".bin"}

SKIP_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp",
              "video/mp4", "video/x-matroska", "audio/mpeg", "audio/mp3",
              "application/zip", "application/x-7z-compressed",
              "application/gzip", "application/x-rar-compressed"}


def should_compress(path: str, mime: str = "") -> bool:
    ext = os.path.splitext(path)[1].lower()
    if ext in SKIP_EXTENSIONS:
        return False
    if mime in SKIP_MIMES:
        return False
    return True


def compress(data: bytes) -> bytes:
    import zstandard as zstd
    cctx = zstd.ZstdCompressor(level=3)
    return cctx.compress(data)


def decompress(data: bytes) -> bytes:
    import zstandard as zstd
    dctx = zstd.ZstdDecompressor()
    return dctx.decompress(data)

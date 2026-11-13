"""File chunking and reassembly."""
import math


def chunk_bytes(data: bytes, size: int) -> list:
    if size <= 0:
        raise ValueError("chunk size must be > 0")
    if not data:
        return [b""]
    return [data[i:i + size] for i in range(0, len(data), size)]


def assemble_chunks(chunks: dict, total: int) -> bytes:
    """chunks: {index: bytes}. Returns assembled bytes or None if incomplete."""
    if len(chunks) < total:
        return None
    out = bytearray()
    for i in range(total):
        if i not in chunks:
            return None
        out += chunks[i]
    return bytes(out)


def missing_indices(received: set, total: int) -> list:
    return [i for i in range(total) if i not in received]

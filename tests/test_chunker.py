import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.chunker import chunk_bytes, assemble_chunks, missing_indices


def test_chunk():
    data = b"abcdefghij"
    ch = chunk_bytes(data, 3)
    assert ch == [b"abc", b"def", b"ghi", b"j"]
    assert assemble_chunks({0: b"abc", 1: b"def", 2: b"ghi", 3: b"j"}, 4) == data
    assert assemble_chunks({0: b"abc"}, 4) is None
    assert missing_indices({0, 2}, 4) == [1, 3]

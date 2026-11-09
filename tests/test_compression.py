import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.compression import should_compress, compress, decompress


def test_skip():
    assert should_compress("a.jpg", "image/jpeg") is False
    assert should_compress("a.txt", "text/plain") is True


def test_roundtrip():
    data = b"hello " * 100
    c = compress(data)
    assert decompress(c) == data
    assert len(c) < len(data)

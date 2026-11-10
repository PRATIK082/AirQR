import sys, os, hashlib, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.integrity import crc32, sha256_bytes, sha256_file


def test_crc():
    assert crc32(b"abc") == 0x352441C2  # known? just consistency
    assert crc32(b"") == 0


def test_sha256_bytes():
    assert sha256_bytes(b"abc") == hashlib.sha256(b"abc").hexdigest()


def test_sha256_file():
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, "wb") as f:
        f.write(b"hello world")
    assert sha256_file(path) == hashlib.sha256(b"hello world").hexdigest()
    os.remove(path)

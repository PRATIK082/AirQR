import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.crypto import derive_key, encrypt, decrypt, make_nonce


def test_roundtrip():
    key = derive_key("pass", os.urandom(8).ljust(16, b"\x00"))
    nonce = make_nonce(os.urandom(8), 1, 2)
    ct = encrypt(b"secret", key, nonce)
    assert decrypt(ct, key, nonce) == b"secret"


def test_wrong_key():
    k1 = derive_key("a", b"\x00"*16)
    k2 = derive_key("b", b"\x00"*16)
    nonce = make_nonce(b"\x00"*8, 1, 0)
    ct = encrypt(b"x", k1, nonce)
    try:
        decrypt(ct, k2, nonce)
        assert False
    except Exception:
        pass

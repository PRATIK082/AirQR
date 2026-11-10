"""Encryption service: AES-256-GCM + Argon2id key derivation."""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type


def derive_key(passphrase: str, salt: bytes) -> bytes:
    salt = salt.ljust(16, b"\x00")[:16]
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=2,
        memory_cost=65536,
        parallelism=2,
        hash_len=32,
        type=Type.ID,
    )


def encrypt(data: bytes, key: bytes, nonce: bytes) -> bytes:
    aes = AESGCM(key)
    return aes.encrypt(nonce, data, None)


def decrypt(data: bytes, key: bytes, nonce: bytes) -> bytes:
    aes = AESGCM(key)
    return aes.decrypt(nonce, data, None)


def make_nonce(transfer_id: bytes, file_id: int, chunk_index: int) -> bytes:
    import hashlib
    h = hashlib.sha256()
    h.update(transfer_id)
    h.update(file_id.to_bytes(4, "little"))
    h.update(chunk_index.to_bytes(4, "little"))
    return h.digest()[:12]

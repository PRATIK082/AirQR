"""Transfer manifest encode/decode."""
import struct
import time
import mimetypes
import os


def guess_mime(path: str) -> str:
    m, _ = mimetypes.guess_type(path)
    return m or "application/octet-stream"


def collect_files(source) -> list:
    """Return list of dicts: {path (abs), rel (relative), size, mtime}."""
    out = []
    if os.path.isfile(source):
        out.append({"path": source, "rel": os.path.basename(source),
                    "size": os.path.getsize(source),
                    "mtime": int(os.path.getmtime(source))})
        return out
    base = source
    for root, _, files in os.walk(source):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, base)
            out.append({"path": full, "rel": rel,
                        "size": os.path.getsize(full),
                        "mtime": int(os.path.getmtime(full))})
    out.sort(key=lambda x: x["rel"])
    return out


def build_manifest(transfer_id: bytes, files: list, sha256s: list,
                   compression_methods: list, encrypted: bool,
                   salt: bytes, parity_count: int, chunk_size: int,
                   sender_label: str = "AirQR Sender") -> bytes:
    import hashlib
    parts = []
    parts.append(transfer_id.ljust(8, b"\x00")[:8])
    sb = sender_label.encode("utf-8")
    parts.append(struct.pack("<H", len(sb)) + sb)
    parts.append(salt.ljust(16, b"\x00")[:16])
    parts.append(struct.pack("<BII", parity_count, chunk_size, len(files)))
    for i, f in enumerate(files):
        name = f["rel"].encode("utf-8")
        mime = (f.get("mime") or guess_mime(f["path"])).encode("utf-8")
        sha = bytes.fromhex(sha256s[i])
        cm = compression_methods[i]
        enc = 1 if encrypted else 0
        parts.append(struct.pack("<H", len(name)) + name)
        parts.append(struct.pack("<Q", f["size"]))
        parts.append(struct.pack("<Q", f.get("compressed_size", f["size"])))
        parts.append(sha)  # 32 bytes
        parts.append(struct.pack("<H", len(mime)) + mime)
        parts.append(struct.pack("<IBBBQI", f["chunks"], cm, enc, 0, f["mtime"], i))
        # chunks filled later by caller; placeholder 0 -> caller must set f['chunks']
    return b"".join(parts)


def parse_manifest(data: bytes):
    off = 0
    transfer_id = data[off:off + 8]; off += 8
    (nlen,) = struct.unpack("<H", data[off:off + 2]); off += 2
    sender_label = data[off:off + nlen].decode("utf-8"); off += nlen
    salt = data[off:off + 16]; off += 16
    parity_count, chunk_size, file_count = struct.unpack("<BII", data[off:off + 9]); off += 9
    files = []
    for _ in range(file_count):
        (nlen,) = struct.unpack("<H", data[off:off + 2]); off += 2
        name = data[off:off + nlen].decode("utf-8"); off += nlen
        (size,) = struct.unpack("<Q", data[off:off + 8]); off += 8
        (csize,) = struct.unpack("<Q", data[off:off + 8]); off += 8
        sha = data[off:off + 32].hex(); off += 32
        (mlen,) = struct.unpack("<H", data[off:off + 2]); off += 2
        mime = data[off:off + mlen].decode("utf-8"); off += mlen
        chunks, cm, enc, _r, mtime, order = struct.unpack("<IBBBQI", data[off:off + 4 + 1 + 1 + 1 + 8 + 4])
        # careful: format "<IBBBQI" sizes: 4+1+1+1+8+4=19
        off += 19
        files.append({
            "name": name, "size": size, "compressed_size": csize, "sha256": sha, "mime": mime,
            "chunks": chunks, "compression": cm, "encrypted": bool(enc),
            "mtime": mtime, "order": order,
        })
    return {
        "transfer_id": transfer_id, "sender_label": sender_label, "salt": salt,
        "parity_count": parity_count, "chunk_size": chunk_size, "files": files,
    }

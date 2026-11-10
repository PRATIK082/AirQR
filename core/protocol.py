"""Compact binary packet format for AirQR.

Layout (little-endian), header = 30 bytes:
  magic        2 bytes  (b"AQ")
  version      1 byte
  transfer_id  8 bytes
  file_id      4 bytes (uint32)
  total_chunks 4 bytes (uint32)   # data + parity
  chunk_index  4 bytes (uint32)
  payload_len  2 bytes (uint16)
  crc32        4 bytes
  flags        1 byte
  payload      variable

Flags bits:
  0 compression (payload is zstd-compressed)
  1 encryption (payload is AES-256-GCM ciphertext)
  2 final data chunk of a file
  3 manifest packet
  4 transfer done
  5 ack packet
  6 parity/fec packet
"""
import struct
import base64
import zlib
from .integrity import crc32

MAGIC = b"AQ"
VERSION = 1
HEADER_FMT = "<2sB8sIIIHIB"  # 2+1+8+4+4+4+2+4+1 = 30
HEADER_SIZE = struct.calcsize(HEADER_FMT)

# flag bits
FLAG_COMPRESSED = 1 << 0
FLAG_ENCRYPTED = 1 << 1
FLAG_FINAL = 1 << 2
FLAG_MANIFEST = 1 << 3
FLAG_DONE = 1 << 4
FLAG_ACK = 1 << 5
FLAG_PARITY = 1 << 6


class Packet:
    __slots__ = ("version", "transfer_id", "file_id", "total_chunks",
                 "chunk_index", "payload", "crc", "flags")

    def __init__(self, transfer_id: bytes, file_id: int, total_chunks: int,
                 chunk_index: int, payload: bytes = b"", flags: int = 0,
                 version: int = VERSION):
        if len(transfer_id) != 8:
            transfer_id = transfer_id.ljust(8, b"\x00")[:8]
        self.version = version
        self.transfer_id = transfer_id
        self.file_id = file_id
        self.total_chunks = total_chunks
        self.chunk_index = chunk_index
        self.payload = payload
        self.crc = crc32(payload)
        self.flags = flags

    def encode(self) -> bytes:
        header = struct.pack(
            HEADER_FMT,
            MAGIC, self.version, self.transfer_id, self.file_id,
            self.total_chunks, self.chunk_index, len(self.payload),
            self.crc, self.flags,
        )
        return header + self.payload

    @staticmethod
    def decode(data: bytes) -> "Packet":
        if len(data) < HEADER_SIZE:
            raise ValueError("packet too short")
        magic, version, tid, fid, total, idx, plen, crc, flags = struct.unpack(
            HEADER_FMT, data[:HEADER_SIZE])
        if magic != MAGIC:
            raise ValueError("bad magic")
        payload = data[HEADER_SIZE:HEADER_SIZE + plen]
        if len(payload) != plen:
            raise ValueError("truncated payload")
        if crc32(payload) != crc:
            raise ValueError("crc mismatch")
        p = Packet(tid, fid, total, idx, payload, flags, version)
        p.crc = crc
        return p

    def to_qr(self) -> str:
        return base64.b64encode(self.encode()).decode("ascii")

    @staticmethod
    def from_qr(text: str) -> "Packet":
        text = text.strip()
        raw = base64.b64decode(text, validate=False)
        return Packet.decode(raw)


def make_ack(transfer_id: bytes, file_id: int, chunk_index: int, status: int = 0,
             missing: list = None) -> Packet:
    """status: 0=ok, 1=nak(missing list in payload)."""
    if missing:
        import struct as s
        payload = s.pack("<" + "I" * len(missing), *missing)
        flags = FLAG_ACK | FLAG_PARITY if False else FLAG_ACK
    else:
        payload = bytes([status])
    flags = FLAG_ACK
    if status == 1:
        flags |= 0  # nak indicated by payload[0]==1 when no list
    # encode missing list marker: if missing provided, payload starts with 0x01 then indices
    if missing:
        payload = bytes([1]) + struct.pack("<I", len(missing)) + struct.pack("<" + "I" * len(missing), *missing)
    else:
        payload = bytes([status])
    return Packet(transfer_id, file_id, 0, chunk_index, payload, flags)


def parse_ack(pkt: Packet):
    """Return (chunk_index, ok_bool, missing_list)."""
    if not (pkt.flags & FLAG_ACK):
        return None
    pl = pkt.payload
    if not pl:
        return pkt.chunk_index, True, []
    if pl[0] == 0:
        return pkt.chunk_index, True, []
    if pl[0] == 1:
        # nak with missing list
        import struct as s
        if len(pl) >= 5:
            count = s.unpack("<I", pl[1:5])[0]
            offs = 5
            missing = list(s.unpack("<" + "I" * count, pl[offs:offs + 4 * count]))
            return pkt.chunk_index, False, missing
        return pkt.chunk_index, False, []
    # simple nak
    return pkt.chunk_index, False, []

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.protocol import Packet, FLAG_MANIFEST, FLAG_ACK, make_ack, parse_ack


def test_roundtrip():
    tid = b"12345678"
    pkt = Packet(tid, 2, 5, 3, b"hello", 0)
    raw = pkt.encode()
    p2 = Packet.decode(raw)
    assert p2.transfer_id == tid
    assert p2.file_id == 2
    assert p2.total_chunks == 5
    assert p2.chunk_index == 3
    assert p2.payload == b"hello"
    assert p2.crc == pkt.crc


def test_qr_roundtrip():
    tid = os.urandom(8)
    pkt = Packet(tid, 1, 4, 0, b"abc", FLAG_MANIFEST)
    s = pkt.to_qr()
    p2 = Packet.from_qr(s)
    assert p2.payload == b"abc"
    assert p2.flags & FLAG_MANIFEST


def test_ack():
    tid = os.urandom(8)
    ack = make_ack(tid, 1, 5, 0)
    s = ack.to_qr()
    p = Packet.from_qr(s)
    idx, ok, missing = parse_ack(p)
    assert idx == 5
    assert ok is True
    assert missing == []


def test_ack_nak():
    tid = os.urandom(8)
    ack = make_ack(tid, 1, 0, 1, [2, 4])
    s = ack.to_qr()
    p = Packet.from_qr(s)
    idx, ok, missing = parse_ack(p)
    assert ok is False
    assert missing == [2, 4]

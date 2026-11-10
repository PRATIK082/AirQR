import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.recovery import rs_encode_chunks, rs_recover


def test_recover():
    chunks = [b"hello!", b"world!"]
    par = rs_encode_chunks(chunks, 2)
    avail = {1: chunks[1]}
    for i, p in enumerate(par):
        avail[2 + i] = p
    rec = rs_recover(avail, 2, 2)
    assert rec is not None
    assert 0 in rec
    # trim padding
    assert rec[0].startswith(b"hello")

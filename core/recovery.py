"""Forward error correction (Reed-Solomon) and retransmission helpers."""
from reedsolo import RSCodec


def rs_encode_chunks(chunks: list, parity_count: int) -> list:
    if parity_count <= 0 or not chunks:
        return []
    size = max((len(c) for c in chunks), default=0)
    padded = [c.ljust(size, b"\x00") for c in chunks]
    n = len(chunks)
    parity = [bytearray() for _ in range(parity_count)]
    rsc = RSCodec(parity_count)
    for pos in range(size):
        col = bytes(padded[i][pos] for i in range(n))
        enc = rsc.encode(col)
        for j in range(parity_count):
            parity[j].append(enc[n + j])
    return [bytes(p) for p in parity]


def rs_recover(chunks: dict, data_count: int, parity_count: int) -> dict:
    """Given available chunks (index->bytes) among 0..data_count+parity_count-1,
    recover missing data chunks. Returns {index: bytes} for recovered data chunks or None."""
    total = data_count + parity_count
    available = [i for i in range(total) if i in chunks]
    missing = [i for i in range(total) if i not in chunks]
    if len(missing) > parity_count or not missing:
        return {} if not missing else None
    size = max((len(chunks[i]) for i in available), default=0)
    rsc = RSCodec(parity_count)
    recovered = {i: bytearray() for i in missing if i < data_count}
    try:
        for pos in range(size):
            codeword = bytearray(total)
            for i in available:
                b = chunks[i]
                codeword[i] = b[pos] if pos < len(b) else 0
            _msg, full, _err = rsc.decode(codeword, erase_pos=missing)
            for i in missing:
                if i < data_count:
                    recovered[i].append(full[i])
    except Exception:
        return None
    return {i: bytes(recovered[i]) for i in recovered}

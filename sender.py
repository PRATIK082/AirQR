"""Sender: read files, encode as binary QR stream, handle ACKs."""
import os
import sys
import time
import struct
import argparse
import getpass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import protocol as P
from core.protocol import (Packet, FLAG_COMPRESSED, FLAG_ENCRYPTED, FLAG_FINAL,
                           FLAG_MANIFEST, FLAG_DONE, FLAG_PARITY, FLAG_ACK,
                           make_ack, parse_ack)
from core.manifest import collect_files, build_manifest, guess_mime
from core.compression import should_compress, compress
from core.crypto import derive_key, encrypt, make_nonce
from core.chunker import chunk_bytes
from core.integrity import sha256_file, sha256_bytes
from core.recovery import rs_encode_chunks
from core.adaptive import choose_chunk_size, choose_ec
from qr_utils import QRDisplay, QRScanner

MAX_RETRIES = 3
ACK_TIMEOUT = 2.0
MANIFEST_CHUNK = 800
PARITY_COUNT = 2
RETRY_ROUNDS = 3


def is_ack_transfer(s, transfer_id):
    try:
        p = Packet.from_qr(s)
        return bool(p.flags & FLAG_ACK) and p.transfer_id == transfer_id
    except Exception:
        return False


def send_transfer(source, passphrase=None, display_mode="image", camera_id=0, web_mode=False, broadcast=False):
    files = collect_files(source)
    if not files:
        print("No files found.")
        return

    # Prepare per-file data
    file_meta = []  # list of dicts
    file_plain_chunks = []  # list of list[bytes] (compressed, pre-encryption)
    file_compressed = []  # bool
    for f in files:
        raw = open(f["path"], "rb").read()
        f["mime"] = guess_mime(f["path"])
        comp = False if web_mode else should_compress(f["path"], f["mime"])
        if comp:
            data = compress(raw)
        else:
            data = raw
        chunk_size = choose_chunk_size(len(raw), f["mime"])
        chunks = chunk_bytes(data, chunk_size)
        file_plain_chunks.append(chunks)
        file_compressed.append(comp)
        file_meta.append({
            "path": f["path"], "rel": f["rel"], "size": f["size"],
            "mtime": f["mtime"], "mime": f["mime"],
            "chunks": len(chunks), "compressed_size": len(data),
            "compression": 1 if comp else 0,
        })

    transfer_id = os.urandom(8)
    if web_mode:
        passphrase = None
    encrypted = (not web_mode) and bool(passphrase)
    salt = transfer_id if encrypted else b"\x00" * 16
    key = derive_key(passphrase, salt) if encrypted else None
    parity_count = 0 if web_mode else PARITY_COUNT

    sha256s = [sha256_file(f["path"]) for f in files]
    comp_methods = [1 if c else 0 for c in file_compressed]
    manifest_bytes = build_manifest(transfer_id, file_meta, sha256s,
                                   comp_methods, encrypted, salt, parity_count,
                                   choose_chunk_size(0, ""), "AirQR Sender")
    # fix chunk_size in manifest: use per-file? manifest expects single chunk_size. Use 900.
    # rebuild with a representative chunk size
    chunk_size_global = 900
    manifest_bytes = build_manifest(transfer_id, file_meta, sha256s,
                                   comp_methods, encrypted, salt, parity_count,
                                   chunk_size_global, "AirQR Sender")

    print(f"Transfer ID: {transfer_id.hex()}")
    print(f"Files: {len(files)}, Encrypted: {encrypted}")
    print("Position receiver camera, then press ENTER to start.")
    input()

    display = QRDisplay(display_mode)
    if broadcast:
        try:
            mchunks = chunk_bytes(manifest_bytes, MANIFEST_CHUNK)
            bpkts = []
            for i, mc in enumerate(mchunks):
                bpkts.append(Packet(transfer_id, 0xFFFFFFFF, len(mchunks), i, mc, FLAG_MANIFEST))
            # prepare file packets (reuse logic)
            file_packets_local = {}
            for fi, f in enumerate(files):
                fid = fi + 1
                plain_chunks = file_plain_chunks[fi]
                dc = len(plain_chunks)
                parity_plain = rs_encode_chunks(plain_chunks, parity_count) if parity_count > 0 else []
                total = dc + len(parity_plain)
                pkts = {}
                for ci, chunk in enumerate(plain_chunks):
                    p = chunk
                    flags = FLAG_COMPRESSED if file_compressed[fi] else 0
                    if encrypted:
                        nonce = make_nonce(transfer_id, fid, ci)
                        p = encrypt(p, key, nonce)
                        flags |= FLAG_ENCRYPTED
                    if ci == dc - 1:
                        flags |= FLAG_FINAL
                    pkt = Packet(transfer_id, fid, total, ci, p, flags)
                    pkts[ci] = pkt
                for pj, par in enumerate(parity_plain):
                    p = par
                    flags = FLAG_PARITY
                    if file_compressed[fi]:
                        flags |= FLAG_COMPRESSED
                    if encrypted:
                        nonce = make_nonce(transfer_id, fid, dc + pj)
                        p = encrypt(p, key, nonce)
                        flags |= FLAG_ENCRYPTED
                    pkt = Packet(transfer_id, fid, total, dc + pj, p, flags)
                    pkts[dc + pj] = pkt
                file_packets_local[fid] = pkts
            for fid in sorted(file_packets_local):
                for ci in sorted(file_packets_local[fid]):
                    bpkts.append(file_packets_local[fid][ci])
            bpkts.append(Packet(transfer_id, 0, 0, 0, b"", FLAG_DONE))
            print("Broadcast mode: streaming packets. Press Ctrl+C to stop.")
            while True:
                for pkt in bpkts:
                    display.show(pkt.to_qr())
                    time.sleep(1.2)
        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            display.close()
        return

    scanner = QRScanner(camera_id)
    scanner.__enter__()

    try:
        # Send manifest
        mchunks = chunk_bytes(manifest_bytes, MANIFEST_CHUNK)
        mtotal = len(mchunks)
        print(f"Sending manifest ({mtotal} chunks)...")
        for i, mc in enumerate(mchunks):
            pkt = Packet(transfer_id, 0xFFFFFFFF, mtotal, i, mc, FLAG_MANIFEST)
            ok = _send_with_ack(pkt, display, scanner, transfer_id)
            if not ok:
                print(f"Manifest chunk {i} failed")

        # Prepare file packets
        file_packets = {}  # fid -> {chunk_index: Packet}
        for fi, f in enumerate(files):
            fid = fi + 1
            plain_chunks = file_plain_chunks[fi]
            dc = len(plain_chunks)
            # parity over plain chunks
            parity_plain = rs_encode_chunks(plain_chunks, parity_count) if parity_count > 0 else []
            total = dc + len(parity_plain)
            pkts = {}
            # data chunks
            for ci, chunk in enumerate(plain_chunks):
                p = chunk
                flags = FLAG_COMPRESSED if file_compressed[fi] else 0
                if encrypted:
                    nonce = make_nonce(transfer_id, fid, ci)
                    p = encrypt(p, key, nonce)
                    flags |= FLAG_ENCRYPTED
                if ci == dc - 1:
                    flags |= FLAG_FINAL
                pkt = Packet(transfer_id, fid, total, ci, p, flags)
                pkts[ci] = pkt
            # parity
            for pj, par in enumerate(parity_plain):
                p = par
                flags = FLAG_PARITY
                if file_compressed[fi]:
                    flags |= FLAG_COMPRESSED
                if encrypted:
                    nonce = make_nonce(transfer_id, fid, dc + pj)
                    p = encrypt(p, key, nonce)
                    flags |= FLAG_ENCRYPTED
                pkt = Packet(transfer_id, fid, total, dc + pj, p, flags)
                pkts[dc + pj] = pkt
            file_packets[fid] = (pkts, dc, len(parity_plain))
            print(f"Sending file {fi + 1}/{len(files)}: {f['rel']} ({dc} chunks)")
            for ci in range(total):
                pkt = pkts[ci]
                ok = _send_with_ack(pkt, display, scanner, transfer_id)
                if not ok:
                    print(f"  chunk {ci} failed (FEC may recover)")

        # Done
        done_pkt = Packet(transfer_id, 0, 0, 0, b"", FLAG_DONE)
        for _ in range(3):
            display.show(done_pkt.to_qr())
            time.sleep(0.5)

        # Recovery rounds
        for rnd in range(RETRY_ROUNDS):
            raw = scanner.scan(timeout=3.0, filter_fn=lambda s: is_ack_transfer(s, transfer_id))
            if not raw:
                break
            try:
                ap = Packet.from_qr(raw)
            except Exception:
                break
            ok, missing = parse_ack(ap)[:2] if False else (None, None)
            _ok, _missing = _parse_ack_simple(ap)
            if _missing is None or not _missing:
                print("Receiver reports complete.")
                break
            fid = ap.file_id
            if fid not in file_packets:
                continue
            pkts, dc, pc = file_packets[fid]
            print(f"Retransmitting {len(_missing)} chunks for file {fid}")
            for mi in _missing:
                if mi in pkts:
                    _send_with_ack(pkts[mi], display, scanner, transfer_id)

        print("Transfer finished.")
    finally:
        scanner.release()
        display.close()


def _parse_ack_simple(ap):
    # returns (ok_bool, missing_list)
    pl = ap.payload
    if not pl:
        return True, []
    if pl[0] == 0:
        return True, []
    if pl[0] == 1:
        import struct as s
        if len(pl) >= 5:
            count = s.unpack("<I", pl[1:5])[0]
            offs = 5
            missing = list(s.unpack("<" + "I" * count, pl[offs:offs + 4 * count]))
            return False, missing
        return False, []
    return False, []


def _send_with_ack(pkt, display, scanner, transfer_id):
    def filt(s):
        try:
            ap = Packet.from_qr(s)
            return (ap.flags & FLAG_ACK and ap.transfer_id == transfer_id
                    and ap.file_id == pkt.file_id and ap.chunk_index == pkt.chunk_index)
        except Exception:
            return False
    data_str = pkt.to_qr()
    for attempt in range(MAX_RETRIES):
        display.show(data_str)
        ack_str = scanner.scan(timeout=ACK_TIMEOUT, filter_fn=filt)
        if ack_str:
            try:
                ap = Packet.from_qr(ack_str)
                pl = ap.payload
                if pl and pl[0] == 0:
                    return True
                if pl and pl[0] == 1:
                    # nak -> retry
                    pass
                else:
                    return True
            except Exception:
                pass
        time.sleep(0.1)
    return False


def main():
    parser = argparse.ArgumentParser(prog="airqr")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_send = sub.add_parser("send")
    p_send.add_argument("source")
    p_send.add_argument("--encrypt", action="store_true")
    p_send.add_argument("--passphrase", default=None)
    p_send.add_argument("--display", default="image", choices=["image", "ascii"])
    p_send.add_argument("--camera", type=int, default=0)
    p_send.add_argument("--web", action="store_true", help="Web-compatible: no compression/encryption/FEC")
    p_send.add_argument("--broadcast", action="store_true", help="Broadcast/loop packets without ACK (for mobile/web receivers)")
    args = parser.parse_args()
    passphrase = args.passphrase
    if args.encrypt and not passphrase:
        passphrase = getpass.getpass("Passphrase: ")
    if args.cmd == "send":
        send_transfer(args.source, passphrase, args.display, args.camera, args.web, args.broadcast)


if __name__ == "__main__":
    main()

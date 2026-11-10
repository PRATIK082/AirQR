"""Receiver: scan QR stream, reassemble files, verify integrity."""
import os
import sys
import time
import argparse
import getpass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import protocol as P
from core.protocol import (Packet, FLAG_COMPRESSED, FLAG_ENCRYPTED, FLAG_FINAL,
                           FLAG_MANIFEST, FLAG_DONE, FLAG_PARITY, FLAG_ACK,
                           make_ack, parse_ack)
from core.manifest import parse_manifest
from core.compression import decompress
from core.crypto import derive_key, decrypt, make_nonce
from core.chunker import assemble_chunks
from core.integrity import sha256_file
from core.recovery import rs_recover
from qr_utils import QRDisplay, QRScanner


def is_data_any(s):
    try:
        p = Packet.from_qr(s)
        return not (p.flags & FLAG_ACK)
    except Exception:
        return False


def receive_transfer(dest, passphrase=None, display_mode="image", camera_id=0, resume=False):
    os.makedirs(dest, exist_ok=True)
    display = QRDisplay(display_mode)
    scanner = QRScanner(camera_id)
    scanner.__enter__()

    transfer_id = None
    manifest = None
    manifest_chunks = {}
    manifest_total = 0
    files_data = {}  # fid -> dict
    done_received = False
    key = None
    encrypted = False
    salt = None

    def process_packet(pkt):
        nonlocal transfer_id, manifest, key, encrypted, salt, passphrase
        if transfer_id is None:
            transfer_id = pkt.transfer_id
        if pkt.flags & FLAG_MANIFEST:
            manifest_chunks[pkt.chunk_index] = pkt.payload
            # ack
            ack = make_ack(pkt.transfer_id, pkt.file_id, pkt.chunk_index, 0)
            display.show(ack.to_qr())
            if len(manifest_chunks) == pkt.total_chunks and manifest is None:
                mbytes = assemble_chunks(manifest_chunks, pkt.total_chunks)
                manifest = parse_manifest(mbytes)
                encrypted = any(f.get("encrypted") for f in manifest["files"])
                salt = manifest["salt"]
                if encrypted:
                    if not passphrase:
                        # prompt
                        nonlocal_pass = None
                    # derive key later when passphrase known
                parity_count = manifest["parity_count"]
                for fi, f in enumerate(manifest["files"]):
                    fid = fi + 1
                    files_data[fid] = {
                        "info": f, "chunks": {}, "data_count": f["chunks"],
                        "parity_count": parity_count, "received": set(),
                    }
                print(f"Manifest received: {len(manifest['files'])} files")
            return
        if pkt.flags & FLAG_DONE:
            done_received = True
            ack = make_ack(pkt.transfer_id, 0, 0, 0)
            display.show(ack.to_qr())
            return
        fid = pkt.file_id
        if fid not in files_data:
            return
        fd = files_data[fid]
        # decrypt if needed
        payload = pkt.payload
        if pkt.flags & FLAG_ENCRYPTED:
            if key is None:
                # prompt passphrase
                if passphrase is None:
                    passphrase = getpass.getpass("Passphrase: ")
                key = derive_key(passphrase, salt)
            nonce = make_nonce(pkt.transfer_id, fid, pkt.chunk_index)
            try:
                payload = decrypt(payload, key, nonce)
            except Exception as e:
                print("Decryption failed:", e)
                return
        fd["chunks"][pkt.chunk_index] = payload
        fd["received"].add(pkt.chunk_index)
        ack = make_ack(pkt.transfer_id, fid, pkt.chunk_index, 0)
        display.show(ack.to_qr())
        # progress
        dc = fd["data_count"]
        have = sum(1 for i in range(dc) if i in fd["chunks"])
        print(f"\rFile {fid}: {have}/{dc} chunks", end="", flush=True)

    def all_complete():
        if manifest is None:
            return False
        for fid, fd in files_data.items():
            dc = fd["data_count"]
            pc = fd["parity_count"]
            # try recovery
            if not all(i in fd["chunks"] for i in range(dc)):
                recovered = rs_recover(fd["chunks"], dc, pc)
                if recovered:
                    for idx, b in recovered.items():
                        fd["chunks"][idx] = b
                        fd["received"].add(idx)
            if not all(i in fd["chunks"] for i in range(dc)):
                return False
        return done_received

    try:
        print("Scanning for QR codes... (press q in camera window to quit)")
        while not all_complete():
            raw = scanner.scan(timeout=2.0, filter_fn=is_data_any)
            if raw is None:
                continue
            try:
                pkt = Packet.from_qr(raw)
            except Exception:
                continue
            process_packet(pkt)

        # Recovery rounds for missing
        for rnd in range(3):
            if all(i in fd["chunks"] for fid, fd in files_data.items() for i in range(fd["data_count"])):
                # all data present
                pass
            # check missing
            missing_any = False
            for fid, fd in files_data.items():
                dc = fd["data_count"]
                missing = [i for i in range(dc) if i not in fd["chunks"]]
                if missing:
                    missing_any = True
                    nak = make_ack(transfer_id, fid, 0, 1, missing)
                    display.show(nak.to_qr())
                    print(f"\nRequesting {len(missing)} missing chunks for file {fid}")
            if not missing_any:
                break
            # scan for retransmissions
            end = time.time() + 4
            while time.time() < end:
                raw = scanner.scan(timeout=0.5, filter_fn=is_data_any)
                if raw is None:
                    continue
                try:
                    pkt = Packet.from_qr(raw)
                except Exception:
                    continue
                process_packet(pkt)
            if all_complete():
                break

        # Reassemble and save
        print("\nVerifying and saving files...")
        for fid, fd in files_data.items():
            info = fd["info"]
            dc = fd["data_count"]
            pc = fd["parity_count"]
            # recovery one more time
            if not all(i in fd["chunks"] for i in range(dc)):
                recovered = rs_recover(fd["chunks"], dc, pc)
                if recovered:
                    for idx, b in recovered.items():
                        fd["chunks"][idx] = b
            chunks_dict = {i: fd["chunks"][i] for i in range(dc) if i in fd["chunks"]}
            compressed_data = assemble_chunks(chunks_dict, dc)
            if compressed_data is None:
                print(f"File {fid} incomplete, skipping")
                continue
            if info.get("compression", 0) == 1:
                try:
                    raw_data = decompress(compressed_data)
                except Exception as e:
                    print(f"Decompression failed: {e}")
                    raw_data = compressed_data
            else:
                raw_data = compressed_data
            raw_data = raw_data[:info["size"]]
            rel = info["name"]
            out_path = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(out_path) or dest, exist_ok=True)
            # duplicate detection
            if os.path.exists(out_path):
                try:
                    if sha256_file(out_path) == info["sha256"]:
                        print(f"Duplicate (already exists): {rel}")
                        continue
                except Exception:
                    pass
            with open(out_path, "wb") as f:
                f.write(raw_data)
            try:
                os.utime(out_path, (info["mtime"], info["mtime"]))
            except Exception:
                pass
            # verify
            actual = sha256_file(out_path)
            if actual == info["sha256"]:
                print(f"Saved & verified: {rel} ({info['size']} bytes)")
            else:
                print(f"WARNING: hash mismatch for {rel}")
                print(f"  expected {info['sha256']}")
                print(f"  actual   {actual}")
    finally:
        scanner.release()
        display.close()


def main():
    parser = argparse.ArgumentParser(prog="airqr")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_recv = sub.add_parser("receive")
    p_recv.add_argument("--dest", default="./received")
    p_recv.add_argument("--resume", action="store_true")
    p_recv.add_argument("--display", default="image", choices=["image", "ascii"])
    p_recv.add_argument("--camera", type=int, default=0)
    p_recv.add_argument("--passphrase", default=None)
    args = parser.parse_args()
    if args.cmd == "receive":
        receive_transfer(args.dest, args.passphrase, args.display, args.camera, args.resume)


if __name__ == "__main__":
    main()

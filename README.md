# AirQR — Take Any File Anywhere. Leave Zero Trace.

> **Every download today leaves a trail** — ISP logs, Wi-Fi records, cloud audits, USB fingerprints, email attachments.
> AirQR moves files as **light on a screen**. No packets, no network, no logs — nothing to intercept, trace, or subpoena.

![Animated demo](docs/demo/demo.gif)

## Why AirQR exists
- 📵 **Zero-trace transfer** — screen → camera. No internet, Wi-Fi, Bluetooth, USB data, cloud, account, pairing, or server. There is simply nothing on any network to record.
- 🔒 **Secure data, physically contained** — files never traverse a cable or router you don't control. What the camera can't see, nobody can copy.
- 🕵️ **No forensic footprint on the PC** — no browser history of a download, no USB insertion event, no cloud sync log. The sender just displays QRs.
- ✈️ **Works where networks don't (or must not)** — airplanes, vaults, labs, field sites, locked-down offices. If you can see the screen, you can receive.
- 📱 **Non-technical friendly** — install one app, tap Start Scan, point at the screen. Files land in Downloads by themselves.
- 🛡️ **Still verifiable** — CRC32 per chunk + SHA-256 per file, AES-256-GCM + Argon2id optional encryption, Reed-Solomon FEC.

Transfer files between a PC and a phone (or PC↔PC) using only animated QR codes on the sender's screen and the receiver's camera.

## Features
- Fully offline binary protocol (chunked, CRC32 + SHA-256)
- Compression (Zstd, skips already-compressed media)
- AES-256-GCM + Argon2id encryption
- Reed-Solomon FEC + selective retransmission + resume
- Folder structure preservation
- PC CLI + Web PWA (mobile send & receive)
- Broadcast mode for laptop→mobile (no ACK)

## Install
```bash
pip install .
# or: pip install -e .
```

## Quick Start
```bash
# Receiver (PC)
airqr receive --dest ./downloads

# Sender (PC)
airqr send ./my_folder

# Laptop → Mobile (no ACK)
airqr send ./folder --web --broadcast
```

## Mobile (PWA)
```bash
python framework/run.py
```
Open `http://<PC-IP>:8765/index.html` on phone → **Add to Home screen**. Use Receive/Send tabs.

## Demo
![Sender](docs/demo/sender.png) ![Receiver](docs/demo/receiver.png)

## Docs
- [Usage](docs/usage.md) · [Protocol](docs/protocol.md) · [Architecture](docs/architecture.md) · [Troubleshooting](docs/troubleshooting.md) · [Install](docs/install.md) · [Competitive Research](docs/competitive_research.md)

## Requirements
Python 3.10+, webcam. See [install.md](docs/install.md). Status: v1 (Python) + web PWA. Native mobile apps on roadmap (PLAN.md).

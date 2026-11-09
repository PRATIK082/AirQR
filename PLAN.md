# AirQR — Product Plan, Requirements & Roadmap

> Offline-first, cross-platform QR-code file transfer system.
> Sender screen displays animated QR codes; receiver camera scans them.
> No internet, Wi-Fi, Bluetooth, mobile data, cloud, account, pairing, or server required.

**Repository:** https://github.com/PRATIK082/AirQR
**Status:** Prototype (Python) → Production plan (this document)
**Last updated:** 2026-11-09

---

## 0. Current Prototype (existing code)

The repo currently contains a working Python prototype (`main.py`, `sender.py`, `receiver.py`, `qr_utils.py`, `protocol.py`, `state.py`) that:

- Splits files into ~1200-byte chunks, encodes each as a QR code shown on screen.
- Receiver scans with OpenCV, reassembles chunks, writes files.
- Bidirectional ACK protocol: receiver shows ACK QR; sender retries on timeout (3 attempts, 3s).
- Integrity: CRC32 per chunk + MD5 per file.
- Resume via `transfer_state.json`.
- Display modes: OpenCV window (auto-sized, always-on-top) or ASCII art.
- CLI: `python main.py sender --source DIR` / `python main.py receiver --dest DIR [--resume]`.

**Prototype gaps vs. production spec:** JSON-based (not compact binary) packets, MD5 (not SHA-256), no compression, no encryption, no FEC, no folder structure preservation, no mobile apps, no web PWA, no i18n, no accessibility modes.

---

## 1. Product Requirement Document (PRD)

### 1.1 Goal
Enable transfer of any file or folder between PC and mobile using only the sender's screen (animated QR codes) and the receiver's camera. Fully offline after install.

### 1.2 Core Requirements
1. Any file type: PDF, images, video, audio, documents, ZIP, 7z, APK, EXE, arbitrary binary.
2. Single files, multiple files, folders.
3. Preserve filenames, folder structure, file sizes, MIME types, modification dates where possible.
4. Bidirectional: PC screen → phone camera; phone screen → PC webcam.
5. Fully offline after installation.
6. UI: beautiful, simple, modern, accessible; dark/light/large-text/high-contrast modes.
7. Localization: English, Hindi, Marathi, Kannada, Spanish, French, Arabic, Chinese.

### 1.3 Non-Goals
- No internet, network, cloud, account, pairing, or server dependency.
- No automatic execution of received files.

---

## 2. User Flows

### 2.1 PC → Phone
1. Sender (PC): drag-and-drop file/folder or CLI `airqr send myfile.zip`.
2. Sender selects options (compression, encryption, speed).
3. Sender enters fullscreen QR presenter mode; QR stream begins.
4. Receiver (phone): opens app, taps "Scan", grants camera permission.
5. Phone scans; live progress (%, speed, ETA, received/missing chunks).
6. On completion: verify SHA-256; show file name, size, type, sender label, hash.
7. User confirms save to Downloads / chosen folder; optional sender-confirmation QR.
8. Duplicate detection via SHA-256; transfer history stored locally.

### 2.2 Phone → PC
1. Sender (phone): select file/folder; show QR on phone screen.
2. Receiver (PC): `airqr receive --output ./downloads`; webcam scans phone screen.
3. Same progress/verification/save flow.

### 2.3 Primary flow target: < 10 seconds Select → Show QR → Scan → Receive → Save.

---

## 3. Wireframes (textual)

- **Sender Home**: drop zone, queue list, "Start transfer" CTA, settings (density/speed/EC/brightness/color).
- **Sender Presenting**: fullscreen QR, progress bar, speed, ETA, chunk counter, retry status, pause/resume/cancel.
- **Receiver Scanning**: camera preview with QR overlay, progress ring, received/missing chunks, pause/resume.
- **Receiver Complete**: file preview (image/PDF/text/audio/video), save location, open (with executable warning), share.
- **Error/Low-light**: permission prompts, low-light guidance, camera-permission guidance, recovery states.
- **States**: Ready, Scanning, Transferring, Paused, Recovering, Verifying, Complete, Failed; plus empty/error/permission states.

Design: premium, minimal, trustworthy; large QR, strong contrast, generous quiet zone, prominent progress.

---

## 4. System Architecture

Modular layers:
- Core transfer engine
- QR encoder / QR decoder
- Chunker
- Compression service
- Encryption service
- Integrity verifier
- Recovery manager
- UI layer
- Platform adapters: Windows, macOS, Linux, Android, iOS, Web

```
┌─────────────────────────────────────────────────────┐
│                    UI Layer                         │
│  Desktop (Tauri/Electron)  Mobile (Compose/SwiftUI)  │
│  Web PWA (WebCodecs/Camera API/Workers/WASM)        │
├─────────────────────────────────────────────────────┤
│              Platform Adapters                      │
│  FS, Camera, Display, Notifications, Storage        │
├─────────────────────────────────────────────────────┤
│              Core Transfer Engine                   │
│  Chunker · Manifest · Scheduler · Recovery · State  │
├──────────────┬──────────────┬───────────────────────┤
│ QR Encoder   │ QR Decoder   │ Compression (Zstd/7z) │
│ (native)     │ (ML Kit/     │ Encryption            │
│              │  ZXing/Vision)│ (AES-256-GCM+Argon2id)│
├──────────────┴──────────────┴───────────────────────┤
│ Integrity: CRC32 (chunk) + SHA-256 (file)           │
│ FEC: Reed-Solomon / RaptorQ erasure coding          │
└─────────────────────────────────────────────────────┘
```

### Technology Stack
- Desktop: Tauri or Electron with Rust/TypeScript.
- Mobile: Kotlin + Jetpack Compose (Android); Swift + SwiftUI (iOS).
- QR gen: high-performance native QR library.
- QR decode: ML Kit, ZXing, or native Vision/MLKit.
- Compression: Zstandard.
- Encryption: AES-256-GCM + Argon2id.
- Testing: unit, integration, camera sim, low-light sim, motion-blur sim, corrupted-frame tests.

---

## 5. Binary Packet Format Specification

Compact binary (not JSON). Fields in order:

| Field | Size | Description |
|-------|------|-------------|
| Magic bytes | 2 bytes | `0x41 0x51` ("AQ") |
| Protocol version | 1 byte | e.g. `0x01` |
| Transfer ID | 8 bytes | unique per transfer |
| File ID | 4 bytes | index within transfer |
| Total chunk count | 4 bytes (uint32) | |
| Current chunk index | 4 bytes (uint32) | |
| Payload length | 2 bytes (uint16) | |
| CRC32 | 4 bytes | checksum of payload |
| Flags | 1 byte | bit0 compression, bit1 encryption, bit2 final chunk, bit3 manifest |
| Payload | variable | binary chunk data |

Endianness: little-endian. Max QR payload sized to fit chosen QR version/EC level.

### Manifest (separate packet type, flag bit3)
Contains per file:
- File name (UTF-8, length-prefixed)
- File size (uint64)
- SHA-256 (32 bytes)
- MIME type (string)
- Chunk count (uint32)
- Compression method (enum)
- Encryption flag (bool)
- File order index (uint32)

---

## 6. Error Recovery & Resumable Transfer Design

- Receiver tracks received chunk bitmap per file.
- Detects missing chunks; requests selective retransmission via ACK/NAK QR.
- ACK protocol: receiver shows ACK QR with status (ok/nak) + file/chunk index; sender retries on timeout (configurable).
- Pause/resume/cancel/retry/background transfer supported.
- State persisted to local storage (JSON/state DB) for resume across restarts.
- FEC (Reed-Solomon / RaptorQ): sender emits parity frames; receiver can reconstruct a limited number of missing frames without retransmission.
- Adaptive streaming: auto-select QR version, EC level, chunk size, frame interval, compression based on file type, screen size, lighting estimate, scan success rate.
- Optimized for glare, motion blur, low light, unstable hands (high contrast, large QR, generous quiet zone, dynamic frame interval).

---

## 7. Security & Privacy Threat Model

- Optional AES-256-GCM encryption; key derived via Argon2id from passphrase.
- Show file name, size, type, sender label, SHA-256 before open/save.
- Never auto-execute received files.
- Warn before opening executable/script/archive.
- No upload to any server; all processing local.
- Threats: shoulder-surfing (QR visible), malicious crafted files, replay, tampering. Mitigations: encryption, integrity hashes, user confirmation, no auto-exec, local-only.

---

## 8. Performance Benchmarks & Target Metrics

Target: transfer 100 MB ZIP reliably PC→phone with resume, verification, optional encryption, polished mobile UX.

Metrics to track:
- Throughput (KB/s) per QR version/EC/chunk size.
- Frame success rate under low light / motion blur.
- Retry rate, recovery time.
- End-to-end time for 100 MB.
- Memory/CPU on mobile.

Benchmarks: camera sim, low-light sim, motion-blur sim, corrupted-frame tests.

---

## 9. MVP Feature List

MVP (v1):
- Desktop sender (Windows/macOS/Linux) + Android receiver.
- Single/multi-file + folder transfer.
- Binary packets, CRC32, SHA-256.
- Compression (Zstd) for text/docs; skip for media/archives.
- Optional AES-256-GCM encryption.
- Resume + selective retransmission.
- Basic adaptive QR params.
- English + one additional language.
- Dark/light modes.

Post-MVP:
- iOS receiver, web PWA, FEC, full i18n (8 langs), accessibility modes, watch-folder, CLI, external monitor/TV, preview, history, duplicate detection.

---

## 10. Full Development Roadmap

Phase 0 — Prototype (done): Python CLI transfer.
Phase 1 — Core engine (Rust/TS): binary protocol, chunker, manifest, integrity, state.
Phase 2 — Compression & encryption services.
Phase 3 — Desktop app (Tauri) with presenter + CLI + watch-folder.
Phase 4 — Android receiver (Compose) with camera decoder + progress + save.
Phase 5 — Recovery manager + FEC + adaptive streaming.
Phase 6 — iOS receiver.
Phase 7 — Web PWA fallback.
Phase 8 — i18n + accessibility modes.
Phase 9 — Testing harness (camera/low-light/motion-blur/corrupted frames) + benchmarks.
Phase 10 — Hardening, security review, release.

---

## 11. Production-Ready Code Structure (target)

```
airqr/
├── core/                 # transfer engine (Rust crate or TS package)
│   ├── protocol/         # binary packet encode/decode
│   ├── chunker/
│   ├── manifest/
│   ├── integrity/        # CRC32, SHA-256
│   ├── compression/
│   ├── crypto/           # AES-256-GCM, Argon2id
│   ├── recovery/         # FEC, retransmission
│   └── state/            # resume persistence
├── qr/
│   ├── encoder/          # native QR gen
│   └── decoder/          # ML Kit / ZXing / Vision
├── desktop/              # Tauri app (sender + receiver)
│   ├── src/              # TS UI
│   └── src-tauri/        # Rust
├── mobile/
│   ├── android/          # Kotlin + Compose
│   └── ios/              # Swift + SwiftUI
├── web/                  # PWA
├── cli/                  # airqr command
├── i18n/                 # locale files
├── tests/
└── docs/
```

---

## 12. Competitive Analysis (QRCast, QR Forge, etc.)

Analyze existing QR-based offline transfer tools without copying code/design/branding:
- Protocol assumptions (JSON vs binary, chunk sizes, ACK strategy).
- QR frame size & speed approach.
- Error-recovery strategy (retry vs selective retransmission vs FEC).
- Compression approach.
- Mobile receiver UX.
- Missing features (folder structure, encryption, resume, accessibility, i18n).
- Performance bottlenecks (QR gen latency, scan cycle delays).
- Security weaknesses (no encryption, auto-open, no hash verification).

AirQR differentiators: compact binary packets, SHA-256 verification, optional AES-256-GCM+Argon2id, Reed-Solomon/RaptorQ FEC, adaptive streaming, folder reconstruction, accessibility modes, 8-language i18n, web PWA fallback, no auto-exec with warnings.

---

## 13. README, Installation, Privacy & License

- **README**: usage, CLI reference, troubleshooting, architecture notes (see current README.md; to be updated alongside implementation).
- **Installation guide**: per-platform install (desktop installers, APK/TestFlight, PWA).
- **Privacy policy**: no data collection, no network, local-only processing, no accounts.
- **License recommendation**: Apache-2.0 or MIT for code; CC-BY for docs (final decision pending).

---

## 14. Open Questions / Decisions Pending
- Desktop framework final choice: Tauri vs Electron.
- FEC library: Reed-Solomon vs RaptorQ.
- Mobile decoder: ML Kit vs ZXing vs native.
- Chunk size defaults & adaptive thresholds (needs benchmarking).
- Whether to keep Python prototype as reference implementation.

---

## Appendix A — CLI (target)
```
airqr send myfile.zip
airqr send folder/ --encrypt
airqr receive --output ./downloads
```
Options: `--resume`, `--display image|ascii`, compression/encryption flags, speed/density controls.
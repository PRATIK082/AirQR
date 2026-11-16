# AirQR Native Mobile Apps

Native receiver/sender apps fill the gap left by the Web PWA:
- Web depends on `BarcodeDetector` (Chrome) or `jsQR` fallback → lower throughput (~1-3 fps effective).
- Native uses **ML Kit (Android)** / **Vision (iOS)** → 10-30 fps, faster auto-focus, better low-light handling.

Both apps implement the same `AQ` binary protocol as `core/protocol.py` (base64 QR → 30-byte header + payload, CRC32, manifest).

## Structure

- `android/` — Kotlin + CameraX + ML Kit + Jetpack Compose (receiver + sender, tunable params)
- `ios/` — Swift + SwiftUI + AVFoundation + Vision (receiver + sender, tunable params)

## Tunable sender params (both natives + web)

- Chunk size bytes (200-2000, default 800)
- Frame interval ms (500-3000, default 1200)
- QR box size / display size
- Parity count (native supports 0-4; web fixed 0)
- Manifest chunk size (desktop CLI `--manifest-chunk`)

Live preview shows: file size → chunk count, total frames, est. loop time.

## Build

See `android/README.md` and `ios/README.md`.

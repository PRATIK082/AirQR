# AirQR Mobile Guide

## Options

| Option | Speed | Install | Notes |
|---|---|---|---|
| Web PWA (`web/`) | ~1-5 fps | Add to Home screen | Chrome best; `jsQR` fallback for Safari/Firefox |
| Android native (`mobile/android`) | 10-30 fps (ML Kit) | Android Studio / APK | Tunable chunk/frame/QR/parity UI |
| iOS native (`mobile/ios`) | 10-30 fps (Vision) | Xcode / device | Tunable chunk/frame/QR UI |

## Sender params (all platforms)

- **Chunk size** bytes: 200-2000, default 800. Smaller = more reliable, more frames. `chunks = ceil(file_size / chunk_size)`.
- **Frame interval** ms: 500-3000, default 1200. Time each QR stays on screen.
- **QR size** px: 180-480 (web), display scale (native).
- **Parity/FEC**: 0-4. Web fixed 0; native + desktop support FEC recovery.
- **Manifest chunk**: desktop `--manifest-chunk` (default 800).

Live preview shows: per-file bytes → chunks, total frames (data + manifest + done), est. loop time.

## Desktop CLI equivalents

```bash
airqr send ./folder --chunk-size 800 --parity 2 --frame-interval 1.2 --manifest-chunk 800 --broadcast --web
```

- `--broadcast` required for mobile/web receivers (no ACK).
- `--web` for web-compatible (no compression/encryption/FEC).

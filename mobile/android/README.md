# AirQR Android App

Native receiver/sender using CameraX + ML Kit Barcode Scanning + Jetpack Compose.

## Why native
- 10-30 fps scan vs ~1-5 fps web (`BarcodeDetector`/`jsQR`)
- Better autofocus, low-light, motion-blur handling
- Background-capable, save to Downloads via MediaStore

## Build
1. Open `mobile/android` in Android Studio (Hedgehog+).
2. Sync Gradle, connect device, Run `app`.
3. Grant Camera permission.

## Sender params UI
Chunk size (200-2000), frame interval ms, QR size px, parity 0-4 with live chunk-count preview (`SenderParams.chunkCount`, est. loop time).

## Protocol
Same as `core/protocol.py`: base64 QR → `AQ` magic, 30-byte LE header, CRC32, flags. See `protocol/AirQrPacket.kt`, `protocol/Manifest.kt`, `transfer/TransferSession.kt`.

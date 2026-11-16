# AirQR Android App

One app, zero network. Install once, receive files forever with no WiFi, no hotspot, no internet.

## Install (no technical steps on the phone)

1. On your **PC**, open this repo on GitHub → **Actions** tab → latest **android-apk** run → download **AirQR-android-apk**.
2. Copy `app-debug.apk` to the phone over USB cable.
3. On the phone, tap the APK → **Install** (allow "install unknown apps" if asked).
4. Open **AirQR** → allow Camera.

## Receive a file (non-technical)

1. On the **PC**, in the AirQR folder:
```powershell
airqr send E:\My_Project\My_Github\QR_Transfer --web --broadcast --chunk-size 500 --frame-interval 2.0
```
The PC screen starts looping QR codes. Leave it.
2. On the **phone**, open AirQR → **Receive** tab → **Start Scan** → point at the PC screen (~20 cm, avoid glare).
3. Files save themselves to **Downloads/AirQR**. Done.

No URLs, no IPs, no settings, no network of any kind.

## For developers

Native receiver/sender using CameraX + ML Kit Barcode Scanning (bundled model, works offline) + Jetpack Compose.

- Open `mobile/android` in Android Studio (Hedgehog+), sync Gradle, Run `app`.
- Or push to GitHub: `.github/workflows/android-apk.yml` builds the APK automatically.
- Chunk size (200-2000), frame interval ms, QR size px, parity 0-4 with live chunk-count preview (`SenderParams.chunkCount`, est. loop time).

## Protocol

Same as `core/protocol.py`: base64 QR → `AQ` magic, 30-byte LE header, CRC32, flags. See `protocol/AirQrPacket.kt`, `protocol/Manifest.kt`, `transfer/TransferSession.kt`.

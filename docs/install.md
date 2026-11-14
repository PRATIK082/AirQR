# Installation Guide

## Desktop (Python package)

### Install from source (Windows / Linux / macOS)
1. Install Python 3.10+.
2. Clone the repo:
   ```
   git clone https://github.com/PRATIK082/AirQR.git
   cd AirQR
   ```
3. Install the package:
   ```
   pip install .
   ```
   (or editable: `pip install -e .`)
4. Run:
   ```
   airqr send ./my_folder
   airqr receive --dest ./downloads
   ```

### Run without installing
- Windows: `py airqr_cli.py send ./my_folder` or `airqr.bat send ./my_folder`
- macOS/Linux: `python3 airqr_cli.py send ./my_folder`

## Mobile (full support via PWA)
The web app now supports **both sending and receiving** on mobile browsers:
1. Start framework: `python framework/run.py`
2. On phone, open `http://<PC-IP>:8765/index.html` in Chrome.
3. Tap **Add to Home screen** to install.
4. Use **Receive** tab to scan; **Send** tab to pick a file and stream QR codes.
5. Mobile web uses uncompressed transfers; PC sender should use `--web` for compatibility.

### Laptop → Mobile (no ACK)
Mobile receivers cannot easily display ACK QR codes, so use broadcast mode:
```
py airqr send ./folder --web --broadcast
```
This streams packets in a loop; the mobile receiver scans at its own pace (duplicates are ignored).
   Or on Windows without install: `python main.py send ./my_folder`.

## Web Fallback (PWA) on Mobile
1. Serve the `web/` folder (e.g. `python -m http.server 8080` inside `web/`) or host it.
2. On the phone, open the URL in Chrome.
3. Tap the browser menu → **Add to Home screen** (installs AirQR like an app).
4. Launch from home screen; grant camera permission.
5. For a PC sender compatible with the web receiver, run: `airqr send ./folder --web` (disables compression/encryption/FEC).

Works offline after first load via service worker. Mobile web uses the browser BarcodeDetector; best on Chrome/Android.

## Mobile (planned)
Android (Kotlin + Compose) and iOS (Swift + SwiftUI) apps are on the roadmap; see PLAN.md.

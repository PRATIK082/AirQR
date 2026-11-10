# Installation Guide

## Desktop (Python v1)

1. Install Python 3.10+.
2. Clone the repo:
   ```
   git clone https://github.com/PRATIK082/AirQR.git
   cd AirQR
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run:
   ```
   airqr send ./my_folder
   airqr receive --dest ./downloads
   ```
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

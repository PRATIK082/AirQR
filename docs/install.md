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

## Web Fallback (PWA)
Open `web/index.html` in a browser or serve the `web/` folder over localhost. Grant camera permission. Works offline after first load via service worker.

## Mobile (planned)
Android (Kotlin + Compose) and iOS (Swift + SwiftUI) apps are on the roadmap; see PLAN.md.

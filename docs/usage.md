# AirQR Usage Guide

## PC ↔ Phone

### A. PC → Phone
1. On PC (sender):
   - Install: `pip install .`
   - Run: `airqr send ./my_folder --display image`
   - (Optional) Encrypt: `airqr send ./secret.zip --encrypt`
2. A large QR code appears on the PC screen.
3. On phone (receiver): install/use the AirQR Web PWA (Chrome → Add to Home screen) or open the web app; tap **Enable Camera**, grant camera permission.
4. Point the phone camera at the PC screen. Keep 30–50 cm distance, avoid glare.
5. Watch live progress (%, speed, ETA, received/missing chunks).
6. On completion, verify SHA-256 hash shown; confirm save to Downloads.
7. For executables/archives, a warning is shown before opening.

For laptop→mobile (no ACK), use broadcast mode - needs 2 terminals on PC:

Terminal 1 - QR loop (this is what phone scans):
```
airqr send ./folder --web --broadcast --chunk-size 800 --frame-interval 1.2 --qr-scale 0.75
```
- `--chunk-size 200-2000` (default 800): smaller = easier to scan but more frames.
- `--frame-interval 0.5-3.0s` (default 1.2): how long each QR stays. Use 2.0 if phone misses frames.
- `--qr-scale 0.3-1.0` (default 0.75): PC window size. Use 0.9 for large QR (scan from far), 0.5 for small laptop screens.
- `--manifest-chunk 800`: usually leave default.

Terminal 2 - serve receiver page to phone (phone does NOT run Python):
```
python framework/run.py
# then on phone browser open: http://192.168.1.3:8765/index.html -> Receive tab -> Enable Camera
# PC and phone must be on same WiFi/hotspot for this step only.
# Transfer itself is offline (camera scans screen, no data over WiFi).
# Tip: open page once -> Add to Home screen -> works offline after that.
```

Phone camera shows "not a secure context" or nothing happens? Chrome blocks
camera on `http://192.168.x.x`. Two fixes:
- Fix A (easiest): on phone Chrome open `chrome://flags/#unsafely-treat-insecure-origin-as-secure`,
  add `http://192.168.1.3:8765`, Enable, Relaunch, reopen page.
- Fix B: on PC run `python framework/run.py --https`, on phone open
  `https://<PC-IP>:8766/index.html`, accept the self-signed cert warning.
- Never open `index.html` as `file://` - camera will always be blocked.
- Also grant camera permission when prompted, use back camera, keep 30-50cm.

### B. Phone → PC
1. On phone (sender): select file/folder, tap **Show QR** (fullscreen).
2. On PC (receiver): `airqr receive --dest ./downloads --display image`
3. Point the PC webcam at the phone screen.
4. Progress and verification as above.

### C. Resume after interruption
- Sender: re-run the same `airqr send ...` (stateless sender re-streams; receiver resumes via `--resume`).
- Receiver: `airqr receive --dest ./downloads --resume` to continue from saved state.

### D. Tips for reliability
- Use high brightness, avoid reflections, keep camera steady.
- Larger files: use `--display ascii` only if no GUI; otherwise image mode auto-sizes.
- If chunks fail, FEC recovers a few missing frames; otherwise selective retransmission runs automatically.
- Point Receiver's camera at Sender's screen (data QRs); Sender's camera at Receiver's screen (ACK QRs) for PC↔PC.

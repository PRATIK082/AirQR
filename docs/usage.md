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

For laptop→mobile (no ACK), use broadcast mode:
```
airqr send ./folder --web --broadcast
```

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

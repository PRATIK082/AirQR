# AirQR Troubleshooting

| Symptom | Likely Fix |
|---------|------------|
| "X Chunk N failed after 3 retries" | Sender camera isn't seeing receiver's ACK QR. Reposition sender camera to point at receiver screen. |
| Receiver keeps printing the same header | Sender's ACK scan is failing. Ensure sender camera sees receiver screen (not its own). |
| QR window behind terminal | Display and camera windows are now always-on-top. If still behind, minimize other windows. |
| QR code too big for screen | QR is now auto-sized. If still too big, try `--display ascii` mode. |
| Camera not found | Change camera ID in `qr_utils.py` `QRScanner.__init__(camera_id=0)` to 1 or 2. |
| "Invalid QR data, skipping" | Camera is seeing garbage or wrong QR codes. Check positioning and lighting. |

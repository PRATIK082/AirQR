#!/usr/bin/env python3
"""Build a single-file offline receiver page for zero-radio phone use.

Reads web/receiver.js + web/jsQR.js and emits web/receive-offline.html
with everything inlined. Transfer that ONE file to the phone over USB
(MTP copy to Download), open it in Chrome as
file:///sdcard/Download/receive-offline.html, grant camera, point at
the PC's `airqr send --web --broadcast` QR loop.

Why: with no WiFi/hotspot/USB-network, no http:// URL can load, and
tapping index.html from a file manager breaks (content:// URI kills
relative <script src> paths). One self-contained file has no relative
paths, so it works from file://. file:// is a secure context, so
getUserMedia/BarcodeDetector are allowed (same as https).

Regenerate after editing web/receiver.js:
    python tools/build_offline_receiver.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB = os.path.join(ROOT, "web")

HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>AirQR Offline Receiver</title>
<style>
body { font-family: system-ui, sans-serif; margin: 0; padding: 1rem; background: #0b0d12; color: #e8ecf2; }
.card { max-width: 760px; margin: auto; padding: 1rem; border-radius: 16px; background: #151922; }
button { padding: 0.7rem 1rem; border-radius: 10px; border: none; background: #4f8cff; color: white; font-size: 1rem; cursor: pointer; margin: 0.3rem; }
#status { margin-top: 1rem; font-family: monospace; white-space: pre-wrap; }
.bar { height: 10px; background: #2a2f3a; border-radius: 6px; overflow: hidden; margin-top: 0.5rem; }
.bar > div { height: 100%; background: #4f8cff; width: 0%%; }
.note { opacity: 0.7; font-size: 0.85rem; margin-top: 1rem; }
video { width: 100%%; margin-top: 1rem; border-radius: 12px; background: #000; }
</style>
</head>
<body>
<div class="card">
<h1>AirQR Offline Receiver</h1>
<p class="note">Fully offline: this file has no network requests. Point the camera at the PC's QR loop. Files save automatically when each completes.</p>
<button id="start">Enable Camera (Receiver)</button>
<button id="stopRecv">Stop</button>
<video id="video" autoplay playsinline muted></video>
<p id="status">Idle</p>
<div class="bar"><div id="recvBar"></div></div>
</div>
<script>
/* === inlined jsQR.js === */
"""


def main():
    with open(os.path.join(WEB, "jsQR.js"), "r", encoding="utf-8") as f:
        jsqr = f.read()
    with open(os.path.join(WEB, "receiver.js"), "r", encoding="utf-8") as f:
        receiver = f.read()
    # receiver.js expects #recvStats/#recvBar optionally; guard missing nodes.
    out = (
        HTML_HEAD
        + jsqr
        + "\n/* === inlined receiver.js === */\n"
        + receiver
        + "\n</script>\n</body>\n</html>\n"
    )
    assert 'src="' not in out.replace("video", "v"), "external script ref leaked"
    dest = os.path.join(WEB, "receive-offline.html")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {dest} ({os.path.getsize(dest)} bytes)")


if __name__ == "__main__":
    main()

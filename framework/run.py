#!/usr/bin/env python3
"""Direct-run launcher for the AirQR web framework (PC + mobile)."""
import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8765
HERE = os.path.dirname(os.path.abspath(__file__))
MOBILE = os.path.join(HERE, "mobile")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=MOBILE, **kw)

if __name__ == "__main__":
    os.chdir(MOBILE)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/index.html"
        print(f"AirQR framework running at {url}")
        print("On mobile, open http://<PC-IP>:%d/index.html" % PORT)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")

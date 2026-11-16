#!/usr/bin/env python3
"""Direct-run launcher for the AirQR web framework (PC + mobile).

HTTP mode (default):
  python framework/run.py
  -> phone opens http://<PC-IP>:8765/index.html

HTTPS mode (needed if Chrome blocks camera on http LAN):
  python framework/run.py --https
  -> phone opens https://<PC-IP>:8766/index.html (accept self-signed cert)

Why: getUserMedia/camera requires a secure context. http://192.168.x.x is
NOT secure by default, so Chrome sets navigator.mediaDevices=undefined.
Fix A: chrome://flags/#unsafely-treat-insecure-origin-as-secure + add
http://<PC-IP>:8765. Fix B: this --https mode.
"""
import http.server
import socketserver
import webbrowser
import os
import sys
import argparse
import ipaddress
import socket

PORT_HTTP = 8765
PORT_HTTPS = 8766
HERE = os.path.dirname(os.path.abspath(__file__))
MOBILE = os.path.join(HERE, "mobile")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=MOBILE, **kw)

    def log_message(self, *a):
        pass


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "<PC-IP>"


def ensure_cert(cert_path, key_path):
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "AirQR")])
        san = [x509.DNSName("localhost")]
        try:
            san.append(x509.IPAddress(ipaddress.ip_address(lan_ip())))
        except Exception:
            pass
        cert = (x509.CertificateBuilder()
                .subject_name(subject).issuer_name(issuer)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(datetime.datetime.utcnow())
                .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
                .add_extension(x509.SubjectAlternativeName(san), critical=False)
                .sign(key, hashes.SHA256()))
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(serialization.Encoding.PEM,
                    serialization.PrivateFormat.TraditionalOpenSSL,
                    serialization.NoEncryption()))
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print(f"Generated self-signed cert: {cert_path}")
    except ModuleNotFoundError:
        print("cryptography package needed for --https: pip install cryptography")
        sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--https", action="store_true", help="Serve via HTTPS (for phone camera)")
    ap.add_argument("--port", type=int, default=None)
    args = ap.parse_args()
    os.chdir(MOBILE)
    ip = lan_ip()
    if args.https:
        import ssl
        port = args.port or PORT_HTTPS
        cert = os.path.join(HERE, "airqr-cert.pem")
        key = os.path.join(HERE, "airqr-key.pem")
        ensure_cert(cert, key)
        with socketserver.TCPServer(("", port), Handler) as httpd:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(cert, key)
            httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
            print(f"AirQR HTTPS at https://{ip}:{port}/index.html")
            print(f"Local: https://localhost:{port}/index.html")
            print("On phone: accept the self-signed cert warning, then Receive -> Enable Camera.")
            try:
                webbrowser.open(f"https://localhost:{port}/index.html")
            except Exception:
                pass
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nStopped.")
    else:
        port = args.port or PORT_HTTP
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"AirQR HTTP at http://{ip}:{port}/index.html")
            print(f"Local: http://localhost:{port}/index.html")
            print("If phone camera says 'not a secure context':")
            print(f"  A) Chrome flag: chrome://flags/#unsafely-treat-insecure-origin-as-secure -> add http://{ip}:{port} -> Relaunch")
            print("  B) Or rerun with: python framework/run.py --https")
            try:
                webbrowser.open(f"http://localhost:{port}/index.html")
            except Exception:
                pass
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nStopped.")

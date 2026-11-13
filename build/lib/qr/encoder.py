"""High-performance QR code generation."""
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H


EC_MAP = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M,
          "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}


def make_qr(text: str, ec: str = "M", box_size: int = 10, border: int = 4):
    qr = qrcode.QRCode(
        version=None,  # auto
        error_correction=EC_MAP.get(ec, ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def qr_capacity(ec: str = "M", version: int = None) -> int:
    # approximate max alphanumeric/byte capacity; use conservative byte capacity
    # For version 40 EC M ~ 2331 bytes. We'll just return a safe default.
    return 1200

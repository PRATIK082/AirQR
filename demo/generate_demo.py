"""Generate demo screenshot and animated GIF for AirQR docs."""
import os
import time
import qrcode
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "demo")
os.makedirs(OUT, exist_ok=True)


def make_qr_img(text, size=400):
    qr = qrcode.QRCode(version=None, box_size=10, border=4,
                        error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((size, size), Image.NEAREST)
    return img


def sender_frame(progress, chunk_text):
    W, H = 900, 600
    canvas = Image.new("RGB", (W, H), (11, 13, 18))
    d = ImageDraw.Draw(canvas)
    # title
    d.text((40, 30), "AirQR Sender — Presenting", fill=(232, 236, 242))
    # QR
    qr = make_qr_img(chunk_text, 420)
    canvas.paste(qr, (40, 90))
    # progress panel
    x0, y0 = 480, 120
    d.text((x0, y0), "Transferring: archive.zip", fill=(232, 236, 242))
    d.text((x0, y0 + 40), f"Progress: {progress}%", fill=(150, 160, 180))
    # progress bar
    bar_w = 360
    d.rectangle([x0, y0 + 90, x0 + bar_w, y0 + 110], fill=(40, 44, 55))
    d.rectangle([x0, y0 + 90, x0 + int(bar_w * progress / 100), y0 + 110], fill=(79, 140, 255))
    d.text((x0, y0 + 130), "Speed: 12.4 KB/s   ETA: 00:12", fill=(150, 160, 180))
    d.text((x0, y0 + 170), "Chunks: 42/100   Retries: 0", fill=(150, 160, 180))
    d.text((x0, y0 + 230), "State: Transferring", fill=(120, 200, 120))
    d.text((40, 540), "Press q in camera window to cancel", fill=(100, 100, 110))
    return canvas


def receiver_frame(progress, missing):
    W, H = 900, 600
    canvas = Image.new("RGB", (W, H), (11, 13, 18))
    d = ImageDraw.Draw(canvas)
    d.text((40, 30), "AirQR Receiver — Scanning", fill=(232, 236, 242))
    # fake camera preview
    d.rectangle([40, 90, 520, 510], fill=(20, 22, 28), outline=(60, 64, 75))
    d.text((180, 290), "Camera preview", fill=(100, 100, 110))
    # progress ring text
    d.text((560, 120), f"Received: {progress}%", fill=(232, 236, 242))
    d.text((560, 170), f"Missing chunks: {missing}", fill=(200, 120, 120))
    d.text((560, 220), "Speed: 11.9 KB/s   ETA: 00:14", fill=(150, 160, 180))
    d.text((560, 270), "State: Scanning", fill=(120, 200, 120))
    d.text((560, 340), "Saving to: Downloads/", fill=(150, 160, 180))
    return canvas


# Static screenshots
sender_frame(42, "AIRQR-CHUNK-0042-PAYLOAD-DEMO").save(os.path.join(OUT, "sender.png"))
receiver_frame(42, 3).save(os.path.join(OUT, "receiver.png"))
print("screenshots written")

# Animated GIF: sender progress 0..100
frames = []
for i in range(0, 101, 5):
    chunk = f"AIRQR-CHUNK-{i:04d}-PAYLOAD"
    frames.append(sender_frame(i, chunk))
# append receiver frames
for i in range(0, 101, 10):
    frames.append(receiver_frame(i, max(0, 5 - i // 20)))
gif_path = os.path.join(OUT, "demo.gif")
frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=120, loop=0)
print("gif written:", gif_path)

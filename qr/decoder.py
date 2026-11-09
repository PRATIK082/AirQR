"""QR code decoding from camera frames using OpenCV."""
import cv2
import time


class QRScanner:
    def __init__(self, camera_id: int = 0):
        self.cap = cv2.VideoCapture(camera_id)
        self.detector = cv2.QRCodeDetector()

    def read_frame(self):
        ok, frame = self.cap.read()
        if not ok:
            return None
        return frame

    def scan_once(self, timeout: float = 2.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            frame = self.read_frame()
            if frame is None:
                continue
            data, pts, _ = self.detector.detectAndDecode(frame)
            if data:
                return data
        return None

    def release(self):
        try:
            self.cap.release()
        except Exception:
            pass

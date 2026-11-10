"""Adaptive QR parameters based on file type, size, and scan success."""
import os

# conservative byte capacity per QR (version auto, EC M)
BASE_CAPACITY = 1200


def choose_chunk_size(file_size: int, mime: str) -> int:
    # smaller chunks for reliability; larger for speed on big files
    if file_size > 50 * 1024 * 1024:
        return 900
    if file_size > 10 * 1024 * 1024:
        return 1000
    return 800


def choose_ec(scan_success_rate: float = 1.0) -> str:
    if scan_success_rate < 0.7:
        return "H"
    if scan_success_rate < 0.9:
        return "Q"
    return "M"


def choose_frame_interval(scan_success_rate: float = 1.0) -> float:
    # seconds per frame
    if scan_success_rate < 0.7:
        return 1.2
    return 0.6

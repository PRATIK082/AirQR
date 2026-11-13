#! python3.11
"""AirQR CLI entry point."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sender import main as sender_main
from receiver import main as receiver_main


def main():
    # Support both: `python main.py send ...` and `python main.py sender ...`
    args = sys.argv[1:]
    if len(args) >= 1 and args[0] in ("sender",):
        args = ["send"] + args[1:]
    if len(args) >= 1 and args[0] in ("receiver",):
        args = ["receive"] + args[1:]
    sys.argv = [sys.argv[0]] + args
    if len(args) >= 1 and args[0] == "send":
        sender_main()
    elif len(args) >= 1 and args[0] == "receive":
        receiver_main()
    else:
        # delegate to sender parser for help
        sender_main()


if __name__ == "__main__":
    main()

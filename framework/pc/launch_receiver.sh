#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../.."
read -rp "Destination folder (default ./received): " DEST
DEST="${DEST:-./received}"
python3 airqr receive --dest "$DEST"

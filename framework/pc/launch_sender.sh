#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../.."
read -rp "Source file or folder path: " SRC
python3 airqr send "$SRC"

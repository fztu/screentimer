#!/usr/bin/env bash
set -euo pipefail
pyinstaller --onefile --windowed --name screentimer screentimer/main.py
echo "Build complete: dist/screentimer"

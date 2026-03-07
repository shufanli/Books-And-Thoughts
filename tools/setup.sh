#!/bin/bash
# One-time setup: installs Python deps and optionally Calibre.

set -e

echo "=== Installing Python dependencies ==="
pip3 install -r "$(dirname "$0")/requirements.txt"

echo ""
read -p "Install Calibre (needed for MOBI/AZW3)? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
    brew install --cask calibre
    echo "Calibre installed. Reopen your terminal before converting MOBI/AZW3."
fi

echo ""
echo "Setup complete. Usage:"
echo "  python3 tools/convert.py book.pdf"
echo "  python3 tools/convert.py ./my-books/ -o ./converted"

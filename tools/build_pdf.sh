#!/bin/sh
# Re-lays out index.html with tools/page.py (which stamps "Last updated" with the current UTC time),
# then prints it to geert-greydanus-timeline.pdf with headless Chrome, so the page and PDF carry the
# same stamp. Run from anywhere after any change to the page:
#
#   tools/build_pdf.sh
#
# Set CHROME to a Chrome or Chromium binary if it is not in the default macOS location.
set -eu
cd "$(dirname "$0")/.."
python3 tools/page.py index.html index.html
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
  --virtual-time-budget=5000 \
  --print-to-pdf="$PWD/geert-greydanus-timeline.pdf" \
  "file://$PWD/index.html" 2>/dev/null
echo "wrote geert-greydanus-timeline.pdf"

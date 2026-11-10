#!/bin/sh
# Prints index.html to geert-greydanus-timeline.pdf with headless Chrome, so the PDF always matches
# the page. Run from anywhere after any change to index.html:
#
#   tools/build_pdf.sh
#
# Set CHROME to a Chrome or Chromium binary if it is not in the default macOS location.
set -eu
cd "$(dirname "$0")/.."
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
  --virtual-time-budget=5000 \
  --print-to-pdf="$PWD/geert-greydanus-timeline.pdf" \
  "file://$PWD/index.html" 2>/dev/null
echo "wrote geert-greydanus-timeline.pdf"

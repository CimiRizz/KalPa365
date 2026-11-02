#!/usr/bin/env bash
set -euo pipefail
# Install browser alongside Playwright so it is included in Render deploy artifact.
export PLAYWRIGHT_BROWSERS_PATH=0
python -m pip install -r requirements.txt
python -m playwright install chromium
python - <<'PYCHECK'
import os
from playwright.sync_api import sync_playwright
assert os.environ.get('PLAYWRIGHT_BROWSERS_PATH') == '0'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    print('Chromium bundled OK:', browser.version)
    browser.close()
PYCHECK

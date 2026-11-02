#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
python -m playwright install chromium
python - <<'PYCHECK'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    print('Chromium OK:', browser.version)
    browser.close()
PYCHECK

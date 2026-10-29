#!/usr/bin/env python3
"""KalPa365 v1.0 — news aggregation using public Google News RSS search."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse, quote
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
import json, os, re, time, threading, pathlib, html

ROOT = pathlib.Path(__file__).resolve().parent
PORT = int(os.environ.get('PORT', '8766'))
TTL = 300
LOCK = threading.Lock()
CACHE = {'at': 0, 'data': None}
# Google News returns articles from many publishers. Separate searches help
# smaller publishers surface alongside national news outlets.
SEARCHES = [
    '"KalPa" jääkiekko',
    '"KalPa" Kuopio',
    '"KalPa" site:kalpa.fi',
    '"KalPa" site:savonsanomat.fi',
]
POSITIVE = re.compile(r'(?<![\w])kalpa(?:n|lle|lta|ssa|sta|an|a)?(?![\w])|kuopion\s+kalpa', re.I)
NEGATIVE = re.compile(r'kalpa(?:na|lla)?\s+(?:ruoka|esine|kukka)|kalpa\s+miekk', re.I)

def text(node, tag):
    el = node.find(tag)
    return ''.join(el.itertext()).strip() if el is not None else ''

def strip_markup(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value or ''))).strip()

def feed_url(query):
    return 'https://news.google.com/rss/search?' + urlencode({'q': query, 'hl':'fi', 'gl':'FI', 'ceid':'FI:fi'})

def fetch(query):
    req = Request(feed_url(query), headers={'User-Agent':'Mozilla/5.0 (compatible; KalPa365/1.0; news aggregator)', 'Accept':'application/rss+xml, application/xml'})
    with urlopen(req, timeout=15) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError('RSS response too large')
    root = ET.fromstring(data)
    results = []
    for item in root.findall('./channel/item'):
        title = strip_markup(text(item, 'title'))
        url = text(item, 'link')
        summary = strip_markup(text(item, 'description'))
        source = text(item, 'source') or 'Muu lähde'
        if not url.startswith('https://news.google.com/'):
            continue
        if not POSITIVE.search(title + ' ' + summary) or NEGATIVE.search(title):
            continue
        published = text(item, 'pubDate')
        try:
            stamp = parsedate_to_datetime(published).timestamp()
        except (ValueError, TypeError, OverflowError):
            stamp = 0
        # Google News may append " - Publisher" to a title.
        if source and title.endswith(' - ' + source):
            title = title[:-(len(source) + 3)]
        results.append({'title': title, 'source': source, 'url': url,
                        'summary': summary[:240], 'timestamp': stamp,
                        'published': published})
    return results

def news():
    with LOCK:
        if CACHE['data'] is not None and time.time() - CACHE['at'] < TTL:
            return CACHE['data']
        items, errors = [], []
        for query in SEARCHES:
            try:
                items.extend(fetch(query))
            except Exception as exc:
                errors.append(f'{query}: {type(exc).__name__}')
        seen, unique = set(), []
        for item in sorted(items, key=lambda x: x['timestamp'], reverse=True):
            # Deduplicate by normalized headline + publisher, not opaque Google URL.
            key = (re.sub(r'\W+', '', item['title'].casefold()), item['source'].casefold())
            if key not in seen:
                seen.add(key)
                unique.append(item)
        data = {'articles': unique[:150], 'updated': datetime.now(timezone.utc).isoformat(),
                'errors': errors, 'status': 'ok' if unique else ('error' if errors else 'empty')}
        # Don't cache total network failure for 5 minutes.
        CACHE.update(at=time.time(), data=data) if unique or not errors else None
        return data

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ('/', '/index.html'):
            payload = (ROOT / 'index.html').read_bytes()
            mime = 'text/html; charset=utf-8'
        elif path == '/api/news':
            payload = json.dumps(news(), ensure_ascii=False).encode('utf-8')
            mime = 'application/json; charset=utf-8'
        elif path == '/health':
            payload = b'ok'; mime = 'text/plain; charset=utf-8'
        else:
            self.send_error(404); return
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

if __name__ == '__main__':
    print(f'KalPa365: http://localhost:{PORT}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()

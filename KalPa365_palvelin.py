#!/usr/bin/env python3
"""KalPa365 v1.0 — news aggregation using public Google News RSS search."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse, quote, parse_qs, unquote
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
import json, os, re, time, threading, pathlib, html
from html.parser import HTMLParser

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

# Reader: attempt to resolve a Google News link to the original publisher.
# Some Google News links cannot be resolved without unsupported private APIs.
# Only follow HTTPS links from RSS items; no paywall or login bypass.
ALLOWED_PUBLISHERS = (
    'is.fi', 'iltalehti.fi', 'yle.fi', 'kalpa.fi', 'savonsanomat.fi',
    'liiga.fi', 'jatkoaika.com', 'suomikiekko.com', 'mtvuutiset.fi',
    'kaleva.fi', 'kiekkoareena.fi', 'leijonat.fi', 'keskisuomalainen.fi',
    'sportti.com', 'ess.fi', 'ilkkapohjalainen.fi', 'aamulehti.fi',
)
def allowed_publisher(url):
    p=urlparse(url)
    return p.scheme=='https' and p.hostname is not None and any(
        p.hostname==d or p.hostname.endswith('.'+d) for d in ALLOWED_PUBLISHERS)

class ReaderParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]; self.paragraphs=[]; self.parts=None; self.depth=0
        self.article_depth=0; self.in_article=False
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs); parent=self.stack[-1] if self.stack else (False,False)
        excluded=parent[0] or tag in ('script','style','nav','footer','aside','form','noscript','svg','iframe','button')
        marker=' '.join(str(attrs.get(k,'')) for k in ('class','id','role'))
        article=parent[1] or tag=='article' or bool(re.search(r'article[-_ ]?(body|content|text)|story[-_ ]?body',marker,re.I))
        if tag=='p' and article and not excluded and self.parts is None:
            self.parts=[]; self.depth=len(self.stack)
        if tag not in ('meta','link','img','br','hr','input','source','wbr'):
            self.stack.append((excluded,article))
    def handle_data(self,data):
        if self.parts is not None and self.stack and not self.stack[-1][0]: self.parts.append(data)
    def handle_endtag(self,tag):
        if tag=='p' and self.parts is not None:
            value=' '.join(''.join(self.parts).split())
            if len(value)>55 and not re.match(r'^(?:Lue myös|Katso myös|Kuva:|Mainos|Suosittelemme)',value,re.I):
                self.paragraphs.append(value)
            self.parts=None
        if self.stack:self.stack.pop()

def resolve_publisher(google_url):
    p=urlparse(google_url)
    if p.scheme!='https' or p.hostname!='news.google.com': raise ValueError('Invalid news URL')
    # First try ordinary HTTP redirects. Google may serve an interstitial instead.
    req=Request(google_url,headers={'User-Agent':'Mozilla/5.0 KalPa365/1.2'})
    with urlopen(req,timeout=10) as response:
        final=response.geturl()
        if allowed_publisher(final): return final
        if urlparse(final).hostname!='news.google.com': return None
        raw=response.read(300_000).decode('utf-8','replace')
    # Google sometimes exposes the publisher's URL in a regular HTML link.
    for match in re.finditer(r'https?[^\s"<>]+',html.unescape(raw)):
        candidate=match.group(0).rstrip('\\').rstrip('.,;')
        if allowed_publisher(candidate): return candidate
    return None

def article_for(google_url):
    if google_url not in {a['url'] for a in news()['articles']}:
        raise ValueError('Article not found in current feed')
    original=resolve_publisher(google_url)
    if not original: return {'status':'summary','paragraphs':[], 'message':'Google News ei antanut alkuperäisen artikkelin osoitetta.'}
    req=Request(original,headers={'User-Agent':'Mozilla/5.0 (compatible; KalPa365Reader/1.2)','Accept':'text/html'})
    with urlopen(req,timeout=12) as response:
        if not allowed_publisher(response.geturl()): raise ValueError('Unexpected redirect')
        if 'html' not in response.headers.get('Content-Type','text/html'): raise ValueError('Not HTML')
        raw=response.read(1_500_001)
        if len(raw)>1_500_000: raise ValueError('Article too large')
        decoded=raw.decode(response.headers.get_content_charset() or 'utf-8','replace')
    parser=ReaderParser();parser.feed(decoded)
    unique=list(dict.fromkeys(parser.paragraphs))
    if len(unique)<3 or sum(map(len,unique))<400:
        return {'status':'summary','paragraphs':[], 'original_url':original,'message':'Kokotekstiä ei ollut saatavilla luotettavasti.'}
    return {'status':'full','paragraphs':unique[:100], 'original_url':original}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ('/', '/index.html'):
            payload = (ROOT / 'index.html').read_bytes()
            mime = 'text/html; charset=utf-8'
        elif path == '/api/news':
            payload = json.dumps(news(), ensure_ascii=False).encode('utf-8')
            mime = 'application/json; charset=utf-8'
        elif path == '/api/article':
            params=parse_qs(urlparse(self.path).query)
            try:
                result=article_for(params.get('url',[''])[0])
            except Exception:
                result={'status':'summary','paragraphs':[], 'message':'Artikkelin hakeminen ei onnistunut.'}
            payload=json.dumps(result,ensure_ascii=False).encode('utf-8')
            mime='application/json; charset=utf-8'
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

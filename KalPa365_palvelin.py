#!/usr/bin/env python3
"""KalPa365 v2.0 — direct source discovery and reader."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse, quote, parse_qs, unquote, urljoin
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
import json, os, re, time, threading, pathlib, html, sqlite3
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
PORT = int(os.environ.get('PORT', '8766'))
TTL = 300
DB_PATH = pathlib.Path(os.environ.get('KALPA365_DB', str(ROOT / 'kalpa365_history.sqlite3')))
HISTORY_DAYS = 30
LOCK = threading.Lock()
CACHE = {'at': 0, 'data': None}
FEEDS = {
    'IS': [
        'https://www.is.fi/rss/tuoreimmat.xml',
    ],
    'IL': [
        'https://www.iltalehti.fi/rss.xml',
        'https://www.iltalehti.fi/rss/uutiset.xml',
    ],
    'Jatkoaika': ['https://www.jatkoaika.com/rss.xml'],
    'Savon Sanomat': ['https://www.savonsanomat.fi/feed/rss'],
    'Yle.fi': [
        'https://yle.fi/rss/urheilu',
        'https://yle.fi/rss/tuoreimmat',
    ],
}

# Jatkoajan ja Savon Sanomien syöteosoitteet ovat kokeellisia.
# Lähteen mahdollinen virhe näkyy /api/news-vastauksen sources-kentässä.
POSITIVE = re.compile(r'(?<!\w)kalpa(?:n|lle|lta|ssa|sta|an|a)?(?!\w)|kuopion\s+kalpa', re.I)
NEGATIVE = re.compile(r'kalpa(?:na|lla)?\s+(?:ruoka|esine|kukka)|kalpa\s+miekk', re.I)

ALLOWED_PUBLISHERS = (
    'is.fi',
    'iltalehti.fi',
    'jatkoaika.com',
    'savonsanomat.fi',
    'liiga.fi',
    'yle.fi',
)

def allowed_publisher(url):
    p=urlparse(url)
    return p.scheme=='https' and p.hostname is not None and any(
        p.hostname==d or p.hostname.endswith('.'+d) for d in ALLOWED_PUBLISHERS)

def local(tag): return tag.rsplit('}',1)[-1].lower()
def child_text(node, names):
    for c in node:
        if local(c.tag) in names and c.text and c.text.strip(): return c.text.strip()
    return ''
def strip_markup(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value or ''))).strip()

def history_connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.execute('CREATE TABLE IF NOT EXISTS articles (url TEXT PRIMARY KEY, payload TEXT NOT NULL, timestamp REAL NOT NULL, seen REAL NOT NULL)')
    return conn

def history_merge(fresh):
    # Render Free instance filesystem is ephemeral. History survives normal requests,
    # but can be lost on restart/redeploy unless a persistent DB is configured.
    try:
        with history_connect() as db:
            now = time.time()
            for a in fresh:
                db.execute('INSERT INTO articles(url,payload,timestamp,seen) VALUES(?,?,?,?) ON CONFLICT(url) DO UPDATE SET payload=excluded.payload, timestamp=excluded.timestamp, seen=excluded.seen', (a['url'], json.dumps(a, ensure_ascii=False), a['timestamp'], now))
            db.execute('DELETE FROM articles WHERE seen < ?', (now - HISTORY_DAYS * 86400,))
            rows = db.execute('SELECT payload FROM articles ORDER BY timestamp DESC LIMIT 500').fetchall()
        return [json.loads(row[0]) for row in rows], 'ok'
    except (OSError, sqlite3.Error) as exc:
        return fresh, f'unavailable: {type(exc).__name__}'

def parse_feed(source, raw):
    root = ET.fromstring(raw)
    results, scanned, publisher_links = [], 0, 0
    for item in root.iter():
        if local(item.tag) not in ('item', 'entry'):
            continue
        scanned += 1
        title = strip_markup(child_text(item, {'title'}))
        link = child_text(item, {'link'})
        if not link:
            for child in item:
                if local(child.tag) == 'link' and child.attrib.get('href'):
                    if child.attrib.get('rel', 'alternate') == 'alternate':
                        link = child.attrib['href'].strip()
                        break
        summary = strip_markup(child_text(item, {'description', 'summary', 'encoded', 'content'}))
        if not title or not allowed_publisher(link):
            continue
        publisher_links += 1
        if not POSITIVE.search(title + ' ' + summary) or NEGATIVE.search(title):
            continue
        pub = child_text(item, {'pubdate', 'published', 'updated', 'date'})
        try:
            stamp = parsedate_to_datetime(pub).timestamp()
        except Exception:
            try:
                stamp = datetime.fromisoformat(pub.replace('Z', '+00:00')).timestamp()
            except Exception:
                stamp = 0
        results.append({
            'title': title, 'source': source, 'url': link,
            'summary': summary[:500], 'timestamp': stamp, 'published': pub
        })
    return results, scanned, publisher_links


def fetch(source, urls):
    # Read *all* available feeds. A valid but empty feed must not mask
    # later feeds, and one broken feed must not suppress successful feeds.
    collected, seen = [], set()
    diagnostics = []
    total_scanned = total_links = 0
    success = 0
    for url in urls:
        try:
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; KalPa365/1.9)',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*'
            })
            with urlopen(req, timeout=12) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ValueError('Feed too large')
            items, scanned, links = parse_feed(source, raw)
            success += 1
            total_scanned += scanned
            total_links += links
            for item in items:
                key = item['url'].split('?')[0].rstrip('/')
                if key not in seen:
                    seen.add(key)
                    collected.append(item)
            diagnostics.append({
                'feed': url, 'status': 'ok', 'scanned': scanned,
                'publisher_links': links, 'count': len(items)
            })
        except Exception as exc:
            diagnostics.append({
                'feed': url, 'status': 'error',
                'message': f'{type(exc).__name__}: {str(exc)[:140]}'
            })
    info = {
        'status': 'ok' if success else 'error',
        'count': len(collected),
        'scanned': total_scanned,
        'publisher_links': total_links,
        'feeds': diagnostics,
    }
    # Keep the old single-feed field for compatibility with the UI.
    info['feed'] = next((d['feed'] for d in diagnostics if d['status'] == 'ok'), urls[0] if urls else '')
    if not success:
        info['message'] = ' | '.join(d['message'] for d in diagnostics if d['status'] == 'error')
    elif any(d['status'] == 'error' for d in diagnostics):
        info['warning'] = 'Some feeds failed; see feeds'
    return collected, info


# Liiga.fi does not advertise a verified RSS feed. Extract only public news links
# present in the server response; never invent articles or bypass access controls.
LIIGA_NEWS = 'https://liiga.fi/fi/uutiset?kategoria=uusimmat'

class LiigaLinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links=[]; self.current=None
    def handle_starttag(self, tag, attrs):
        if tag != 'a': return
        attrs=dict(attrs); href=attrs.get('href','')
        target=urljoin('https://liiga.fi',href)
        if urlparse(target).hostname in ('liiga.fi','www.liiga.fi') and re.match(r'^/fi/uutiset/[^/?#]+',urlparse(target).path):
            self.current={'url':target.split('?')[0], 'parts':[]}
    def handle_data(self, data):
        if self.current is not None: self.current['parts'].append(data)
    def handle_endtag(self, tag):
        if tag=='a' and self.current is not None:
            title=strip_markup(' '.join(self.current['parts']))
            if title: self.links.append((title,self.current['url']))
            self.current=None

def fetch_liiga():
    try:
        req=Request(LIIGA_NEWS,headers={'User-Agent':'KalPa365/1.5 (+public news index)', 'Accept':'text/html'})
        with urlopen(req,timeout=12) as response:
            if not allowed_publisher(response.geturl()): raise ValueError('Unexpected redirect')
            raw=response.read(2_000_001)
            if len(raw)>2_000_000: raise ValueError('Page too large')
            decoded=raw.decode(response.headers.get_content_charset() or 'utf-8','replace')
        parser=LiigaLinkParser(); parser.feed(decoded)
        # Some SPA pages embed news records as JSON rather than visible anchors.
        for match in re.finditer(r'(?P<url>/fi/uutiset/[a-zA-Z0-9_\-%]+)', decoded):
            url=urljoin('https://liiga.fi',html.unescape(match.group('url')))
            around=decoded[max(0,match.start()-450):min(len(decoded),match.end()+450)]
            titles=re.findall(r'"(?:title|headline|name)"\s*:\s*"([^"\\]{8,220})"',around)
            for title in titles:
                parser.links.append((strip_markup(title),url))
        results=[]; seen=set()
        for title,url in parser.links:
            if url in seen: continue
            seen.add(url)
            if not POSITIVE.search(title) or NEGATIVE.search(title): continue
            results.append({'title':title,'source':'Liiga.fi','url':url,'summary':'',
                            'timestamp':time.time(),'published':''})
        return results, {'status':'ok' if parser.links else 'empty', 'count':len(results),
                         'scanned':len(seen),'publisher_links':len(seen),'feed':LIIGA_NEWS,
                         'note':'Liiga.fi news links found in public page HTML; JavaScript-only articles may not appear.'}
    except Exception as exc:
        return [], {'status':'error','count':0,'scanned':0,'message':f'{type(exc).__name__}: {str(exc)[:140]}'}

# Direct publisher category/team pages. Only public links present in HTML are used.
# A 403 response is recorded and never bypassed.
DIRECT_PAGES = {
    'Jatkoaika': ['https://www.jatkoaika.com/Joukkue/KalPa'],
    'Liiga.fi': ['https://liiga.fi/fi/uutiset?kategoria=uusimmat'],
}

class DirectLinkParser(HTMLParser):
    def __init__(self, source, base):
        super().__init__(convert_charrefs=True)
        self.source, self.base = source, base
        self.active = None
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag != 'a': return
        href = dict(attrs).get('href', '')
        link = urljoin(self.base, href)
        path = urlparse(link).path
        valid_path = (path.startswith('/Uutiset/') or path.startswith('/LIIGA/')) if self.source == 'Jatkoaika' else path.startswith('/fi/uutiset/')
        if valid_path and allowed_publisher(link):
            self.active = [link.split('#')[0], []]
    def handle_data(self, data):
        if self.active is not None: self.active[1].append(data)
    def handle_endtag(self, tag):
        if tag == 'a' and self.active is not None:
            title = strip_markup(' '.join(self.active[1]))
            if title: self.links.append((title, self.active[0]))
            self.active = None

def fetch_direct(source, pages):
    all_items, seen, diagnostics = [], set(), []
    for page in pages:
        try:
            req = Request(page, headers={'User-Agent': 'Mozilla/5.0 (compatible; KalPa365/2.0)', 'Accept': 'text/html'})
            with urlopen(req, timeout=12) as response:
                if not allowed_publisher(response.geturl()): raise ValueError('Unexpected redirect')
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000: raise ValueError('Page too large')
                decoded = raw.decode(response.headers.get_content_charset() or 'utf-8', 'replace')
            parser = DirectLinkParser(source, page)
            parser.feed(decoded)
            for title, link in parser.links:
                if link in seen or not POSITIVE.search(title) or NEGATIVE.search(title): continue
                seen.add(link)
                all_items.append({'title': title, 'source': source, 'url': link,
                                  'summary': '', 'timestamp': 0, 'published': ''})
            diagnostics.append({'page': page, 'status': 'ok', 'scanned': len(parser.links)})
        except Exception as exc:
            diagnostics.append({'page': page, 'status': 'error', 'message': f'{type(exc).__name__}: {str(exc)[:120]}'})
    return all_items, {'status': 'ok' if any(d['status']=='ok' for d in diagnostics) else 'error',
                       'count': len(all_items), 'scanned': sum(d.get('scanned', 0) for d in diagnostics),
                       'publisher_links': sum(d.get('scanned', 0) for d in diagnostics),
                       'pages': diagnostics, 'feed': pages[0]}

def news():
    with LOCK:
        if CACHE['data'] is not None and time.time()-CACHE['at']<TTL: return CACHE['data']
        items=[]; sources={}
        for source,urls in FEEDS.items():
            result,info=fetch(source,urls); items.extend(result); sources[source]=info
        for source, pages in DIRECT_PAGES.items():
            found, info = fetch_direct(source, pages)
            items.extend(found)
            sources[source] = info
        seen=set(); unique=[]
        for item in sorted(items,key=lambda x:x['timestamp'],reverse=True):
            key=item['url'].split('?')[0].rstrip('/')
            if key not in seen: seen.add(key); unique.append(item)
        historical,history_status=history_merge(unique)
        data={'articles':historical[:150],'sources':sources,'history_status':history_status,'updated':datetime.now(timezone.utc).isoformat(),
              'errors':[name for name,info in sources.items() if info['status']=='error'],
              'status':'ok' if historical else ('error' if all(v['status']=='error' for v in sources.values()) else 'empty')}
        CACHE.update(at=time.time(),data=data)
        return data

class ReaderParser(HTMLParser):
    """Collect public article paragraphs and JSON-LD NewsArticle content."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]; self.paragraphs=[]; self.current=None
        self.json_scripts=[]; self.script_parts=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        parent=self.stack[-1] if self.stack else (False,False)
        marker=' '.join(str(attrs.get(k,'')) for k in ('class','id','role','data-testid'))
        excluded=parent[0] or tag in ('script','style','nav','footer','aside','form','noscript','svg','iframe','button','header') or bool(re.search(r'related|recommend|advert|promo|share|caption|cookie|paywall',marker,re.I))
        article=parent[1] or tag=='article' or bool(re.search(r'article|story[-_ ]?body|article[-_ ]?(body|content|text)',marker,re.I))
        if tag=='script' and attrs.get('type','').lower()=='application/ld+json': self.script_parts=[]
        if tag in ('p','h2','h3','blockquote') and article and not excluded and self.current is None:
            self.current={'tag':tag,'parts':[]}
        if tag not in ('meta','link','img','br','hr','input','source','wbr','area','embed'):
            self.stack.append((excluded,article,tag))
    def handle_startendtag(self,tag,attrs): pass
    def handle_data(self,data):
        if self.script_parts is not None: self.script_parts.append(data)
        if self.current is not None and self.stack and not self.stack[-1][0]: self.current['parts'].append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.script_parts is not None:
            self.json_scripts.append(''.join(self.script_parts)); self.script_parts=None
        if self.current is not None and tag==self.current['tag']:
            value=' '.join(''.join(self.current['parts']).split())
            if len(value)>35 and not re.match(r'^(?:Lue myös|Katso myös|Kuva:|Mainos|Suosittelemme|Jaa artikkeli)',value,re.I):
                self.paragraphs.append(value)
            self.current=None
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][2]==tag:
                del self.stack[i:]; break

def jsonld_paragraphs(scripts):
    bodies=[]
    def visit(obj):
        if isinstance(obj,list):
            for v in obj: visit(v)
        elif isinstance(obj,dict):
            types=obj.get('@type',[])
            if isinstance(types,str): types=[types]
            if any(str(t).lower() in ('newsarticle','article','reportagenewsarticle') for t in types):
                body=obj.get('articleBody')
                if isinstance(body,str) and body.strip(): bodies.append(body)
            for k in ('@graph','mainEntity'):
                if k in obj: visit(obj[k])
    for script in scripts:
        try: visit(json.loads(script))
        except (ValueError,TypeError): pass
    if not bodies: return []
    body=max(bodies,key=len)
    return [x.strip() for x in re.split(r'\n\s*\n',html.unescape(body)) if len(x.strip())>35]

def article_for(original):
    if original not in {a['url'] for a in news()['articles']}:
        raise ValueError('Article not in current feed')
    if not allowed_publisher(original): raise ValueError('Publisher not allowed')
    req=Request(original,headers={'User-Agent':'Mozilla/5.0 (compatible; KalPa365Reader/1.8)','Accept':'text/html'})
    with urlopen(req,timeout=12) as response:
        if not allowed_publisher(response.geturl()): raise ValueError('Unexpected redirect')
        if 'html' not in response.headers.get('Content-Type','text/html'): raise ValueError('Not HTML')
        raw=response.read(1_500_001)
        if len(raw)>1_500_000: raise ValueError('Article too large')
        decoded=raw.decode(response.headers.get_content_charset() or 'utf-8','replace')
    parser=ReaderParser(); parser.feed(decoded)
    visible=list(dict.fromkeys(parser.paragraphs))
    structured=list(dict.fromkeys(jsonld_paragraphs(parser.json_scripts)))
    paragraphs=max((visible,structured),key=lambda ps:sum(map(len,ps)))
    if sum(map(len,paragraphs))<250:
        return {'status':'summary','paragraphs':[],'original_url':original,
                'message':'Kokotekstiä ei löytynyt julkisesta sivusta.',
                'debug':{'html_paragraphs':len(visible),'jsonld_paragraphs':len(structured)}}
    return {'status':'full','paragraphs':paragraphs[:100],'original_url':original,
            'extraction':'html' if paragraphs is visible else 'jsonld'}

class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        if urlparse(self.path).path in ('/', '/health'):
            self.send_response(200); self.send_header('Content-Length','0'); self.end_headers()
        else: self.send_error(404)
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

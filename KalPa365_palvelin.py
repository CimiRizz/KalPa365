#!/usr/bin/env python3
"""KalPa365 v1.3 — direct RSS sources only, no Google News."""
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
FEEDS = {
    'IS': ['https://www.is.fi/rss/tuoreimmat.xml'],
    'IL': ['https://www.iltalehti.fi/rss/tuoreimmat.xml'],
    'Jatkoaika': ['https://www.jatkoaika.com/rss.xml'],
    'Savon Sanomat': ['https://www.savonsanomat.fi/feed/rss'],
}
# Jatkoajan ja Savon Sanomien syöteosoitteet ovat kokeellisia.
# Lähteen mahdollinen virhe näkyy /api/news-vastauksen sources-kentässä.
POSITIVE = re.compile(r'(?<!\w)kalpa(?:n|lle|lta|ssa|sta|an|a)?(?!\w)|kuopion\s+kalpa', re.I)
NEGATIVE = re.compile(r'kalpa(?:na|lla)?\s+(?:ruoka|esine|kukka)|kalpa\s+miekk', re.I)
ALLOWED_PUBLISHERS = ('is.fi','iltalehti.fi','jatkoaika.com','savonsanomat.fi')

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

def fetch(source, urls):
    failures=[]
    for url in urls:
        try:
            req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; KalPa365/1.3)','Accept':'application/rss+xml, application/xml, text/xml, */*'})
            with urlopen(req,timeout=12) as response:
                raw=response.read(2_000_001)
                if len(raw)>2_000_000: raise ValueError('Feed too large')
            root=ET.fromstring(raw)
            results=[]
            for item in root.iter():
                if local(item.tag) not in ('item','entry'): continue
                title=strip_markup(child_text(item,{'title'}))
                link=child_text(item,{'link'})
                if not link:
                    link=next((c.attrib['href'] for c in item if local(c.tag)=='link' and c.attrib.get('href')), '')
                summary=strip_markup(child_text(item,{'description','summary','encoded','content'}))
                if not title or not allowed_publisher(link): continue
                if not POSITIVE.search(title+' '+summary) or NEGATIVE.search(title): continue
                pub=child_text(item,{'pubdate','published','updated','date'})
                try: stamp=parsedate_to_datetime(pub).timestamp()
                except Exception:
                    try: stamp=datetime.fromisoformat(pub.replace('Z','+00:00')).timestamp()
                    except Exception: stamp=0
                results.append({'title':title,'source':source,'url':link,'summary':summary[:500], 'timestamp':stamp,'published':pub})
            return results, {'status':'ok','count':len(results),'feed':url}
        except Exception as exc:
            failures.append(f'{type(exc).__name__}: {str(exc)[:100]}')
    return [],{'status':'error','count':0,'message':' | '.join(failures)}

def news():
    with LOCK:
        if CACHE['data'] is not None and time.time()-CACHE['at']<TTL: return CACHE['data']
        items=[]; sources={}
        for source,urls in FEEDS.items():
            result,info=fetch(source,urls); items.extend(result); sources[source]=info
        seen=set(); unique=[]
        for item in sorted(items,key=lambda x:x['timestamp'],reverse=True):
            key=item['url'].split('?')[0].rstrip('/')
            if key not in seen: seen.add(key); unique.append(item)
        data={'articles':unique[:150],'sources':sources,'updated':datetime.now(timezone.utc).isoformat(),
              'errors':[name for name,info in sources.items() if info['status']=='error'],
              'status':'ok' if unique else ('error' if all(v['status']=='error' for v in sources.values()) else 'empty')}
        CACHE.update(at=time.time(),data=data)
        return data

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

def article_for(original):
    if original not in {a['url'] for a in news()['articles']}:
        raise ValueError('Article not in current feed')
    if not allowed_publisher(original): raise ValueError('Publisher not allowed')
    req=Request(original,headers={'User-Agent':'Mozilla/5.0 (compatible; KalPa365Reader/1.3)','Accept':'text/html'})
    with urlopen(req,timeout=12) as response:
        if not allowed_publisher(response.geturl()): raise ValueError('Unexpected redirect')
        if 'html' not in response.headers.get('Content-Type','text/html'): raise ValueError('Not HTML')
        raw=response.read(1_500_001)
        if len(raw)>1_500_000: raise ValueError('Article too large')
        decoded=raw.decode(response.headers.get_content_charset() or 'utf-8','replace')
    parser=ReaderParser(); parser.feed(decoded)
    paragraphs=list(dict.fromkeys(parser.paragraphs))
    if len(paragraphs)<3 or sum(map(len,paragraphs))<400:
        return {'status':'summary','paragraphs':[],'original_url':original,'message':'Kokotekstiä ei ollut saatavilla.'}
    return {'status':'full','paragraphs':paragraphs[:100],'original_url':original}

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

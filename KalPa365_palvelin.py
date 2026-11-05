#!/usr/bin/env python3
"""Liiga365 v0.3 — direct publisher news and shared Liiga fixtures."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse, quote, parse_qs, unquote, urljoin
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
import json, os, re, time, threading, pathlib, html, sqlite3, unicodedata
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
PORT = int(os.environ.get('PORT', '8766'))
TTL = 300
DB_PATH = pathlib.Path(os.environ.get('KALPA365_DB', str(ROOT / 'kalpa365_history.sqlite3')))
HISTORY_DAYS = 30
LOCK = threading.Lock()
CACHE = {'at': 0, 'data': None, 'refreshing': False}
# Only one refresh is allowed even if multiple browsers request news at once.
REFRESH_LOCK = threading.Lock()
SOURCE_WORKERS = 8
FREE_CACHE = {}
FREE_CACHE_LOCK = threading.Lock()
FEEDS = {
    'MTV Uutiset': ['https://www.mtvuutiset.fi/api/feed/rss/uutiset_uusimmat'],
    'SuomiKiekko': [
        'https://www.suomikiekko.com/feed/',
        'https://www.suomikiekko.com/?s=KalPa&feed=rss2',
    ],
    'Yle.fi': [
        'https://yle.fi/rss/urheilu',
        'https://yle.fi/rss/t/18-141764/fi',
        'https://yle.fi/rss/uutiset/tuoreimmat',
        'https://yle.fi/rss/tuoreimmat',
    ],
}

# Osa julkaisijoiden RSS-osoitteista on kokeellisia.
# Virheet raportoidaan lähdekohtaisesti eikä niitä peitetä.
# Lähteen mahdollinen virhe näkyy /api/news-vastauksen sources-kentässä.
POSITIVE = re.compile(r'(?<!\w)kalpa(?:n|lle|lta|ssa|sta|an|a)?(?!\w)|kuopion\s+kalpa', re.I)
NEGATIVE = re.compile(r'kalpa(?:na|lla)?\s+(?:ruoka|esine|kukka)|kalpa\s+miekk', re.I)

ALLOWED_PUBLISHERS = (
    'liiga.fi',
    'yle.fi',
    'mtvuutiset.fi',
    'kalpa.fi',
    'suomikiekko.com',
    'kiekkouutiset.fi',
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
# Remove third-party social embeds before their HTML becomes plain article text.
# In particular, a quoted X/Twitter embed often includes its script, a t.co URL,
# and the attribution/date; none of those is the article's own prose.
SOCIAL_EMBED_MARKER = re.compile(
    r'(?:twitter-tweet|instagram-media|tiktok-embed|fb-post|facebook-post|'
    r'platform\.(?:twitter|x)\.com/widgets\.js|www\.instagram\.com/embed|'
    r'platform\.tiktok\.com/embed)', re.I)
SOCIAL_EMBED_BLOCKS = re.compile(
    r'<(?:blockquote|div|iframe)\b(?=[^>]*\b(?:twitter-tweet|instagram-media|'
    r'tiktok-embed|fb-post|facebook-post|\b(?:twitter|instagram|tiktok)[-_]embed)\b)'
    r'[^>]*>.*?</(?:blockquote|div|iframe)\s*>', re.I | re.S)
SOCIAL_SCRIPT = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*['\"]?https?://(?:platform\.(?:twitter|x)\.com/widgets\.js|platform\.tiktok\.com/[^>]*|www\.instagram\.com/[^>]*)[^>]*>\s*</script\s*>",
    re.I | re.S)
SOCIAL_URL_LINE = re.compile(r'^(?:https?://(?:t\.co/[\w-]+|x\.com/[^\s]+|twitter\.com/[^\s]+)|'
                             r'@\w+\s*\|\s*#\w+)\s*$', re.I)

def remove_social_markup(value):
    value = html.unescape(str(value or ''))
    value = SOCIAL_EMBED_BLOCKS.sub(' ', value)
    value = SOCIAL_SCRIPT.sub(' ', value)
    return value

def clean_article_paragraphs(paragraphs):
    cleaned = []
    for paragraph in paragraphs:
        text = remove_social_markup(paragraph)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = html.unescape(text)
        # Drop standalone embed URLs, platform script references, and widget leftovers.
        text = re.sub(r'https?://(?:t\.co/\S+|platform\.(?:twitter|x)\.com/widgets\.js\S*)', '', text, flags=re.I)
        text = re.sub(r'\s+', ' ', text).strip()
        if not text or SOCIAL_URL_LINE.fullmatch(text) or SOCIAL_EMBED_MARKER.search(text):
            continue
        cleaned.append(text)
    return cleaned

def strip_markup(value):
    value = remove_social_markup(value)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', value)).strip()

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
            # Retire removed publishers from stored history too.
            db.execute("DELETE FROM articles WHERE json_extract(payload, '$.source') IN ('IS', 'IL', 'Savon Sanomat', 'Jatkoaika', 'Keskisuomalainen', 'Etelä-Suomen Sanomat', 'Karjalainen', 'Kaleva', 'Pallomeri.net', 'Kiekkoareena', 'UrheiluSuomi')")
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
    'KalPa.fi': [
        'https://kalpa.fi/fi-fi/cg/2026-2027/60/',
        'https://kalpa.fi/?lang=fi-FI',
        'https://kalpa.fi/',
    ],
    'SuomiKiekko': ['https://www.suomikiekko.com/?s=KalPa', 'https://www.suomikiekko.com/', 'https://www.suomikiekko.com/uusimmat/'],
    'Kiekkouutiset': ['https://kiekkouutiset.fi/?s=KalPa', 'https://kiekkouutiset.fi/liiga/'],
    'MTV Uutiset': [
        'https://www.mtvuutiset.fi/tuoreimmat/urheilu',
        'https://www.mtvuutiset.fi/liiga',
        'https://www.mtvuutiset.fi/liiga/kalpa',
    ],
}

class DirectLinkParser(HTMLParser):
    def __init__(self, source, base):
        super().__init__(convert_charrefs=True)
        self.source, self.base = source, base
        self.active = None
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img' and self.active is not None:
            # Many publisher cards use an image-only anchor; image alt is the title.
            alt = attrs.get('alt', '')
            if alt and self.source != 'KalPa.fi': self.active[1].append(alt)
            return
        if tag != 'a': return
        href = attrs.get('href', '')
        link = urljoin(self.base, href)
        path = urlparse(link).path
        if self.source == 'MTV Uutiset':
            valid_path = bool(re.fullmatch(r'/artikkeli/[^/?#]+/\d{6,10}/?', path, re.I))
        elif self.source == 'KalPa.fi':
            valid_path = bool(re.match(r'^/fi-fi/article/[^/]+/[^/]+/\d+/?$', path))
        elif self.source == 'SuomiKiekko':
            # Publisher uses dated permalink URLs: /2026/10/article-slug/
            valid_path = bool(re.fullmatch(r'/20\d{2}/(?:0?[1-9]|1[0-2])/[a-z0-9-]+/?', path, re.I))
        elif self.source == 'Kiekkouutiset':
            # Article links, not category or index pages.
            valid_path = bool(re.fullmatch(r'/(?:liiga|uutiset|jaakiekko)/[a-z0-9-]{12,}/?', path, re.I))
        else:
            valid_path = path.startswith('/fi/uutiset/')
        if valid_path and allowed_publisher(link):
            self.active = [link.split('#')[0], [attrs.get('title', ''), attrs.get('aria-label', '')]]
    def handle_data(self, data):
        if self.active is not None: self.active[1].append(data)
    def handle_endtag(self, tag):
        if tag == 'a' and self.active is not None:
            title = strip_markup(' '.join(x for x in self.active[1] if x))
            if title: self.links.append((title, self.active[0]))
            self.active = None

# SuomiKiekko's search-result headlines do not always contain "KalPa".
# Only promote a search result after checking its *own article body*, date and
# access status. The HTML page's navigation/sidebar text is never evidence.
SUOMIKIEKKO_RESULT_CACHE = {}
SUOMIKIEKKO_REJECTIONS = {}
SUOMIKIEKKO_RESULT_LOCK = threading.Lock()

class SuomiKiekkoBodyParser(HTMLParser):
    """Fallback for article templates without <article>/<main> wrappers.

    Only paragraphs after the real H1 are used. Stop before related-news areas.
    Ignore navigation, figure captions and sidebars.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.after_headline = False
        self.stopped = False
        self.ignore = 0
        self.ignore_stack = []
        self.current = None
        self.paragraphs = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        marker = ' '.join(str(attrs.get(k,'')) for k in ('class','id','role'))
        excluded = tag in ('nav','footer','aside','script','style','figcaption','figure','header') or bool(re.search(r'related|recommend|advert|promo|share|cookie|widget|sidebar', marker, re.I))
        if tag not in ('meta','link','img','br','hr','input','source','wbr','area','embed'):
            self.ignore_stack.append((tag, excluded))
            if excluded: self.ignore += 1
        if self.after_headline and not self.stopped and not self.ignore and tag == 'p':
            self.current = []
    def handle_data(self, data):
        if self.current is not None and not self.ignore:
            self.current.append(data)
    def handle_endtag(self, tag):
        if tag == 'h1' and not self.ignore:
            self.after_headline = True
        if tag == 'p' and self.current is not None:
            text = ' '.join(''.join(self.current).split())
            if re.match(r'^(?:LUE MYÖS|Kuva:|Mainos|Suosittele|Lue lisää|Aiheet\b)', text, re.I):
                self.stopped = True
            elif len(text) > 35 and not self.stopped and len(self.paragraphs) < 35:
                self.paragraphs.append(text)
            self.current = None
        for i in range(len(self.ignore_stack)-1, -1, -1):
            if self.ignore_stack[i][0] == tag:
                self.ignore -= sum(int(v) for _, v in self.ignore_stack[i:])
                del self.ignore_stack[i:]
                break

def verify_suomikiekko_candidate(candidate):
    url = candidate['url']
    if urlparse(url).hostname not in ('suomikiekko.com', 'www.suomikiekko.com'):
        return None
    with SUOMIKIEKKO_RESULT_LOCK:
        cached = SUOMIKIEKKO_RESULT_CACHE.get(url)
        if cached and time.time() - cached[0] < 3600:
            return cached[1]
    item = None
    try:
        request = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; KalPa365/5.5)',
            'Accept': 'text/html'})
        with urlopen(request, timeout=8) as response:
            if urlparse(response.geturl()).hostname not in ('suomikiekko.com', 'www.suomikiekko.com'):
                raise ValueError('Unexpected redirect')
            raw = response.read(1_200_001)
            if len(raw) > 1_200_000:
                raise ValueError('Page too large')
            document = raw.decode(response.headers.get_content_charset() or 'utf-8', 'replace')
        if PAYWALL_HINTS.search(document):
            raise ValueError('Premium article')
        stamp = publication_date_from_html(document, urlparse(url).hostname or '')
        if not stamp or stamp < time.time() - HISTORY_DAYS * 86400 or stamp > time.time() + 86400:
            raise ValueError('No recent original publication date')
        text_parser = ReaderParser()
        text_parser.feed(document)
        fallback = SuomiKiekkoBodyParser()
        fallback.feed(document)
        paragraphs = max(
            (list(dict.fromkeys(text_parser.paragraphs)),
             list(dict.fromkeys(clean_article_paragraphs(jsonld_paragraphs(text_parser.json_scripts)))),
             list(dict.fromkeys(fallback.paragraphs))),
            key=lambda parts: sum(map(len, parts)))
        headline = kalpa_headline_from_html(document)
        # Site search can return related links, ads and unrelated news.
        # Search relevance must occur in the article's actual headline/body.
        if not POSITIVE.search(headline + ' ' + ' '.join(paragraphs)):
            raise ValueError('Not about KalPa')
        if not headline or not valid_kalpa_headline(headline):
            raise ValueError('Missing headline')
        # The article/main parser already excludes sidebars and image captions.
        if not paragraphs or sum(map(len, paragraphs)) < 180:
            raise ValueError('Public article text unavailable')
        item = dict(candidate, title=headline,
                    timestamp=stamp,
                    published=datetime.fromtimestamp(stamp, timezone.utc).isoformat())
        with FREE_CACHE_LOCK:
            FREE_CACHE[url] = (time.time(), True)
    except (OSError, ValueError, TimeoutError, UnicodeError) as exc:
        with SUOMIKIEKKO_RESULT_LOCK:
            SUOMIKIEKKO_REJECTIONS[url] = str(exc)[:110] or type(exc).__name__
    with SUOMIKIEKKO_RESULT_LOCK:
        SUOMIKIEKKO_RESULT_CACHE[url] = (time.time(), item)
    return item

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
            page_candidates = []
            for title, link in parser.links:
                # Search results can have legitimate articles whose headlines
                # never mention KalPa. Check their actual content separately.
                path_label = unquote(urlparse(link).path).replace('-', ' ')
                is_sk_search = source == 'SuomiKiekko' and 's=KalPa' in page
                if (link in seen or NEGATIVE.search(title)
                    or (source not in ('KalPa.fi',) and not is_sk_search
                        and not POSITIVE.search(title + ' ' + path_label))):
                    continue
                seen.add(link)
                page_candidates.append({'title': title, 'source': source, 'url': link,
                                        'summary': '', 'timestamp': 0, 'published': ''})
            if source == 'SuomiKiekko':
                # Limit page fetches so Render doesn't stall on a publisher.
                with ThreadPoolExecutor(max_workers=6) as executor:
                    checked = list(executor.map(verify_suomikiekko_candidate, page_candidates[:70]))
                all_items.extend(item for item in checked if item is not None)
                diagnostics.append({'page': page, 'status': 'ok',
                                    'scanned': len(parser.links),
                                    'candidates_checked': min(len(page_candidates), 70),
                                    'verified_articles': sum(item is not None for item in checked),
                                    'rejection_samples': [
                                        {'url': a['url'], 'reason': SUOMIKIEKKO_REJECTIONS.get(a['url'], 'not accepted')}
                                        for a in page_candidates[:70] if a['url'] in SUOMIKIEKKO_REJECTIONS
                                    ][:8]})
            else:
                all_items.extend(page_candidates)
                diagnostics.append({'page': page, 'status': 'ok', 'scanned': len(parser.links), 'matched_candidates': len(page_candidates), 'sample_titles': [a['title'][:100] for a in page_candidates[:5]]})
        except Exception as exc:
            diagnostics.append({'page': page, 'status': 'error', 'message': f'{type(exc).__name__}: {str(exc)[:120]}'})
    return all_items, {'status': 'ok' if any(d['status']=='ok' for d in diagnostics) else 'error',
                       'count': len(all_items), 'scanned': sum(d.get('scanned', 0) for d in diagnostics),
                       'publisher_links': sum(d.get('scanned', 0) for d in diagnostics),
                       'pages': diagnostics, 'feed': pages[0]}


# Liiga 2.1: extract public news records from embedded JSON and HTML.
# This is intentionally not a guessed/private API endpoint.
LIIGA_NEWS_PAGES = [
    'https://liiga.fi/fi/uutiset?kategoria=uusimmat',
    'https://liiga.fi/fi',
]

def liiga_news_url(value):
    if not isinstance(value, str):
        return ''
    value = html.unescape(value).replace('\\/', '/')
    if value.startswith('/'):
        value = urljoin('https://liiga.fi', value)
    parsed = urlparse(value)
    if parsed.scheme != 'https' or parsed.hostname not in ('liiga.fi', 'www.liiga.fi'):
        return ''
    if not re.fullmatch(r'/fi/uutiset/[^/?#]+', parsed.path):
        return ''
    return 'https://liiga.fi' + parsed.path

def liiga_json_candidates(obj, depth=0):
    if depth > 20:
        return
    if isinstance(obj, list):
        for child in obj[:1000]:
            yield from liiga_json_candidates(child, depth + 1)
    elif isinstance(obj, dict):
        title = next((obj.get(k) for k in ('title', 'headline', 'name')
                      if isinstance(obj.get(k), str)), '')
        url = next((liiga_news_url(obj.get(k)) for k in ('url', 'href', 'link',
                   'canonicalUrl', 'path', 'slug') if liiga_news_url(obj.get(k))), '')
        if title and url:
            yield strip_markup(title), url
        for value in obj.values():
            if isinstance(value, (dict, list)):
                yield from liiga_json_candidates(value, depth + 1)

class LiigaPageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.active = None
        self.scripts = []
        self.script = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('type', '').lower() in (
                'application/json', 'application/ld+json'):
            self.script = []
        if tag == 'a':
            url = liiga_news_url(attrs.get('href', ''))
            if url:
                self.active = [url, []]
    def handle_data(self, value):
        if self.script is not None:
            self.script.append(value)
        if self.active is not None:
            self.active[1].append(value)
    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            self.scripts.append(''.join(self.script))
            self.script = None
        if tag == 'a' and self.active is not None:
            title = strip_markup(' '.join(self.active[1]))
            if title:
                self.links.append((title, self.active[0]))
            self.active = None

def extract_liiga_news(document):
    parser = LiigaPageParser()
    parser.feed(document)
    candidates = list(parser.links)
    json_count = 0
    for script in parser.scripts:
        try:
            data = json.loads(script)
        except (ValueError, TypeError):
            continue
        found = list(liiga_json_candidates(data))
        json_count += len(found)
        candidates.extend(found)
    # Some framework payloads contain JSON escaped as HTML. Match a URL only
    # when an adjacent, explicit headline can be identified; no invented titles.
    seen = set()
    results = []
    for title, url in candidates:
        title = strip_markup(title)
        url = liiga_news_url(url)
        if not url or not title or len(title) < 8 or (url in seen):
            continue
        seen.add(url)
        results.append((title, url))
    return results, {'html_links': len(parser.links), 'json_records': json_count,
                     'json_scripts': len(parser.scripts)}

def liiga_date(value):
    """Parse the observed Liiga newsDate format, including GMT offset."""
    if not isinstance(value, str):
        return 0
    match = re.search(r'^(?:\w{3} )?(\w{3} \d{1,2} \d{4} \d\d:\d\d:\d\d GMT[+-]\d{4})', value)
    if match:
        try:
            return datetime.strptime(match.group(1), '%b %d %Y %H:%M:%S GMT%z').timestamp()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    except ValueError:
        return 0

def liiga_kalpa_main_topic(record):
    """Accept KalPa-specific reporting AND concrete KalPa game events inside roundups."""
    title = strip_markup(str(record.get('articleTitle') or record.get('title') or ''))
    if NEGATIVE.search(title):
        return False, 'unrelated_title'
    if POSITIVE.search(title):
        return True, 'kalpa_in_headline'

    ingress = strip_markup(str(record.get('ingress') or record.get('summary') or record.get('description') or ''))
    body = strip_markup(str(record.get('searchText') or ''))
    opening = (ingress or body)[:550]
    first_sentence = re.split(r'(?<=[.!?])\s+', opening, maxsplit=1)[0][:300]
    generic = re.search(r'\b(?:liiga\s+tiedottaa|otteluohjelma|ottelusiir(?:to|rot|roista)|kooste|tilastonostot|viikkokatsaus)\b', title, re.I)
    if POSITIVE.search(first_sentence) and not generic:
        teams = set(x.lower() for x in re.findall(
            r'\b(?:HIFK|HPK|Ilves|Jukurit|JYP|K-?Espoo|Kärpät|Lukko|Pelicans|SaiPa|Sport|Tappara|TPS|Ässät|Jokerit)\b', opening, re.I))
        if len(teams) <= 1:
            return True, 'kalpa_in_opening'

    # Full article may contain a meaningful KalPa match paragraph even when
    # its headline summarizes multiple teams. Ignore bare historical lists.
    # Sentence boundaries include newlines to avoid combining unrelated rows.
    chunks = re.split(r'(?<=[.!?])\s+|[\r\n]+', body)
    game_action = re.compile(
        r'\b(?:voitt\w*|kaat\w*|kukist\w*|hävi\w*|häv\w*|tappio\w*|'
        r'ottelu\w*|pel\w*|maal\w*|tasoit\w*|ratkais\w*|'
        r'jatkoa\w*|ylivoima\w*|alivoima\w*|siirt\w*|siirty\w*|'
        r'kohta\w*|nous\w*|katkais\w*)\b', re.I)
    for chunk in chunks:
        chunk = chunk.strip()
        if not POSITIVE.search(chunk) or not game_action.search(chunk):
            continue
        if len(chunk) > 650:
            continue
        if re.search(r'\b(?:vuonna|kaudella|historia|ennätysluettelo)\b', chunk, re.I) and not re.search(r'\b2026\b', chunk):
            continue
        return True, 'kalpa_game_event_in_body'
    return False, 'no_relevant_kalpa_event'


def liiga_rejection_sample(record, reason):
    """A short, bounded public metadata preview for reviewing rejected stories.

    No full article text is copied into the diagnostic response.
    """
    title = strip_markup(str(record.get('articleTitle') or record.get('title') or ''))
    lead = strip_markup(str(record.get('ingress') or record.get('summary') or record.get('description') or ''))
    body = strip_markup(str(record.get('searchText') or ''))
    # Locate the first KalPa mention without treating it as proof of main-topic relevance.
    mention = POSITIVE.search(body)
    context = ''
    if mention:
        start = max(0, mention.start() - 85)
        end = min(len(body), mention.end() + 105)
        context = ('…' if start else '') + body[start:end] + ('…' if end < len(body) else '')
    # Inspect only simple, structured metadata fields; avoid exposing raw nested payloads.
    tags = {}
    for key in ('team', 'teams', 'teamId', 'teamIds', 'tags', 'categories', 'category'):
        value = record.get(key)
        if isinstance(value, str):
            tags[key] = value[:160]
        elif isinstance(value, list):
            tags[key] = [str(x)[:60] for x in value[:5]]
    return {'title': title[:180], 'url': liiga_news_url(record.get('url', '')),
            'reason': reason, 'lead': (lead or body)[:220],
            'kalpa_in_title': bool(POSITIVE.search(title)),
            'kalpa_in_body': bool(mention), 'mention_context': context,
            'structured_fields': tags}


def fetch_liiga_news():
    """Page through Liiga news and keep only KalPa-focused articles."""
    endpoint = 'https://liiga.fi/api/v2/news'
    found, seen, diagnostics = [], set(), []
    # Previously only 80 articles were scanned, and searchText was cut to 350 chars.
    # Scan up to 320 articles, retaining the existing 30-day publication filter.
    page_size = 16
    max_pages = max(1, min(30, int(os.environ.get('KALPA365_LIIGA_PAGES', '20'))))
    cutoff = time.time() - HISTORY_DAYS * 86400
    for offset in range(0, page_size * max_pages, page_size):
        params = {'limitRequest': page_size, 'offsetRequest': offset,
                  'builderOffsetRequest': offset, 'legacyOffsetRequest': offset}
        url = endpoint + '?' + urlencode(params)
        try:
            request = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; KalPa365/2.8)',
                'Accept': 'application/json',
                'Referer': 'https://liiga.fi/fi/uutiset?kategoria=uusimmat'
            })
            with urlopen(request, timeout=12) as response:
                if not allowed_publisher(response.geturl()):
                    raise ValueError('Unexpected redirect')
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ValueError('JSON response too large')
            payload = json.loads(raw.decode('utf-8-sig'))
            records = payload.get('articles', []) if isinstance(payload, dict) else []
            if not isinstance(records, list):
                raise ValueError('Expected articles list')
            matches, relevant = 0, 0
            rejection_reasons = {}
            rejected_samples = []
            for record in records:
                if not isinstance(record, dict):
                    continue
                title = strip_markup(str(record.get('articleTitle') or record.get('title') or ''))
                link = liiga_news_url(record.get('url', ''))
                if not title or not link or link in seen:
                    continue
                seen.add(link)
                timestamp = liiga_date(record.get('newsDate') or record.get('published') or '')
                if timestamp and timestamp < cutoff:
                    continue
                relevant += 1
                accepted, reason = liiga_kalpa_main_topic(record)
                if not accepted:
                    rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                    if len(rejected_samples) < 16:
                        rejected_samples.append(liiga_rejection_sample(record, reason))
                    continue
                lead = strip_markup(str(record.get('ingress') or record.get('summary') or ''))
                if not lead:
                    body = str(record.get('searchText') or '')
                    lead = strip_markup(body[:280])
                found.append({'title': title, 'source': 'Liiga.fi', 'url': link,
                              'summary': lead[:400], 'timestamp': timestamp,
                              'published': str(record.get('newsDate') or record.get('published') or '')})
                matches += 1
            diagnostics.append({'url': url, 'status': 'ok', 'scanned': len(records),
                                'within_30_days': relevant, 'matches': matches, 'rejected': rejection_reasons,
                                'rejected_samples': rejected_samples, 'bytes': len(raw)})
            if len(records) < page_size:
                break
        except Exception as exc:
            diagnostics.append({'url': url, 'status': 'error',
                                'message': f'{type(exc).__name__}: {str(exc)[:160]}'})
            break
    success = any(d['status'] == 'ok' for d in diagnostics)
    return found, {'status': 'ok' if success else 'error',
                   'count': len(found), 'scanned': len(seen),
                   'publisher_links': len(seen), 'pages': diagnostics,
                   'feed': endpoint, 'search_pages': len(diagnostics),
                   'note': 'v2.8: accepts concrete KalPa game events inside league roundups; rejects bare historical mentions.'}


def article_title_key(title):
    """Normalize superficial punctuation, diacritics and publisher suffixes."""
    title = strip_markup(str(title or '')).casefold()
    title = re.sub(r'\s+[|–-]\s+(?:yle|yle\.fi|is|iltasanomat|iltalehti|mtv(?: uutiset)?|liiga(?:\.fi)?|savon sanomat|jatkoaika)\s*$', '', title)
    title = ''.join(c for c in unicodedata.normalize('NFKD', title) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', title).strip()


def remove_duplicate_articles(articles):
    """Remove identical and near-identical headlines; preserve distinct reporting.

    A near match requires meaningful headline length, strong lexical overlap,
    and a high character similarity. Different articles about one match remain.
    """
    kept = []
    seen_urls = set()
    signatures = []
    for article in sorted(articles, key=lambda a: (
        allowed_publisher(str(a.get('url') or '')),
        float(a.get('timestamp') or 0)
    ), reverse=True):
        url = str(article.get('url') or '').split('#')[0].split('?')[0].rstrip('/')
        key = article_title_key(article.get('title'))
        if not key or url in seen_urls:
            continue
        words = set(key.split())
        duplicate = False
        for old_key, old_words in signatures:
            if key == old_key:
                duplicate = True
                break
            if (len(key) >= 48 and len(old_key) >= 48 and
                min(len(words), len(old_words)) >= 7 and
                len(words & old_words) / max(len(words | old_words), 1) >= .80 and
                SequenceMatcher(None, key, old_key).ratio() >= .88):
                duplicate = True
                break
        if duplicate:
            continue
        kept.append(article)
        seen_urls.add(url)
        signatures.append((key, words))
    return kept



PAYWALL_HINTS = re.compile(
    r'"isAccessibleForFree"\s*:\s*(?:false|"false")|'
    r'"isAccessibleForFree"\s*:\s*"?False"?|'
    r'"paywall"\s*:\s*true', re.I)
PREMIUM_TITLE = re.compile(r'(?i)(?:^|[\s:|–-])(?:IL\s*Plus|IS\s*Extra|Plus|Premium|Tilaajille)(?:$|[\s:|–-])')

def is_verified_free(article):
    """Conservative: only keep publicly readable articles, never guess from source."""
    url = str(article.get('url') or '')
    if not allowed_publisher(url) or PREMIUM_TITLE.search(article.get('title') or ''):
        return False
    # KalPa publishes its own official news openly. Do not reject these
    # articles for a short body, image-only content or imperfect text parsing.
    # URL must be a genuine KalPa article; the 30-day publication-date gate
    # runs earlier in news() and still applies to every source.
    parsed = urlparse(url)
    if parsed.hostname in ('kalpa.fi', 'www.kalpa.fi') and re.fullmatch(
        r'/fi-fi/article/[^/]+/[^/]+/\d+/?', parsed.path, re.I
    ):
        return True
    now = time.time()
    with FREE_CACHE_LOCK:
        cached = FREE_CACHE.get(url)
        if cached and now - cached[0] < 3600:
            return cached[1]
    ok = False
    try:
        if urlparse(url).hostname == 'liiga.fi':
            result = fetch_liiga_article(url)
            ok = result.get('status') == 'full' and sum(map(len, result.get('paragraphs', []))) >= 450
        else:
            req = Request(url, headers={'User-Agent':'Mozilla/5.0 (compatible; KalPa365Reader/1.8)', 'Accept':'text/html'})
            with urlopen(req, timeout=7) as response:
                if not allowed_publisher(response.geturl()):
                    raise ValueError('Unexpected redirect')
                raw = response.read(900_001)
                if len(raw)>900_000: raise ValueError('Too large')
                html_text = raw.decode(response.headers.get_content_charset() or 'utf-8', 'replace')
            if not PAYWALL_HINTS.search(html_text):
                parser=ReaderParser(); parser.feed(html_text)
                visible=list(dict.fromkeys(parser.paragraphs))
                structured=list(dict.fromkeys(jsonld_paragraphs(parser.json_scripts)))
                paragraphs=max((visible, structured), key=lambda ps:sum(map(len,ps)))
                ok = len(paragraphs)>=2 and sum(map(len,paragraphs))>=450
    except (Exception):
        ok = False
    with FREE_CACHE_LOCK:
        FREE_CACHE[url] = (now, ok)
    return ok


# v5.1: resolve publication dates from original article metadata, not crawl time.
DATE_CACHE = {}
DATE_CACHE_LOCK = threading.Lock()
DATE_META_NAMES = {'article:published_time', 'og:published_time', 'datepublished',
                   'pubdate', 'publishdate', 'date', 'parsely-pub-date',
                   'dc.date.issued', 'dc.date.created', 'citation_publication_date'}

def parse_publication_date(value):
    if not isinstance(value, str) or not value.strip(): return 0
    value = value.strip()
    finnish = re.fullmatch(r'(\d{1,2})\.(\d{1,2})\.(20\d{2})(?:\s+(\d{1,2}):(\d{2}))?\.?', value)
    if finnish:
        from datetime import timedelta
        day, month, year, hour, minute = finnish.groups()
        try:
            # Finnish publisher dates are local time in Finland; use local
            # timezone with DST instead of interpreting midnight as UTC.
            from zoneinfo import ZoneInfo
            dt = datetime(int(year), int(month), int(day), int(hour or 12), int(minute or 0), tzinfo=ZoneInfo('Europe/Helsinki'))
            return dt.timestamp()
        except (ValueError, OverflowError):
            return 0
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, OverflowError): pass
    try: return parsedate_to_datetime(value).timestamp()
    except (ValueError, TypeError, OverflowError): return 0

class PublicationDateParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.metadata=[];self.time_values=[];self.scripts=[];self.script_parts=None
        self.in_time=False;self.time_text=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='meta':
            name=(attrs.get('property') or attrs.get('name') or attrs.get('itemprop') or '').lower()
            if name in DATE_META_NAMES or name=='datepublished':
                self.metadata.append(attrs.get('content',''))
        if tag=='time':
            dt=attrs.get('datetime') or attrs.get('content')
            if dt:self.time_values.append(dt)
            self.in_time=True;self.time_text=[]
        if tag=='script' and attrs.get('type','').lower()=='application/ld+json':self.script_parts=[]
    def handle_data(self,data):
        if self.script_parts is not None:self.script_parts.append(data)
        if self.in_time:self.time_text.append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.script_parts is not None:
            self.scripts.append(''.join(self.script_parts));self.script_parts=None
        if tag=='time' and self.in_time:
            self.time_values.append(''.join(self.time_text).strip());self.in_time=False

def structured_published(scripts):
    values=[]
    def visit(obj):
        if isinstance(obj,list):
            for x in obj:visit(x)
        elif isinstance(obj,dict):
            types=obj.get('@type',[])
            if isinstance(types,str):types=[types]
            if any(str(t).lower().endswith(('article','posting')) for t in types):
                if obj.get('datePublished'):values.append(obj['datePublished'])
            for key in ('@graph','mainEntity','mainEntityOfPage'):
                if key in obj:visit(obj[key])
    for script in scripts:
        try:visit(json.loads(script))
        except (ValueError,TypeError,RecursionError):pass
    return values

class ArticleHeaderDateParser(HTMLParser):
    """Read a date shown near article headline, not dates within article body."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_h1 = False
        self.after_h1 = False
        self.text = []
        self.length = 0
        self.ignore_depth = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','nav','footer','aside'):
            self.ignore_depth += 1
        if tag == 'h1' and not self.ignore_depth:
            self.in_h1 = True
    def handle_endtag(self, tag):
        if tag == 'h1' and self.in_h1:
            self.in_h1 = False
            self.after_h1 = True
        if tag in ('script','style','nav','footer','aside') and self.ignore_depth:
            self.ignore_depth -= 1
    def handle_data(self, data):
        if self.after_h1 and not self.ignore_depth and self.length < 500:
            self.text.append(data)
            self.length += len(data)

class KalpaHeadingDateParser(HTMLParser):
    """Find a publisher date adjacent to H1, including *before* the heading.

    KalPa's templates can place publication date above the headline; the old
    after-H1-only parser ignored those dates and silently dropped fresh news.
    Do not take dates from generic article body, fixtures or match schedules.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.h1_start = None
        self.h1_end = None
        self.hidden = 0
        self.in_h1 = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'nav', 'footer', 'aside', 'noscript'):
            self.hidden += 1
        if tag == 'h1' and not self.hidden and self.h1_start is None:
            self.in_h1 = True
            self.h1_start = len(''.join(self.parts))

    def handle_data(self, data):
        if not self.hidden and len(''.join(self.parts)) < 22000:
            self.parts.append(' ' + data.strip() + ' ')

    def handle_endtag(self, tag):
        if tag == 'h1' and self.in_h1:
            self.h1_end = len(''.join(self.parts))
            self.in_h1 = False
        if tag in ('script', 'style', 'nav', 'footer', 'aside', 'noscript') and self.hidden:
            self.hidden -= 1

    def nearest_date(self):
        if self.h1_start is None:
            return 0
        text = ' '.join(''.join(self.parts).split())
        # Recalculate headline position against normalized text: raw positions
        # are only for slicing the original concatenated string.
        raw = ''.join(self.parts)
        before = ' '.join(raw[max(0, self.h1_start-200):self.h1_start].split())
        after = ' '.join(raw[self.h1_end or self.h1_start:(self.h1_end or self.h1_start)+240].split())
        pattern = r'(?<!\d)(\d{1,2}\.\d{1,2}\.20\d{2}(?:\s+(?:klo\s*)?\d{1,2}[:.]\d{2})?)(?!\d)'
        # Nearest publication date is normally immediately above the H1.
        choices = list(re.finditer(pattern, before, re.I))
        if choices:
            found = choices[-1].group(1)
            return parse_publication_date(re.sub(r'\s+klo\s+', ' ', found, flags=re.I).replace('klo ', '').replace(' ', ' ', 1))
        match = re.search(pattern, after, re.I)
        if match:
            found = re.sub(r'\s+klo\s+', ' ', match.group(1), flags=re.I)
            # HH.MM clock notation is allowed by the site's visible timestamp.
            found = re.sub(r'(\d{1,2}):(\d{2})$', r'\1:\2', found)
            return parse_publication_date(found)
        return 0


def publication_date_from_html(raw, source_host=''):
    parser = PublicationDateParser(); parser.feed(raw)
    for value in structured_published(parser.scripts) + parser.metadata + parser.time_values:
        stamp = parse_publication_date(value)
        if stamp: return stamp
    if source_host in ('kalpa.fi', 'www.kalpa.fi', 'api.kalpa.fi'):
        header = KalpaHeadingDateParser(); header.feed(raw)
        stamp = header.nearest_date()
        if stamp: return stamp
    if source_host in ('suomikiekko.com', 'www.suomikiekko.com'):
        header = ArticleHeaderDateParser(); header.feed(raw)
        match = re.search(r'(?<!\d)(\d{1,2}\.\d{1,2}\.20\d{2}(?:\s+\d{1,2}:\d{2})?)(?!\d)', ' '.join(header.text)[:350])
        if match: return parse_publication_date(match.group(1))
    return 0

class ArticleHeadlineParser(HTMLParser):
    """Retrieve the real article heading, never figure captions or image alt text."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = []
        self.h1 = []
        self.in_h1 = False
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            field = (attrs.get('property') or attrs.get('name') or '').lower()
            if field in ('og:title', 'twitter:title'):
                self.meta.append(attrs.get('content', ''))
        if tag in ('figure', 'figcaption', 'script', 'style'):
            self.skip += 1
        if tag == 'h1' and not self.skip:
            self.in_h1 = True
    def handle_data(self, data):
        if self.in_h1 and not self.skip:
            self.h1.append(data)
    def handle_endtag(self, tag):
        if tag == 'h1':
            self.in_h1 = False
        if tag in ('figure', 'figcaption', 'script', 'style') and self.skip:
            self.skip -= 1

def valid_kalpa_headline(title):
    title = strip_markup(str(title or '')).strip()
    return (len(title) >= 12 and not re.match(r'^(?:kuva|kuvat|image|photo|picture|©|\(c\))\s*[:#–-]?\s', title, re.I)
            and not re.fullmatch(r'(?:kalpa|kalpa\.fi|uutiset)', title, re.I))

def kalpa_headline_from_html(raw):
    parser = ArticleHeadlineParser()
    parser.feed(raw)
    structured = []
    date_parser = PublicationDateParser()
    date_parser.feed(raw)
    for script in date_parser.scripts:
        try:
            def visit(obj):
                if isinstance(obj, list):
                    for x in obj: visit(x)
                elif isinstance(obj, dict):
                    typ = obj.get('@type', [])
                    types = [typ] if isinstance(typ, str) else typ if isinstance(typ, list) else []
                    if any(str(x).lower().endswith(('article','posting')) for x in types):
                        structured.append(obj.get('headline', ''))
                    for k in ('@graph','mainEntity'):
                        if k in obj: visit(obj[k])
            visit(json.loads(script))
        except (ValueError, TypeError, RecursionError):
            pass
    for candidate in [' '.join(parser.h1), *structured, *parser.meta]:
        candidate = re.sub(r'\s+[|–-]\s*(?:KalPa|KalPa\.fi)\s*$', '', strip_markup(str(candidate or '')), flags=re.I).strip()
        if valid_kalpa_headline(candidate):
            return candidate[:220]
    return ''

KALPA_HEADLINE_CACHE = {}
KALPA_HEADLINE_LOCK = threading.Lock()

def resolve_kalpa_headline(item):
    """Refresh even old SQLite-history titles; fall back only to a non-caption title."""
    url = str(item.get('url') or '')
    if item.get('source') != 'KalPa.fi' or urlparse(url).hostname not in ('kalpa.fi', 'www.kalpa.fi'):
        return item
    with KALPA_HEADLINE_LOCK:
        cached = KALPA_HEADLINE_CACHE.get(url)
    if cached and time.time() - cached[0] < 21600:
        title = cached[1]
    else:
        title = ''
        try:
            req = Request(url, headers={'User-Agent':'Mozilla/5.0 (compatible; KalPa365/5.4)', 'Accept':'text/html'})
            with urlopen(req, timeout=8) as response:
                if not allowed_publisher(response.geturl()): raise ValueError('Unexpected redirect')
                raw = response.read(1_200_001)
                if len(raw) > 1_200_000: raise ValueError('Page too large')
                decoded = raw.decode(response.headers.get_content_charset() or 'utf-8', 'replace')
            title = kalpa_headline_from_html(decoded)
        except (OSError, ValueError, TimeoutError, UnicodeError):
            pass
        with KALPA_HEADLINE_LOCK:
            KALPA_HEADLINE_CACHE[url] = (time.time(), title)
    if title:
        item = dict(item)
        item['title'] = title
    return item

def resolve_article_publication(item):
    url=str(item.get('url') or '')
    if not allowed_publisher(url):return item
    # Preserve a trustworthy feed timestamp when already present.
    if float(item.get('timestamp') or 0)>0:return item
    now=time.time()
    with DATE_CACHE_LOCK:
        cached=DATE_CACHE.get(url)
        if cached and now-cached[0]<21600:stamp=cached[1]
        else:stamp=None
    if stamp is None:
        stamp=0
        try:
            req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; KalPa365/5.1)', 'Accept':'text/html'})
            with urlopen(req,timeout=8) as response:
                if not allowed_publisher(response.geturl()):raise ValueError('Unexpected redirect')
                if 'html' not in response.headers.get('Content-Type','text/html'):raise ValueError('Not HTML')
                raw=response.read(1_200_001)
                if len(raw)>1_200_000:raise ValueError('Too large')
                decoded=raw.decode(response.headers.get_content_charset() or 'utf-8','replace')
            stamp=publication_date_from_html(decoded,urlparse(url).hostname or '')
        except (OSError,ValueError,TimeoutError,UnicodeError):pass
        with DATE_CACHE_LOCK:DATE_CACHE[url]=(now,stamp)
    if stamp:
        item=dict(item);item['timestamp']=stamp
        item['published']=datetime.fromtimestamp(stamp,timezone.utc).isoformat()
    return item

def resolve_mtv_headline(item):
    if item.get('source') != 'MTV Uutiset' or item.get('title') != 'MTV Uutiset – KalPa':
        return item
    try:
        req = Request(item['url'], headers={'User-Agent':'Mozilla/5.0 (compatible; KalPa365/6.0)'})
        with urlopen(req, timeout=7) as response:
            if not allowed_publisher(response.geturl()): raise ValueError('Unexpected redirect')
            raw = response.read(1_200_001)
            if len(raw)>1_200_000: raise ValueError('Article too large')
            document = raw.decode(response.headers.get_content_charset() or 'utf-8', 'replace')
        title = kalpa_headline_from_html(document)
        if title and valid_kalpa_headline(title):
            item = dict(item, title=title)
    except (OSError, ValueError, TimeoutError, UnicodeError): pass
    return item


def _timed_source(kind, source, targets=None):
    """Independent publisher fetch; failures do not cancel other publishers."""
    started = time.monotonic()
    try:
        if kind == 'rss':
            articles, info = fetch(source, targets)
        elif kind == 'direct':
            articles, info = fetch_direct(source, targets)
        else:
            articles, info = fetch_liiga_news()
    except Exception as exc:
        articles, info = [], {'status': 'error', 'count': 0,
                              'message': f'{type(exc).__name__}: {str(exc)[:160]}'}
    info['duration_ms'] = round((time.monotonic() - started) * 1000)
    return kind, source, articles, info


def _publish_progress(items, sources, started):
    """Publish dated, verified partial results; never replace verified results with placeholders."""
    cutoff = time.time() - HISTORY_DAYS * 86400
    candidates = [a for a in items if cutoff <= float(a.get('timestamp') or 0) <= time.time() + 86400
                  and allowed_publisher(str(a.get('url') or ''))
                  and (a.get('source') != 'KalPa.fi' or valid_kalpa_headline(a.get('title')))]
    unique = list({a['url']: a for a in sorted(candidates, key=lambda x: float(x['timestamp']))}.values())
    unique.sort(key=lambda x: float(x['timestamp']), reverse=True)
    # Avoid huge page-verification loops during progressive updates.
    recent = unique[:12]
    with ThreadPoolExecutor(max_workers=4) as executor:
        verified = list(executor.map(is_verified_free, recent))
    visible = [a for a, ok in zip(recent, verified) if ok]
    with LOCK:
        old = CACHE.get('data') or {}
        old_articles = old.get('articles') or []
        merged = remove_duplicate_articles(visible + old_articles)
        merged = [a for a in merged if cutoff <= float(a.get('timestamp') or 0) <= time.time() + 86400
                  and allowed_publisher(str(a.get('url') or ''))]
        merged.sort(key=lambda x: float(x.get('timestamp') or 0), reverse=True)
        CACHE['data'] = {
            'articles': merged[:150], 'sources': dict(sources),
            'source_counts': {name: sum(a.get('source') == name for a in merged) for name in sources},
            'status': 'ok' if merged else 'loading', 'errors': [],
            'updated': datetime.now(timezone.utc).isoformat(),
            'refreshing': True, 'partial': True,
            'build_duration_ms': round((time.monotonic() - started) * 1000),
        }


def _build_news():
    """Collect publishers concurrently; release validated partial snapshots as they finish."""
    started = time.monotonic()
    items = []
    sources = {}
    work = ([('rss', source, urls) for source, urls in FEEDS.items()]
            + [('direct', source, pages) for source, pages in DIRECT_PAGES.items()]
            + [('liiga', 'Liiga.fi', None)])
    with ThreadPoolExecutor(max_workers=SOURCE_WORKERS) as pool:
        futures = [pool.submit(_timed_source, *job) for job in work]
        for future in as_completed(futures):
            kind, source, found, info = future.result()
            items.extend(found)
            if kind == 'direct':
                sources.setdefault(source, {})['direct_pages'] = info
            else:
                sources.setdefault(source, {}).update(info)
            if found:
                try:
                    _publish_progress(items, sources, started)
                except Exception as exc:
                    print('Progressive news snapshot skipped:', type(exc).__name__, flush=True)
    # All source results are already merged as futures complete.  A removed
    # 'outcomes' variable here previously caused NameError at the end of a
    # refresh, leaving only provisional results visible.

    seen=set(); unique=[]
    for item in sorted(items,key=lambda x:x['timestamp'],reverse=True):
        key=item['url'].split('?')[0].rstrip('/')
        if key not in seen: seen.add(key); unique.append(item)
    # Resolve dates on direct article pages BEFORE merging/filtering history.
    # RSS dates remain unchanged; unknown dates are not fabricated.
    undated=[a for a in unique if not float(a.get('timestamp') or 0)]
    if undated:
        with ThreadPoolExecutor(max_workers=8) as pool:
            resolved=list(pool.map(resolve_article_publication,undated[:120]))
        resolved_by_url={a['url']:a for a in resolved}
        unique=[resolved_by_url.get(a['url'],a) for a in unique]
    historical,history_status=history_merge(unique)
    historical=[a for a in historical if a.get('source') not in ('IS', 'IL', 'Savon Sanomat', 'Jatkoaika', 'Keskisuomalainen', 'Etelä-Suomen Sanomat', 'Karjalainen', 'Kaleva', 'Pallomeri.net', 'Kiekkoareena', 'UrheiluSuomi') and allowed_publisher(str(a.get('url') or ''))]
    # A direct HTML index has no reliable publication timestamp (timestamp=0).
    # Never present such an article as current; publisher-search/RSS articles
    # with a real timestamp remain eligible. This also cleans persisted history.
    stored_undated=[a for a in historical if not float(a.get('timestamp') or 0)]
    if stored_undated:
        with ThreadPoolExecutor(max_workers=8) as pool:
            fixed=list(pool.map(resolve_article_publication,stored_undated[:120]))
        fixed_by_url={a['url']:a for a in fixed}
        historical=[fixed_by_url.get(a['url'],a) for a in historical]
    freshness_cutoff = time.time() - HISTORY_DAYS * 86400
    historical = [a for a in historical
                  if freshness_cutoff <= float(a.get('timestamp') or 0) <= time.time() + 86400]
    # Replace incorrect titles previously stored in SQLite and newly found
    # caption links BEFORE deduplication. Unresolved caption-only cards are hidden.
    kalpa_rows = [a for a in historical if a.get('source') == 'KalPa.fi']
    if kalpa_rows:
        with ThreadPoolExecutor(max_workers=6) as pool:
            corrected = list(pool.map(resolve_kalpa_headline, kalpa_rows[:120]))
        by_url = {a['url']: a for a in corrected}
        historical = [by_url.get(a['url'], a) for a in historical]
    historical = [a for a in historical if a.get('source') != 'KalPa.fi' or valid_kalpa_headline(a.get('title'))]
    mtv_candidates = [a for a in historical if a.get('source') == 'MTV Uutiset' and a.get('title') == 'MTV Uutiset – KalPa']
    if mtv_candidates:
        with ThreadPoolExecutor(max_workers=5) as pool:
            fixed = list(pool.map(resolve_mtv_headline, mtv_candidates[:80]))
        by_url = {a['url']: a for a in fixed}
        historical = [by_url.get(a['url'], a) for a in historical]
        historical = [a for a in historical if a.get('title') != 'MTV Uutiset – KalPa']
    historical = remove_duplicate_articles(historical)
    historical.sort(key=lambda a: float(a.get('timestamp') or 0), reverse=True)
    # Only show articles whose public text could be verified.
    # This intentionally excludes unknown/paywalled links rather than guessing.
    candidates = historical[:500]
    with ThreadPoolExecutor(max_workers=10) as pool:
        verified = list(pool.map(is_verified_free, candidates))
    historical = [a for a, ok in zip(candidates, verified) if ok]
    counts={name:sum(a.get('source')==name for a in historical) for name in sources}
    candidate_counts={name:sum(a.get('source')==name for a in candidates) for name in sources}
    for name in sources:
        sources[name]['candidate_count'] = candidate_counts[name]
        sources[name]['verified_free_count'] = counts[name]
        sources[name]['rejected_count'] = candidate_counts[name] - counts[name]
    data={'articles':historical[:150],'sources':sources,'source_counts':counts,'history_status':history_status,'updated':datetime.now(timezone.utc).isoformat(),
          'errors':[name for name,info in sources.items() if info.get('status')=='error'],
          'status':'ok' if historical else ('error' if all(v.get('status')=='error' for v in sources.values()) else 'empty')}
    data['build_duration_ms'] = round((time.monotonic() - started) * 1000)
    return data


def _refresh_snapshot():
    try:
        result = _build_news()
        with LOCK:
            result['partial'] = False
            CACHE['data'] = result
            CACHE['at'] = time.time()
    except Exception as exc:
        print(f'KalPa365 refresh failed: {type(exc).__name__}: {exc}', flush=True)
        with LOCK:
            CACHE['at'] = time.time()
    finally:
        with LOCK:
            CACHE['refreshing'] = False
        REFRESH_LOCK.release()


def _stored_news_snapshot():
    """Read local historical articles immediately if they exist (best-effort cache)."""
    try:
        with history_connect() as db:
            rows = db.execute('SELECT payload FROM articles WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT 150',
                              (time.time() - HISTORY_DAYS * 86400,)).fetchall()
        articles = [json.loads(row[0]) for row in rows]
        articles = [a for a in articles if allowed_publisher(str(a.get('url') or ''))
                    and float(a.get('timestamp') or 0) > 0]
        return articles
    except (OSError, sqlite3.Error, ValueError, TypeError):
        return []


def news():
    """Always answer immediately; refresh concurrently and expose intermediate results."""
    now = time.time()
    with LOCK:
        if CACHE['data'] is None:
            stored = _stored_news_snapshot()
            CACHE['data'] = {'articles': stored, 'sources': {}, 'source_counts': {},
                             'status': 'ok' if stored else 'loading', 'errors': [],
                             'updated': datetime.now(timezone.utc).isoformat(),
                             'partial': True}
        age = now - CACHE['at']
        if age >= TTL and not CACHE['refreshing'] and REFRESH_LOCK.acquire(blocking=False):
            CACHE['refreshing'] = True
            threading.Thread(target=_refresh_snapshot, daemon=True,
                             name='KalPa365-news-refresh').start()
        data = dict(CACHE['data'])
        data['refreshing'] = CACHE['refreshing']
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
        excluded=parent[0] or tag in ('script','style','nav','footer','aside','form','noscript','svg','iframe','button','header') or bool(re.search(r'related|recommend|advert|promo|share|caption|cookie|paywall|twitter-tweet|instagram-media|tiktok-embed|facebook-post|fb-post',marker,re.I))
        article=parent[1] or tag in ('article','main') or bool(re.search(r'article|story[-_ ]?body|article[-_ ]?(body|content|text)|entry-content|post-content|news-content',marker,re.I))
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
                self.paragraphs.extend(clean_article_paragraphs([value]))
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
    return clean_article_paragraphs([x.strip() for x in re.split(r'\n\s*\n', body) if len(x.strip())>35])

BUILDER_API_KEY = 'f11503eeae084753968caac3899a5d78'  # Public, read-only Builder.io key.
BUILDER_MODEL = 'news-article-v-1'
BUILDER_ENDPOINT = f'https://cdn.builder.io/api/v3/query/{BUILDER_API_KEY}/{BUILDER_MODEL}'

def fetch_liiga_article(original):
    """Read published Liiga article text from the public Builder.io content query."""
    parsed = urlparse(original)
    if parsed.hostname != 'liiga.fi' or not re.fullmatch(r'/fi/uutiset/[a-z0-9-]+/?', parsed.path):
        raise ValueError('Not a supported Liiga news URL')
    params = {
        'omit': 'meta.componentsUsed', 'apiKey': BUILDER_API_KEY,
        'locale': 'fi', 'includeUnpublished': 'false',
        'userAttributes': json.dumps({'urlPath': parsed.path.rstrip('/'),
                                      'host': 'liiga.fi', 'device': 'desktop'}, separators=(',', ':')),
        'options.news-article-v-1.model': json.dumps(BUILDER_MODEL),
    }
    url = BUILDER_ENDPOINT + '?' + urlencode(params)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; KalPa365/2.3)',
                                'Accept': 'application/json', 'Referer': 'https://liiga.fi/'})
    with urlopen(req, timeout=15) as response:
        final = urlparse(response.geturl())
        if final.scheme != 'https' or final.hostname != 'cdn.builder.io':
            raise ValueError('Unexpected Builder.io redirect')
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Builder.io response too large')
    payload = json.loads(raw.decode('utf-8-sig'))
    entries = payload.get(BUILDER_MODEL, []) if isinstance(payload, dict) else []
    if not isinstance(entries, list):
        raise ValueError('Unexpected Builder.io response')
    for item in entries:
        if not isinstance(item, dict) or item.get('published') != 'published':
            continue
        data = item.get('data') or {}
        if not isinstance(data, dict):
            continue
        # The query is URL-targeted; additionally verify the article's explicit URL when present.
        explicit = data.get('url') or data.get('articleUrl') or item.get('previewUrl')
        if isinstance(explicit, str) and explicit:
            check = urlparse(urljoin('https://liiga.fi/', explicit))
            if check.path.rstrip('/') != parsed.path.rstrip('/'):
                continue
        body = data.get('searchText')
        if not isinstance(body, str) or len(body.strip()) < 60:
            continue
        paragraphs = clean_article_paragraphs([chunk.strip() for chunk in re.split(r'\n\s*\n', body)
                      if chunk.strip()])
        return {'status': 'full', 'paragraphs': paragraphs[:100],
                'original_url': original, 'extraction': 'builder.io',
                'title': strip_markup(str(data.get('articleTitle') or item.get('name') or ''))}
    return {'status': 'summary', 'paragraphs': [], 'original_url': original,
            'message': 'Liigan artikkelin tekstiä ei löytynyt Builder.io-rajapinnasta.'}

def article_for(original, verify_only=False):
    # Liiga365 serves other teams too: do not check only the KalPa feed.
    # Requests are limited to the known public publisher allowlist below.
    if not allowed_publisher(original): raise ValueError('Publisher not allowed')
    if urlparse(original).hostname == 'liiga.fi':
        try:
            result = fetch_liiga_article(original)
            if result['status'] == 'full':
                return result
        except (ValueError, OSError, TimeoutError, json.JSONDecodeError):
            pass  # Preserve existing HTML reader fallback.
    req=Request(original,headers={'User-Agent':'Mozilla/5.0 (compatible; KalPa365Reader/1.8)','Accept':'text/html'})
    with urlopen(req,timeout=12) as response:
        if not allowed_publisher(response.geturl()): raise ValueError('Unexpected redirect')
        if 'html' not in response.headers.get('Content-Type','text/html'): raise ValueError('Not HTML')
        raw=response.read(1_500_001)
        if len(raw)>1_500_000: raise ValueError('Article too large')
        decoded=raw.decode(response.headers.get_content_charset() or 'utf-8','replace')
    if PAYWALL_HINTS.search(decoded):
        return {'status':'summary','paragraphs':[], 'original_url':original, 'message':'Artikkeli vaatii tilauksen.'}
    parser=ReaderParser(); parser.feed(decoded)
    visible=list(dict.fromkeys(clean_article_paragraphs(parser.paragraphs)))
    structured=list(dict.fromkeys(clean_article_paragraphs(jsonld_paragraphs(parser.json_scripts))))
    paragraphs=max((visible,structured),key=lambda ps:sum(map(len,ps)))
    min_chars = 450
    min_paras = 2
    if sum(map(len,paragraphs))<min_chars or len(paragraphs)<min_paras:
        return {'status':'summary','paragraphs':[],'original_url':original,
                'message':'Kokotekstiä ei löytynyt julkisesta sivusta.',
                'debug':{'html_paragraphs':len(visible),'jsonld_paragraphs':len(structured)}}
    return {'status':'full','paragraphs':paragraphs[:100],'original_url':original,
            'extraction':'html' if paragraphs is visible else 'jsonld'}

TEAM_LOGO_FILES = frozenset({'kiekko-espoo.jpg', 'jukurit.jpg', 'jyp.jpg', 'sport.jpg', 'ilves.jpg', 'saipa.jpg', 'assat.jpg', 'karpat.jpg', 'tps.jpg', 'hpk.jpg', 'kookoo.jpg', 'pelicans.jpg', 'hifk.jpg', 'kalpa.jpg', 'tappara.jpg', 'lukko.jpg', 'jokerit.jpg'})



# Liiga365 feature branch: isolate team-specific news without changing KalPa365 main.
# The same Liiga API pages are fetched once per refresh, not once per user/team.
TEAMS = {
    'hifk': 'HIFK', 'hpk': 'HPK', 'ilves': 'Ilves', 'jokerit': 'Jokerit',
    'jukurit': 'Jukurit', 'jyp': 'JYP', 'kalpa': 'KalPa', 'kiekko-espoo': 'Kiekko-Espoo',
    'kookoo': 'KooKoo', 'karpat': 'Kärpät', 'lukko': 'Lukko', 'pelicans': 'Pelicans',
    'saipa': 'SaiPa', 'sport': 'Sport', 'tappara': 'Tappara', 'tps': 'TPS', 'assat': 'Ässät'
}
TEAM_ALIASES = {
    'hifk': [r'\bHIFK\b', r'\bHelsingin IFK\b'],
    'hpk': [r'\bHPK\b', r'\bHämeenlinnan Pallokerho\b'],
    'ilves': [r'\bIlves(?:tä|ksen|een|elle|ellä|eltä)?\b', r'\bTampereen Ilves\b'],
    'jokerit': [r'\bJokerit\b', r'\bJokerien\b', r'\bJokereita\b'],
    'jukurit': [r'\bJukurit\b', r'\bJukurien\b', r'\bMikkelin Jukurit\b'],
    'jyp': [r'\bJYP\b', r'\bJyväskylän JYP\b'],
    'kalpa': [r'\bKalPa(?:n|lle|lta|ssa|sta|an|a)?\b', r'\bKuopion KalPa\b'],
    'kiekko-espoo': [r'\bK[- ]Espoo\b', r'\bKiekko[- ]Espoo\b'],
    'kookoo': [r'\bKooKoo\b', r'\bKouvolan KooKoo\b'],
    'karpat': [r'\bKärpät\b', r'\bKärppien\b', r'\bKärppiä\b', r'\bOulun Kärpät\b'],
    'lukko': [r'\bLukko\b', r'\bLukon\b', r'\bRauman Lukko\b'],
    'pelicans': [r'\bPelicans\b', r'\bLahden Pelicans\b'],
    'saipa': [r'\bSaiPa\b', r'\bSaiPan\b', r'\bLappeenrannan SaiPa\b'],
    'sport': [r'\bVaasan Sport\b', r'\bSportin\b', r'\bSportia\b', r'\bSportille\b'],
    'tappara': [r'\bTappara\b', r'\bTapparan\b', r'\bTapparaa\b'],
    'tps': [r'\bTPS\b', r'\bTurun Palloseura\b'],
    'assat': [r'\bÄssät\b', r'\bÄssien\b', r'\bPorin Ässät\b'],
}
TEAM_PATTERNS = {key: re.compile('|'.join(forms), re.I) for key, forms in TEAM_ALIASES.items()}
LEAGUE_CACHE = {'at': 0, 'articles': [], 'refreshing': False, 'error': None, 'updated': None}
LEAGUE_LOCK = threading.RLock()

def team_article_match(team, article):
    if team not in TEAMS: return False
    title = str(article.get('title') or '')
    summary = str(article.get('summary') or '')
    # Team names in title or opening summary only: avoid historic name-drops in full text.
    if team == 'sport' and re.search(r'\b(e[- ]?sport|sports?|sportti)\b', title, re.I):
        return bool(TEAM_PATTERNS[team].search(title+' '+summary[:220]))
    return bool(TEAM_PATTERNS[team].search(title+' '+summary[:220]))

def _fetch_league_pool():
    # Bounded request budget: at most 8 pages * 16 stories per cycle.
    fetched = []; seen = set(); cutoff = time.time() - HISTORY_DAYS * 86400
    for offset in range(0, 128, 16):
        url = 'https://liiga.fi/api/v2/news?' + urlencode({
            'limitRequest':16,'offsetRequest':offset,
            'builderOffsetRequest':offset,'legacyOffsetRequest':offset})
        req = Request(url, headers={'User-Agent':'Mozilla/5.0 (Liiga365 news index)',
                                    'Accept':'application/json','Referer':'https://liiga.fi/'})
        with urlopen(req, timeout=12) as response:
            if not allowed_publisher(response.geturl()): raise ValueError('Unexpected redirect')
            raw = response.read(2_000_001)
            if len(raw)>2_000_000: raise ValueError('Oversized response')
        data = json.loads(raw.decode('utf-8-sig'))
        records = data.get('articles', []) if isinstance(data,dict) else []
        if not isinstance(records,list): raise ValueError('Unexpected Liiga response')
        for rec in records:
            if not isinstance(rec,dict): continue
            title = strip_markup(rec.get('articleTitle') or rec.get('title') or '')
            link = liiga_news_url(rec.get('url') or '')
            stamp = liiga_date(rec.get('newsDate') or rec.get('published') or '')
            if not title or not link or not stamp or stamp < cutoff or link in seen: continue
            seen.add(link)
            summary = strip_markup(rec.get('ingress') or rec.get('summary') or rec.get('searchText') or '')[:400]
            fetched.append({'title':title,'summary':summary,'timestamp':stamp,
                            'published':str(rec.get('newsDate') or ''),'url':link,'source':'Liiga.fi'})
        if len(records)<16: break
    return sorted(fetched,key=lambda a:a['timestamp'],reverse=True)

def _refresh_league_pool():
    try:
        found = _fetch_league_pool()
        with LEAGUE_LOCK:
            LEAGUE_CACHE.update(articles=found,at=time.time(),updated=datetime.now(timezone.utc).isoformat(),error=None)
    except Exception as exc:
        with LEAGUE_LOCK:
            LEAGUE_CACHE.update(at=time.time(),error=f'{type(exc).__name__}: {str(exc)[:160]}')
    finally:
        with LEAGUE_LOCK: LEAGUE_CACHE['refreshing']=False

def team_news(team):
    if team not in TEAMS: return {'status':'error','error':'Unknown team','articles':[]}
    if team == 'kalpa':
        result = news()
        result['team'] = team
        return result
    with LEAGUE_LOCK:
        if time.time()-LEAGUE_CACHE['at']>=TTL and not LEAGUE_CACHE['refreshing']:
            LEAGUE_CACHE['refreshing']=True
            threading.Thread(target=_refresh_league_pool,daemon=True).start()
        pool = list(LEAGUE_CACHE['articles'])
        refreshing = LEAGUE_CACHE['refreshing']
        updated = LEAGUE_CACHE['updated']
        err = LEAGUE_CACHE['error']
    articles=[a for a in pool if team_article_match(team,a)]
    # Matches are conservative: generic words are insufficient without team context.
    return {'team':team,'status':'ok' if pool else ('loading' if refreshing else 'empty'),
            'articles':articles[:100], 'refreshing':refreshing,'partial':refreshing,
            'updated':updated,'sources':{'Liiga.fi':{'count':len(articles),'status':'error' if err else 'ok'}},
            'errors':[err] if err else [],'coverage':'Liiga.fi; additional team sources pending validation'}


# Liiga365 v0.3: Use the same direct publishers as KalPa365, excluding
# KalPa.fi for other teams. Publisher feeds are fetched ONCE for all clubs;
# never use Google News links as articles because they cannot be read reliably.
TEAM_NEWS_FEEDS = {
    'SuomiKiekko': ['https://www.suomikiekko.com/feed/'],
    'Yle.fi': ['https://yle.fi/rss/urheilu', 'https://yle.fi/rss/t/18-141764/fi'],
    'MTV Uutiset': ['https://www.mtvuutiset.fi/api/feed/rss/uutiset_uusimmat'],
}
TEAM_NEWS_DIRECT = {
    'SuomiKiekko': ['https://www.suomikiekko.com/uusimmat/', 'https://www.suomikiekko.com/'],
    'Kiekkouutiset': ['https://kiekkouutiset.fi/liiga/'],
    'MTV Uutiset': ['https://www.mtvuutiset.fi/liiga', 'https://www.mtvuutiset.fi/tuoreimmat/urheilu'],
}
PUBLISHER_CACHE = {'at': 0, 'articles': [], 'refreshing': False, 'error': None,
                   'sources': {}, 'updated': None}
PUBLISHER_LOCK = threading.RLock()

def parse_team_feed(source, raw):
    """Read publisher RSS without the old KalPa-only relevance filter."""
    root = ET.fromstring(raw)
    found,seen=[],set()
    for node in root.iter():
        if local(node.tag) not in ('item','entry'): continue
        title=strip_markup(child_text(node,{'title'}))
        link=child_text(node,{'link'})
        if not link:
            for child in node:
                if local(child.tag)=='link' and child.attrib.get('href') and child.attrib.get('rel','alternate')=='alternate':
                    link=child.attrib['href'].strip();break
        if not title or not allowed_publisher(link) or link in seen:continue
        summary=strip_markup(child_text(node,{'description','summary','encoded','content'}))
        date=child_text(node,{'pubdate','published','updated','date'})
        try:stamp=parsedate_to_datetime(date).timestamp()
        except (ValueError,TypeError,OverflowError):
            try:stamp=datetime.fromisoformat(date.replace('Z','+00:00')).timestamp()
            except (ValueError,TypeError,OverflowError):continue
        if not (time.time()-HISTORY_DAYS*86400 <= stamp <= time.time()+86400):continue
        seen.add(link)
        found.append({'title':title,'url':link,'source':source,'summary':summary[:600],
                      'timestamp':stamp,'published':date})
    return found

def _fetch_team_feed(source, urls):
    collected=[];diagnostics=[]
    for url in urls:
        try:
            req=Request(url,headers={'User-Agent':'Mozilla/5.0 (Liiga365/0.3)',
                                     'Accept':'application/rss+xml,application/xml,*/*'})
            with urlopen(req,timeout=10) as response:
                if not allowed_publisher(response.geturl()):raise ValueError('Unexpected feed redirect')
                raw=response.read(2_000_001)
            if len(raw)>2_000_000:raise ValueError('Feed too large')
            matches=parse_team_feed(source,raw)
            collected.extend(matches)
            diagnostics.append({'url':url,'status':'ok','count':len(matches)})
        except Exception as exc:
            diagnostics.append({'url':url,'status':'error','message':f'{type(exc).__name__}: {str(exc)[:120]}'})
    return collected,{'status':'ok' if any(v['status']=='ok' for v in diagnostics) else 'error',
                      'count':len(collected),'feeds':diagnostics}

def _fetch_team_direct(source,pages):
    found=[];diagnostics=[]
    for page in pages:
        try:
            req=Request(page,headers={'User-Agent':'Mozilla/5.0 (Liiga365/0.3)','Accept':'text/html'})
            with urlopen(req,timeout=10) as response:
                if not allowed_publisher(response.geturl()):raise ValueError('Unexpected page redirect')
                raw=response.read(2_000_001)
                charset=response.headers.get_content_charset() or 'utf-8'
            if len(raw)>2_000_000:raise ValueError('Page too large')
            parser=DirectLinkParser(source,page)
            parser.feed(raw.decode(charset,'replace'))
            count=0
            # Collect a bounded number of promising titles, across ALL teams.
            for title,link in parser.links[:150]:
                if not any(team_article_match(team,{'title':title}) for team in TEAMS):continue
                found.append({'title':title,'url':link,'source':source,'summary':'',
                              'timestamp':0,'published':''})
                count+=1
                if count>=35:break
            diagnostics.append({'url':page,'status':'ok','candidate_count':count})
        except Exception as exc:
            diagnostics.append({'url':page,'status':'error','message':f'{type(exc).__name__}: {str(exc)[:120]}'})
    # Dates for HTML cards are derived from the original publisher pages;
    # never label a missing date as today.
    if found:
        with ThreadPoolExecutor(max_workers=6) as pool:
            found=list(pool.map(resolve_article_publication,found[:60]))
    return [a for a in found if a.get('timestamp')],{
        'status':'ok' if any(v['status']=='ok' for v in diagnostics) else 'error',
        'count':sum(bool(a.get('timestamp')) for a in found),'pages':diagnostics}

def _refresh_publisher_pool():
    jobs=[('rss',src,urls) for src,urls in TEAM_NEWS_FEEDS.items()]
    jobs += [('direct',src,pages) for src,pages in TEAM_NEWS_DIRECT.items()]
    results=[];sources={}
    try:
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures={pool.submit(_fetch_team_feed if kind=='rss' else _fetch_team_direct,src,urls):(kind,src)
                     for kind,src,urls in jobs}
            for future in as_completed(futures):
                kind,src=futures[future]
                try:articles,info=future.result()
                except Exception as exc:articles,info=[],{'status':'error','message':str(exc)[:120]}
                results.extend(articles)
                sources.setdefault(src,{})[kind]=info
                with PUBLISHER_LOCK:
                    # As with v6.22, expose first verified publisher results during refresh.
                    old=PUBLISHER_CACHE.get('articles',[])
                    merged={a['url']:a for a in old+results if a.get('url')}
                    PUBLISHER_CACHE.update(articles=sorted(merged.values(),key=lambda a:a.get('timestamp',0),reverse=True)[:300],
                                           sources=dict(sources))
        with PUBLISHER_LOCK:
            PUBLISHER_CACHE.update(at=time.time(),error=None,
                                   updated=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        with PUBLISHER_LOCK:PUBLISHER_CACHE.update(at=time.time(),error=f'{type(exc).__name__}: {str(exc)[:160]}')
    finally:
        with PUBLISHER_LOCK:PUBLISHER_CACHE['refreshing']=False

def publisher_news():
    with PUBLISHER_LOCK:
        if time.time()-PUBLISHER_CACHE['at']>TTL and not PUBLISHER_CACHE['refreshing']:
            PUBLISHER_CACHE['refreshing']=True
            threading.Thread(target=_refresh_publisher_pool,daemon=True).start()
        return (list(PUBLISHER_CACHE['articles']),PUBLISHER_CACHE['refreshing'],
                dict(PUBLISHER_CACHE['sources']),PUBLISHER_CACHE['error'])

# One shared official schedule for all clubs, cached for 30 minutes.
# Source: https://liiga.fi/api/v2/games, season=2027 means 2026–27.
GAMES_CACHE={'at':0,'games':[],'error':None,'refreshing':False,'updated':None}
GAMES_LOCK=threading.RLock()
GAMES_TTL=1800
TEAM_ID_BY_NAME={
    'hifk':'hifk','ifk':'hifk','hpk':'hpk','ilves':'ilves','jokerit':'jokerit',
    'jukurit':'jukurit','jyp':'jyp','kalpa':'kalpa','kiekkoespoo':'kiekko-espoo',
    'kespoo':'kiekko-espoo','kookoo':'kookoo','karpat':'karpat','lukko':'lukko',
    'pelicans':'pelicans','saipa':'saipa','sport':'sport','vaasansport':'sport',
    'tappara':'tappara','tps':'tps','assat':'assat'
}

def team_id(name):
    if isinstance(name,dict):
        name=next((name.get(k) for k in ('name','displayName','shortName','teamName','slug') if name.get(k)), '')
    name=unicodedata.normalize('NFKD',str(name or '')).casefold()
    name=''.join(ch for ch in name if not unicodedata.combining(ch))
    name=re.sub('[^a-z0-9]','',name)
    return TEAM_ID_BY_NAME.get(name)

def _date_game(value):
    if isinstance(value,(int,float)) and value>1e9:
        return datetime.fromtimestamp(value/1000 if value>1e11 else value,timezone.utc).isoformat()
    if isinstance(value,str):
        try:
            d=datetime.fromisoformat(value.strip().replace('Z','+00:00'))
            if d.tzinfo is None: d=d.replace(tzinfo=timezone.utc)
            return d.isoformat()
        except ValueError:return None
    return None

def _game_team(obj,side):
    # Liiga API keys may be homeTeam/awayTeam or home/away; accept both.
    variants=(side+'Team',side+'TeamName',side+'Name',side)
    for k in variants:
        if obj.get(k):
            v=obj[k]
            if isinstance(v,dict):
                return (v.get('teamName') or v.get('name') or v.get('displayName')
                        or v.get('shortName') or v.get('slug') or '')
            return str(v)
    return ''

def normalize_games(body):
    if isinstance(body,list): rows=body
    elif isinstance(body,dict):
        rows=next((body[k] for k in ('games','schedule','matches','items','data') if isinstance(body.get(k),list)),[])
        if not rows:
            # Some schedule responses wrap weeks; unfold only known collections.
            weeks=next((body[k] for k in ('weeks','gameWeeks') if isinstance(body.get(k),list)),[])
            rows=[g for w in weeks if isinstance(w,dict) for g in (w.get('games') or []) if isinstance(g,dict)]
    else: rows=[]
    result=[]; seen=set()
    for raw in rows:
        if not isinstance(raw,dict):continue
        home=_game_team(raw,'home');away=_game_team(raw,'away')
        hid=team_id(home);aid=team_id(away)
        if not hid or not aid: continue
        dt=next((_date_game(raw.get(k)) for k in ('start','startTime','startDate','date','gameDate','scheduledStart') if _date_game(raw.get(k))),None)
        if not dt:continue
        # Keep regular season only if the field is supplied.
        series=str(raw.get('serie') or raw.get('series') or raw.get('tournament') or '').casefold()
        if series and not ('runkosarja' in series or series in ('1','regular','regularseason')):
            continue
        key=(hid,aid,dt)
        if key in seen:continue
        seen.add(key)
        venue=raw.get('iceRink') or raw.get('rink') or raw.get('arena') or ''
        if isinstance(venue,dict):venue=venue.get('name') or venue.get('city') or ''
        result.append({'home':TEAMS[hid],'away':TEAMS[aid],'date':dt,'venue':str(venue),
                       'home_id':hid,'away_id':aid})
    return sorted(result,key=lambda x:x['date'])

def _fetch_games():
    url='https://liiga.fi/api/v2/games?' + urlencode({'season':2027,'tournament':'runkosarja'})
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 (Liiga365 schedule)',
                             'Accept':'application/json','Referer':'https://liiga.fi/'})
    with urlopen(req,timeout=12) as response:
        if urlparse(response.geturl()).hostname not in ('liiga.fi','www.liiga.fi'):
            raise ValueError('Unexpected schedule host')
        data=response.read(5_000_001)
        if len(data)>5_000_000:raise ValueError('Schedule too large')
    games=normalize_games(json.loads(data.decode('utf-8-sig')))
    if not games:raise ValueError('Official schedule response contained no recognized games')
    return games

def _refresh_games():
    try:
        games=_fetch_games()
        with GAMES_LOCK:
            GAMES_CACHE.update(games=games,at=time.time(),updated=datetime.now(timezone.utc).isoformat(),error=None)
    except Exception as exc:
        with GAMES_LOCK:GAMES_CACHE.update(at=time.time(),error=f'{type(exc).__name__}: {str(exc)[:180]}')
    finally:
        with GAMES_LOCK:GAMES_CACHE['refreshing']=False

def matches_for(team):
    if team not in TEAMS:return {'status':'error','games':[],'error':'Unknown team'}
    with GAMES_LOCK:
        if time.time()-GAMES_CACHE['at']>GAMES_TTL and not GAMES_CACHE['refreshing']:
            GAMES_CACHE['refreshing']=True
            threading.Thread(target=_refresh_games,daemon=True).start()
        rows=list(GAMES_CACHE['games']); refreshing=GAMES_CACHE['refreshing']; error=GAMES_CACHE['error']; updated=GAMES_CACHE['updated']
    now=time.time()-3*3600
    matches=[g for g in rows if (g['home_id']==team or g['away_id']==team)
             and datetime.fromisoformat(g['date']).timestamp()>=now]
    matches=matches[:3]
    return {'team':team,'games':matches,'status':'ok' if matches else ('loading' if refreshing else 'empty'),
            'refreshing':refreshing,'updated':updated,'error':error,
            'source':'Liiga.fi API (2026–2027 runkosarja)'}

# One shared publisher index supplements the shared Liiga.fi index.
# Club-specific filtering is applied after collection, not at download time.
_previous_team_news=team_news
def team_news(team):
    if team not in TEAMS:return {'status':'error','articles':[],'error':'Unknown team'}
    if team=='kalpa':return _previous_team_news(team)
    base=_previous_team_news(team)
    extra,busy,sources,error=publisher_news()
    combined={a['url']:a for a in base.get('articles',[])+extra
              if a.get('url') and team_article_match(team,a)}
    articles=sorted(combined.values(),key=lambda a:a.get('timestamp') or 0,reverse=True)
    base['articles']=articles[:100]
    base['refreshing']=bool(base.get('refreshing') or busy)
    base['partial']=base['refreshing']
    base['status']='ok' if articles else ('loading' if base['refreshing'] else 'empty')
    base['sources'].update(sources)
    if error:base.setdefault('errors',[]).append('Julkaisijalähteet: '+error)
    base['coverage']='Liiga.fi, SuomiKiekko, Yle.fi, MTV Uutiset, Kiekkouutiset'
    return base

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
        elif path == '/api/matches':
            team=parse_qs(urlparse(self.path).query).get('team',['kalpa'])[0].lower()
            if team not in TEAMS:
                self.send_error(400,'Unknown team');return
            payload=json.dumps(matches_for(team),ensure_ascii=False).encode('utf-8')
            mime='application/json; charset=utf-8'
        elif path == '/api/teams':
            payload = json.dumps({'teams':[{'id':k,'name':v} for k,v in TEAMS.items()]},ensure_ascii=False).encode('utf-8')
            mime = 'application/json; charset=utf-8'
        elif path == '/api/news':
            team=parse_qs(urlparse(self.path).query).get('team',['kalpa'])[0].lower()
            if team not in TEAMS:
                self.send_error(400, 'Unknown team'); return
            payload = json.dumps(team_news(team), ensure_ascii=False).encode('utf-8')
            mime = 'application/json; charset=utf-8'
        elif path == '/api/sources':
            data = news()
            payload = json.dumps({'sources':data.get('sources',{}),
                                  'article_counts':{
                                      source:sum(a.get('source')==source for a in data.get('articles',[]))
                                      for source in data.get('sources',{})}},
                                 ensure_ascii=False).encode('utf-8')
            mime = 'application/json; charset=utf-8'
        elif path == '/api/article':
            params=parse_qs(urlparse(self.path).query)
            try:
                result=article_for(params.get('url',[''])[0])
            except Exception:
                result={'status':'summary','paragraphs':[], 'message':'Artikkelin hakeminen ei onnistunut.'}
            payload=json.dumps(result,ensure_ascii=False).encode('utf-8')
            mime='application/json; charset=utf-8'
        elif path == '/kalpa-logo.svg':
            # Local image always works with the existing restrictive CSP.
            payload = (ROOT / 'kalpa-logo.svg').read_bytes()
            mime = 'image/svg+xml; charset=utf-8'
        elif path == '/kalpa-logo.png' and (ROOT / 'kalpa-logo.png').is_file():
            payload = (ROOT / 'kalpa-logo.png').read_bytes()
            mime = 'image/png'
        elif path.startswith('/logos/') and path.rsplit('/', 1)[-1] in TEAM_LOGO_FILES:
            payload = (ROOT / 'logos' / path.rsplit('/', 1)[-1]).read_bytes()
            mime = 'image/jpeg'
        elif path == '/ottelut.json':
            payload = (ROOT / 'ottelut.json').read_bytes()
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

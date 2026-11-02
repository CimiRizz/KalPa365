"""KalPa365 v6.15: paikallinen Jatkoajan uusimpien vastausten kerääjä.
Asenna: pip install playwright beautifulsoup4 && python -m playwright install chromium
Aseta KALPA365_URL ja KALPA_FORUM_TOKEN ympäristömuuttujat, käynnistä skripti.
"""
import os, time, re, json, calendar, datetime, urllib.request
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

FEED='https://keskustelu.jatkoaika.com/forums/kalpa.161/index.rss'
BASE=os.environ.get('KALPA365_URL','').rstrip('/')
TOKEN=os.environ.get('KALPA_FORUM_TOKEN','')
INTERVAL=max(120,int(os.environ.get('KALPA_INTERVAL_SECONDS','300')))
if not BASE.startswith('https://') or not TOKEN:
    raise SystemExit('Aseta KALPA365_URL (https://...) ja KALPA_FORUM_TOKEN.')

def parse_message_time(article):
    """Prefer a complete machine-readable date; never int('08.45')."""
    for tag in article.select('time'):
        for attr in ('data-time', 'data-timestamp', 'datetime', 'title'):
            raw = (tag.get(attr) or '').strip()
            if not raw:
                continue
            if re.fullmatch(r'\d{10}(?:\.\d+)?', raw):
                return int(float(raw))
            if re.fullmatch(r'\d{13}', raw):
                return int(raw) // 1000
            # XenForo's visible local times, e.g. 08.45, are NOT Unix seconds.
            try:
                dt = datetime.datetime.fromisoformat(raw.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
                if dt.year >= 2020:
                    return int(dt.timestamp())
            except ValueError:
                pass
            try:
                dt = parsedate_to_datetime(raw)
                if dt.year >= 2020:
                    return int(dt.timestamp())
            except (ValueError, TypeError, IndexError):
                pass
    return 0

def get_posts(page):
    response=page.goto(FEED,wait_until='domcontentloaded',timeout=30000)
    if not response or not response.ok: raise RuntimeError('RSS-haku estetty')
    root=ET.fromstring(response.body())
    threads=[]
    for item in root.findall('./channel/item')[:10]:
        url=(item.findtext('link') or '').strip()
        title=(item.findtext('title') or '').strip()
        if url.startswith('https://keskustelu.jatkoaika.com/threads/'):
            threads.append((title,url))
    results=[]
    for title,url in threads:
        try:
            # /latest navigates to the end of a XenForo thread; avoids scraping all pages.
            page.goto(url.rstrip('/')+'/latest',wait_until='domcontentloaded',timeout=25000)
            html=page.content(); soup=BeautifulSoup(html,'html.parser')
            for article in soup.select('article.message--post, article.message'):
                body=article.select_one('.message-body .bbWrapper, .message-content .bbWrapper')
                if not body: continue
                for quote in body.select('blockquote, .bbCodeBlock, .js-expandWatch'):quote.decompose()
                content=body.get_text(' ',strip=True)[:3000]
                ts=parse_message_time(article)
                link=article.select_one('a[href*="/posts/"], a[href*="/post-"]')
                post_id=(article.get('id') or '').removeprefix('js-post-').removeprefix('post-')
                link_url=urljoin(page.url,link.get('href','')) if link else (urljoin(page.url,'/posts/'+post_id+'/') if post_id.isdigit() else url.rstrip('/')+'/latest')
                if ts>0 and content and link_url.startswith('https://keskustelu.jatkoaika.com/'):
                    results.append(dict(topic=title,content=content,timestamp=ts,url=link_url))
        except Exception as exc:
            print('Ketju ei auennut:',url,str(exc)[:150],flush=True)
    if not results:
        print('Viestejä ei löytynyt kelvollisilla päiväyksillä: tarkista keskustelusivun aika-attribuutit.',flush=True)
    # Duplicate post IDs should never be shown twice.
    unique={r['url']:r for r in results}
    return sorted(unique.values(),key=lambda r:r['timestamp'],reverse=True)[:3]

def upload(items):
    data=json.dumps({'messages':items},ensure_ascii=False).encode('utf-8')
    req=urllib.request.Request(BASE+'/api/forum-posts',data=data,method='POST',headers={
        'X-Kalpa-Token':TOKEN,'Content-Type':'application/json; charset=utf-8'})
    with urllib.request.urlopen(req,timeout=20) as resp:
        if resp.status!=200: raise RuntimeError('Lähetys ei onnistunut')

with sync_playwright() as playwright:
    # Pysyvä selaintila: voit kirjautua tai hyväksyä evästeet kerran, tarvittaessa.
    context=playwright.chromium.launch_persistent_context('kalpa365_browser_profile',headless=False)
    page=context.new_page()
    print('KalPa365 keskusteluhaku käynnissä. Sulje komentokehote lopettaaksesi.',flush=True)
    try:
        while True:
            try:
                items=get_posts(page)
                if items:
                    upload(items)
                    print('Päivitetty viestejä:',len(items),datetime.datetime.now().strftime('%H:%M:%S'),flush=True)
                else: print('Yksittäisiä viestejä ei löydetty; vanhaa sisältöä ei korvattu.',flush=True)
            except Exception as exc:print('Haku/lähetys epäonnistui:',str(exc)[:350],flush=True)
            time.sleep(INTERVAL)
    finally:context.close()

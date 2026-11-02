"""KalPa365 v6.13: paikallinen Jatkoajan uusimpien vastausten kerääjä.
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

def get_posts(page):
    page.goto(FEED,wait_until='domcontentloaded',timeout=30000)
    raw=page.locator('body').inner_text()
    # Browser may render RSS as raw XML or as an XML tree.
    response=page.request.get(FEED,timeout=20000)
    if not response.ok: raise RuntimeError('RSS HTTP '+str(response.status))
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
                time_tag=article.select_one('time[data-time]')
                ts=int(time_tag.get('data-time','0')) if time_tag else 0
                link=article.select_one('a[href*="/post-"], a[href*="/posts/"]')
                link_url=urljoin(page.url,link.get('href','')) if link else page.url
                if ts>0 and content and link_url.startswith('https://keskustelu.jatkoaika.com/'):
                    results.append(dict(topic=title,content=content,timestamp=ts,url=link_url))
        except Exception as exc:
            print('Ketju ei auennut:',url,str(exc)[:150],flush=True)
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

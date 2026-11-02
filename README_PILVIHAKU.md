# KalPa365 v6.18 – Render Cron -pilvihaku (TESTI)

**Tämä ei takaa Jatkoajan hakua:** Jatkoaika on aiemmin palauttanut Renderin IP-osoitteille HTTP 403. Cron käyttää Renderin verkkoa, joten eston jatkuminen on todennäköistä. Älä sammuta toimivaa Windows-hakijaa ennen onnistunutta testiä.

## Testi Renderissä

1. Lisää GitHubin KalPa365-repositorioon `KalPa365_render_keskusteluhaku.py`. Muita olemassa olevia tiedostoja ei tarvitse vaihtaa.
2. Render Dashboard → New → Cron Job. Valitse sama GitHub-repo ja haara.
3. Build Command: `bash render-build.sh`
4. Command: `python KalPa365_render_keskusteluhaku.py`
5. Schedule: `*/5 * * * *` (UTC, viiden minuutin välein).
6. Environment: `KALPA365_URL=https://kalpa365.onrender.com`, `KALPA_FORUM_TOKEN` = sama arvo kuin verkkopalvelussa; `PLAYWRIGHT_BROWSERS_PATH=0` myös build/run-ympäristössä, jos selaimen löytämisessä ongelmia.
7. Valitse Renderissä soveltuva maksullinen Cron-plan ja tarkista kustannus ENNEN luomista (vähintään $1/kk per Cron Job, plus käytön mukainen laskutus).
8. Käynnistä Cron Job → Runs → Trigger Run. Tarkista lokit.

Onnistunut tuloste: `Render pilvihaku: lähetetty 3 viestiä`. Sen jälkeen tarkista /api/forum-posts: `storage_status=persistent` ja päivitetty `updated_at`.

Jos näkyy `RSS-haku estetty`, `403` tai viestejä ei löydy, Renderin IP-estettä ei ole ratkaistu. Poista Cron Job kustannusten välttämiseksi ja jatka Windows-hakijalla tai sovitulla, sallitulla erillisellä lähteellä.

**Huom:** Cron Job ei tarvitse PostgreSQL:n salasanaa: se toimittaa viestit olemassa olevaan rajapintaan tunnisteella. Älä lähetä tunnistetta tai tietokannan salasanaa keskusteluun. Vaihda aiemmin paljastuneet tunnisteet.

Käyttöliittymää (index.html) ei ole muutettu.

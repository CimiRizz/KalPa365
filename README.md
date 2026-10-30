# KalPa365 v2.4 – Liiga.fi-uutishaku

Korjaa vain Liiga.fi-uutisten löytämistä. Builder.io-artikkelilukija ja muut lähteet pysyvät ennallaan.

- Hakee Liigan julkisesta /api/v2/news-rajapinnasta enintään 20 × 16 = 320 artikkelia (aiemmin 80).
- Tutkii artikkelin koko searchText-kentän (aiemmin vain 350 ensimmäistä merkkiä), otsikon ja mahdolliset joukkuetunnisteet.
- Pitää 30 päivän julkaisuaikarajauksen ja päällekkäisten artikkelien poiston.
- Diagnostiikka: /api/news → sources → Liiga.fi → pages; `scanned`, `within_30_days`, `matches`.
- Haku voidaan rajata ympäristömuuttujalla KALPA365_LIIGA_PAGES (1–30, oletus 20).

## Asennus

Pura ZIP ja korvaa GitHubin KalPa365-repositorion vastaavat viisi tiedostoa. Render julkaisee uuden version.

## Huomio

Paikalliset testit käyttävät simuloituja API-vastauksia. Julkisen Liiga-rajapinnan todellinen tulos pitää tarkistaa Renderissä.

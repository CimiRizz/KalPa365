# Liiga365 v0.6 – virallisten seurasivujen uutiskorjaukset

Perustuu Liiga365 v0.5:een. Branch: `feature/liiga365`. KalPa365 `main` ja lukittu käyttöliittymä pysyvät koskemattomina.

## Korjaukset

- **Jokerit**: virallinen lähde vaihdettu `jokerit.com` → `jokerit.fi`; `https://www.jokerit.fi/uutiset`, Squarespace-uutis-RSS ja suomenkielisten pitkien julkaisupäivien varatunnistus.
- **Jukurit**: `/fi-fi/cg/uutiset/1/` sekä suomenkielinen etusivu; WiseNetwork-artikkeleiden julkaisuajan tunnistus otsikon vierestä.
- **Kiekko-Espoo**: vanha `kiekko-espoo.com` → virallinen liigajoukkueen `kiekko-espoo.fi/uutiset-ja-tarinat/`; lisäksi WordPressin julkinen read-only REST API -varahaku ja RSS-yritykset.
- **SaiPa**: `/fi-fi/cg/uutiset/1/`, `/fi-fi/`; WiseNetwork-julkaisuajan varatunnistus.
- **TPS**: useampi uutiskategorian reitti, `/fi-fi/` ja WiseNetwork-julkaisuajan varatunnistus.
- Näkyvämpi lähdekohtainen diagnostiikka: `article_checks`, `accepted`, `candidate_links`.
- Muiden joukkueiden lähteet, nopea uutishaku, ottelut, lukutila ja UI ennallaan.

## Asennus

GitHubissa valitse **feature/liiga365**, korvaa **vain KalPa365_palvelin.py** ja julkaise erilliseen Liiga365-Render-palveluun. Älä korvaa KalPa365-mainia.

Testaa `/api/news?team=jokerit`, `jukurit`, `kiekko-espoo`, `saipa`, `tps`. Ensimmäinen vastaus voi sisältää `refreshing: true`, jolloin lähdekohtainen haku on vielä käynnissä; päivitä tai odota sivun automaattista päivitystä. `sources`-kohdasta näet `count`, `pages` ja uudet diagnostiikkakentät.

## Varmennus

29/29 yksikkötestiä läpäisty ja Python-syntaksi tarkistettu. Sivustojen live-vastauksia Renderistä ei ole varmennettu. WordPress-rajapinta voi olla suljettu eikä ole varmaa, että se palauttaa artikkelit; silloinkin perinteinen HTML/RSS-haku jatkuu.

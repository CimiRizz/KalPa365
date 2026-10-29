# KalPa365 1.4 — suorat lähteet ja diagnostiikka

Lähteet: IS, IL, Jatkoaika ja Savon Sanomat. Ei Google Newsia.

## Mitä korjattiin
- `/api/news` näyttää jokaisesta lähteestä `scanned` (RSS:n kaikki artikkelit), `publisher_links` (hyväksytyt artikkelilinkit) ja `count` (KalPa-osumat).
- Löytyneet KalPa-uutiset säilyvät SQLite-historiassa 30 päivää viimeisestä esiintymisestä syötteessä.
- HEAD-terveystarkistus palauttaa 200.
- Nykyinen Savon Sanomien RSS-syöte ja lukutila on säilytetty.

## Tärkeät rajoitukset
- IS:n ja IL:n tuoreimmat-RSS:t voivat sisältää 0 KalPa-uutista. Tämä versio ei väitä korjaavansa lähteiden kattavuutta.
- Jatkoajan HTTP 403 ei ratkea ilman toimivaa, sallittua syötettä tai käyttöoikeutta.
- Renderin ilmaisinstanssin paikallinen SQLite-tietokanta **ei säily luotettavasti uudelleenkäynnistyksissä tai julkaisuissa**. Pysyvään historiaan tarvitaan ulkoinen tietokanta.
- Artikkelien kokotekstit eivät ole taattuja. Maksumuureja tai pääsynrajoituksia ei kierretä.

## Päivitys
Vie paketin viisi tiedostoa GitHubin KalPa365-repositorion juureen, korvaa vanhat ja odota Renderin Live-tilaa. Start Command: `python KalPa365_palvelin.py`. Tarkista `https://kalpa365.onrender.com/api/news`.

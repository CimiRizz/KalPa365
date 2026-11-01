# KalPa365 v3.6 — Yle-uutiset mukaan

Pohjautuu v3.5-versioon: musta yläpalkki, KalPan logo, ottelukortit ja joukkueiden tunnukset säilyvät.

## Muutos

`KalPa365_palvelin.py` hakee nyt Yle.fi-lähteestä neljää Ylen virallista RSS-syötettä:
- `https://yle.fi/rss/urheilu`
- `https://yle.fi/rss/t/18-141764/fi` (Pohjois-Savo)
- `https://yle.fi/rss/uutiset/tuoreimmat`
- `https://yle.fi/rss/tuoreimmat`

Vain KalPaan liittyvät artikkelit otetaan mukaan nykyisellä suodattimella. Sama artikkeli poistetaan kaksoiskappaleena URL-osoitteen perusteella. Jos yksi syöte ei vastaa, muut toimivat edelleen. Yle.fi näkyy uutislähdevalikossa, kun syötteistä löytyy KalPa-aiheisia artikkeleita.

## Julkaisu

Päivitä GitHubissa vain `KalPa365_palvelin.py` (halutessasi myös `index.html`, jossa versionumero v3.6). Renderin automaattinen deploy käynnistyy GitHub-päivityksestä, jos se on otettu käyttöön. Muut tiedostot ovat mukana täyden paketin vuoksi.

## Tarkistukset

Python-koodi on syntaksitarkistettu ja syöteparseri testattu paikallisella esimerkkisyötteellä. Ulkoista Render-palvelua tai Ylen RSS-verkkohaun toimintaa tässä ympäristössä ei ole testattu.

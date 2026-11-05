# Liiga365 v0.5 – Pelicans, Tappara ja TPS -uutiskorjaukset

Tämä on Liiga365:n `feature/liiga365`-branchille tarkoitettu kehitysversio, joka perustuu toimivaan v0.4-koodiin.

## Korjaukset

- Pelicansin virallinen uutislista: `https://pelicans.fi/fi-fi/cg/uutinen/1/` ja `https://pelicans.fi/fi-fi/`.
- Tapparan virallinen uutislista: `https://www.tappara.fi/fi-fi/cg/uutiset/1/` ja `https://www.tappara.fi/fi-fi/`.
- TPS:n virallinen uutislista: `https://hc.tps.fi/fi-fi/cg/uutiset/1/` ja `https://hc.tps.fi/fi-fi/`.
- WiseNetwork-sivujen artikkelilinkit (`/fi-fi/article/...`) asetetaan etusijalle, jotta navigaatio- ja mainoslinkit eivät kuluta tarkistusmäärää.
- Artikkelin julkaisupäivä löydetään myös artikkelin otsikon välittömästä läheisyydestä, jos koneellisesti luettava päiväys puuttuu.
- Muut 14 joukkuetta, yhteiset uutislähteet ja aiemmin hyväksytty käyttöliittymä ennallaan.

## Asennus

1. Avaa GitHub-repositorion branch `feature/liiga365`.
2. Korvaa **vain** `KalPa365_palvelin.py` tällä tiedostolla.
3. Render julkaisee uuden branch-version, jos automaattinen julkaisu on päällä; muutoin tee Manual Deploy.
4. Avaa Liiga365 ja vaihda Pelicansiin, Tapparaan ja TPS:ään. Uudessa prosessissa seurakohtaiset välimuistit alkavat tyhjistä; anna hakukierroksen valmistua.
5. Tarkista `/api/news?team=pelicans`, `/api/news?team=tappara`, `/api/news?team=tps`. `sources`-osiossa näkyvät lähdekohtaiset `pages`/`candidates` ja uutisten määrät.

## Testattu

`python -m unittest discover -s tests -v` → 23 testiä hyväksytty.
`python -m py_compile KalPa365_palvelin.py` → hyväksytty.

Huomio: ulkoisten sivujen saatavuutta Renderin verkosta ei voida taata paikallisilla yksikkötesteillä; varmistus tehdään julkaistulla testipalvelulla.

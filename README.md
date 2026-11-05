# Liiga365 v0.2 – feature/liiga365

**Älä asenna tähän pakettiin kuuluvia tiedostoja `main`-branchiin.**

## Käyttöönotto
1. Luo tai valitse `feature/liiga365` GitHubissa.
2. Siirrä tämän paketin `KalPa365_palvelin.py` ja `index.html` vain siihen branchiin.
3. Säilytä alkuperäiset staattiset tiedostot, logot, `requirements.txt`, `render-build.sh` ja `render.yaml`.
4. Käynnistä `python KalPa365_palvelin.py` ja avaa `http://localhost:8766`.
5. Jos julkaiset Renderiin, luo **erillinen** palvelu, jonka GitHub Branch on `feature/liiga365`. Älä muuta nykyisen KalPa365-palvelun branchia.

## Uutta
- 17 Liiga-joukkueen valinta ja selaimessa säilyvä valinta.
- Kauden 2026–2027 runkosarjan otteluhaku: `/api/matches?team=kalpa` ja vastaavasti muut joukkueet. Yhteinen 30 minuutin välimuisti, 3 seuraavaa ottelua.
- Uutiset: yhteinen Liiga.fi-uutisvirta, lisäksi muiden kuin KalPan osalta joukkuekohtainen julkinen Google News RSS (ei omaa maksullista API-avainta). 10 minuutin välimuisti.
- KalPan alkuperäinen v6.25 uutishaku säilyy.
- Haun aikana näkyvät ensimmäiset saatavilla olevat tulokset, ilman kaikkien lähteiden odotusta.
- Virheet raportoidaan; uutisia/otteluita ei keksitä.

## Rajoitteet
- Liigan julkinen API voi muuttaa vastausrakennetta tai estää Renderin. Testaa `/api/matches?team=...` julkaisuympäristössä. API:n tuloksille ei keksitä korvaavia otteluita.
- Google News RSS voi estää pilvipalvelimelta tulevat haut. Silloin Liiga.fi toimii ainoana yhteisenä uutislähteenä kyseiselle joukkueelle.
- Kaikkien 17 seuran omia verkkosivustoja ei ole vielä liitetty erillisinä lukijoina. Tämä versio laajentaa uutiskattavuutta kaikille joukkueille yhteisen lähteen ja joukkuekohtaisen RSS-haun kautta, mutta ei takaa kaikkien seurojen uutisten täydellistä kattavuutta.
- Projektin lähdekoodissa ei ole mukana alkuperäisiä logoja tai muita resursseja; ne säilytetään nykyisestä branchista.
- Kolmannen osapuolen rajapinnan käyttöehdot ja kuormitusrajat on tarkistettava ennen laajaa julkaisua.

## Testit
`python -m unittest discover -s tests -v`

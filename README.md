# KalPa365 v6.14 – keskusteluviestien näyttö

- RSS-tuontipainike ja siihen liittyvä ohjeteksti poistettu.
- Keskustelulinkki ohjaa uusimpaan viestiin (ketjun `/latest`-reitti), tai yksittäisen viestin pysyvään osoitteeseen jos hakija löytää sen.
- Kolmen uusimman löydetyn yksittäisen viestin sisältö näytetään, jos Windows-hakija on toiminnassa ja on lähettänyt viestit Renderiin.
- Jos viestien sisältöä ei ole saatavilla, näytetään rehellinen ilmoitus, ei pelkkiä RSS-otsikoita.

## Käyttöönotto
1. Korvaa GitHubissa `index.html` ja `KalPa365_palvelin.py`; Render julkaisee muutoksen.
2. Render Environment: aseta `KALPA_FORUM_TOKEN` pitkäksi satunnaiseksi salaisuudeksi.
3. Windows: `pip install playwright beautifulsoup4` ja `python -m playwright install chromium`.
4. Aseta `KALPA365_URL` Render-sivuston osoitteeksi ja `KALPA_FORUM_TOKEN` samaksi kuin Renderissä.
5. Käynnistä `ALOITA_AUTOMAATTINEN_HAKU.bat` samasta kansiosta.
6. Tarkista `https://OMA-RENDER/api/forum-posts`: jos `messages` on tyhjä, paikallinen hakija ei ole vielä onnistunut.

Huom: Hakija on kokeellinen; pääsy Jatkoajan sivuille riippuu sen asettamista rajoituksista. Renderin muisti tyhjenee palvelun uudelleenkäynnistyessä, jolloin viestit odottavat seuraavaa lähetystä. Käyttäjän Windows-koneen on oltava päällä automaattista hakua varten.

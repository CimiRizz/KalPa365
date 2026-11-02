# KalPa365 v6.13 – automaattinen kolmen uusimman viestin haku

**Tämä versio on testattava kokeilu, ei vahvistetusti toimiva Jatkoajan viestihaku.** RSS sisältää ketjujen päivitysajat mutta ei uusimpia vastauksia. Siksi Windowsissa ajettava Playwright-selain hakee 10 viimeksi päivitetyn ketjun viimeiseltä sivulta viestit, järjestää saatavilla olevat vastaukset aikaleiman mukaan ja lähettää kolme uusinta Renderiin. Tämä ei takaa koko foorumin kolmea absoluuttisesti uusinta viestiä, jos RSS jättää olennaisia ketjuja pois. Jatkoaika voi estää myös paikallisen selainhaun.

## Asennus
1. Päivitä Render-projektin `index.html` ja `KalPa365_palvelin.py` GitHubissa. Säilytä muut nykyiset tiedostot.
2. Lisää Renderin Environment-asetuksiin `KALPA_FORUM_TOKEN`, jonka arvoksi asetat itse valitsemasi **pitkän satunnaisen salaisuuden**. Älä julkaise sitä GitHubissa.
3. Windowsissa asenna `pip install playwright beautifulsoup4` ja `python -m playwright install chromium`.
4. Aseta omassa Windows-komentorivissä `set KALPA365_URL=https://OMA-PALVELU.onrender.com` ja `set KALPA_FORUM_TOKEN=SAMASALAISUUS`.
5. Suorita samassa ikkunassa `python KalPa365_automaattinen_keskusteluhaku.py` (tai `ALOITA_AUTOMAATTINEN_HAKU.bat`). Pidä ikkuna ja kone käynnissä.
6. Katso KalPa365-sivua: yksittäisten viestien sisältö näkyy, jos paikallinen haku ja lähetys onnistuvat. Päivitysväli on 5 minuuttia.

**Rajoitukset:** Renderin ilmaisinstanssin muisti nollautuu uudelleenkäynnistyksessä, joten viestit katoavat, kunnes Windows-hakija lähettää ne uudelleen. Hakija vaatii käynnissä olevan Windows-koneen. Jatkoajan käyttöehdot ja mahdolliset pääsyn rajoitukset tulee huomioida; automaatti ei ratkaise pääsyestoa itsestään. Jos lähetys ei onnistu, tuttu v6.12 RSS-tiedoston tuonti toimii ennallaan. Kirjoittajan nimeä ei näytetä.

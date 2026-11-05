# Liiga365 v0.7 – välitön uutisnäyttö ja virallinen lähde ensin

Tämä paketti on tarkoitettu vain GitHubin `feature/liiga365`-haaraan. KalPa365:n `main`-haaraan ei tehdä muutoksia.

## Muutokset

- Selaimen `localStorage` säilyttää **kunkin joukkueen kolme viimeksi näytettyä uutista** (otsikko, lähde, linkki, julkaisuajankohta ja mahdollinen tiivistelmä). Ne näytetään heti sivua avattaessa tai joukkuetta vaihdettaessa; tämä ei vaadi verkkoyhteyttä näyttövaiheessa.
- Aiemmin tallennetut uutiset pysyvät näkyvissä, kunnes uusia on saatu; tyhjä tai epäonnistunut haku ei tyhjennä niitä.
- Muille kuin KalPalle `/api/news?team=...` palauttaa ensin oman virallisen verkkosivun löydökset (`phase: official`). Vasta virallisen sivun haun valmistuttua alkaa yhteisten Liiga.fi- ja muiden medioiden haku (`phase: media`). Lopuksi `phase: complete`.
- Uutisia päivitetään edelleen ajantasaisuusjärjestyksessä; lähteen prioriteetti määrää hakujärjestyksen, ei sitä, mitkä ovat lopulta kolme uusinta.
- Uutishaku jatkuu 2,5 sekunnin kyselyvälillä haun ollessa käynnissä.
- KalPan vanha haku säilyy: se ei ole vielä jaettu virallinen/muut mediat -vaiheisiin.
- Visuaalinen ulkoasu ja asettelu eivät muutu.

## Asennus

Korvaa `feature/liiga365`-haarassa **kaksi tiedostoa**, `KalPa365_palvelin.py` ja `index.html`. Uusi toiminnallisuus tarvitsee sekä palvelimen vaiheistuksen että selaimen välimuistin. Renderin Start Command säilyy `python KalPa365_palvelin.py`.

Selaimen localStorage on selain- ja laitekohtainen, eikä säily incognito-istunnon päättyessä tai käyttäjän tyhjentäessä sivuston tallennustiedot. Palvelimen uudelleenkäynnistys ei tyhjennä selaimeen tallennettuja kolmea otsikkoa.

## Testit

`python -m unittest discover -s tests -q`

Tarkistukset suoritettiin 32/32 hyväksytysti ja JavaScript-tiedoston syntaksi tarkistettiin Node.js:n `--check`-komennolla. Tuotantoympäristön lähteitä ei testattu tässä suoritusympäristössä.

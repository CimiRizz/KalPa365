# Liiga365 v0.3 – feature/liiga365

**Asenna vain `feature/liiga365`-branchiin. KalPa365:n `main`-branchia ei muuteta.**

## Korjaukset versioon v0.2

- Poistettu Google Uutiset -RSS kokonaan uutisvirrasta. Google News -välityslinkit eivät olleet suoria julkaisijan artikkelilinkkejä, eivätkä toimineet KalPa365:n artikkelilukijassa.
- Muut 16 joukkuetta: sama julkaisijavalikoima kuin KalPa365:ssä ilman KalPa.fi:tä: **Liiga.fi, SuomiKiekko, Yle.fi, MTV Uutiset, Kiekkouutiset**.
- Julkaisijat haetaan yhteisellä haulla. Joukkuekohtainen suodatus tehdään vasta uutisten löytämisen jälkeen, ei KalPa-nimellä lähdettä luettaessa.
- `/api/article` ei enää vaadi, että muiden joukkueiden artikkelit löytyvät KalPa-kohtaisesta uutislistasta. Artikkelilukija rajoittuu edelleen tunnettuihin sallittuihin julkaisijoihin.
- Säilytetty KalPan erillinen toimivaksi rakennettu uutishaku ja otteluohjelman haku.
- `index.html` on sama kuin v0.2:ssa: hyväksyttyyn korttiasetteluun, joukkuevalintaan tai väreihin ei tehty muutoksia.

## Asennus

1. Avaa GitHub-repositorio ja vaihda branchiksi `feature/liiga365`.
2. Korvaa **vain `KalPa365_palvelin.py`** tämän paketin tiedostolla.
3. Renderin testipalvelu ottaa muutoksen käyttöön uuden julkaisun jälkeen.
4. Avaa selaimessa Liiga365 ja paina `Ctrl+F5`.

## Testaus

- `python -m unittest discover -s tests -v`
- Renderissä tarkista `/api/news?team=tappara`, `/api/news?team=ilves` ja `/api/news?team=kalpa`.
- Artikkeleissa `source` on alkuperäinen julkaisija eikä `Google Uutiset`.
- Klikkaa uutiskorttia: `/api/article?url=...` hakee julkaisijan artikkelin tekstin, kun se on julkisesti haettavissa. Jos teksti ei ole saatavilla, näytetään tiivistelmä tai linkki alkuperäiseen artikkeliin.

## Rajoitteet

Julkaisijat voivat estää palvelimelta haun, vaihtaa sivurakennetta tai tarjota artikkeleita ilman luettavissa olevaa kokotekstiä. Tuloksia ei ole vielä testattu Renderissä. Puuttuvia uutisia, päivämääriä tai tekstiä ei keksitä. Pelkkä RSS-julkaisu ei välttämättä kata jokaista joukkueuutista. Nykyisen KalPa365:n alkuperäinen lukija ei kaikissa tapauksissa pysty tuomaan maksullista tai asiakaspohjaista sisältöä.

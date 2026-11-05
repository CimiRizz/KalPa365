# Liiga365 v0.4 – viralliset joukkuesivustot

**Vain branchiin `feature/liiga365`.** Älä muuta KalPa365:n `main`-branchia.

## Muutokset
- Kaikkien 17 joukkueen viralliset uutislähteet lisätty annettujen verkkotunnusten perusteella.
- KalPa säilyttää aiemman KalPa.fi-hakunsa, mukaan lukien kausiuutislista.
- Muut joukkueet: oma virallinen uutisvirta + Liiga.fi, SuomiKiekko, Yle.fi, MTV Uutiset ja Kiekkouutiset.
- Virallisten sivujen RSS-osoitteet kokeillaan vain, jos ne ovat julkisesti saatavilla. Lisäksi haetaan etusivun ja uutislistasivun artikkelilinkit.
- Kaikille artikkeleille vaaditaan lähteen itsensä ilmoittama julkaisupäivä. Linkki hyväksytään vain joukkueen omalta verkkotunnukselta.
- Jokaisella joukkueella on oma 15 minuutin välimuisti. Lähteet käynnistyvät vasta joukkueen valinnalla.
- Artikkelilukija hyväksyy nyt myös näiden virallisten sivujen artikkeliosoitteet.
- Uutishaun lähdekohtainen tila näkyy `/api/news?team=<joukkue>` -vastauksen `sources`-kentässä.
- `index.html` säilyy täysin samana kuin v0.3:ssa. Ulkoasua ei ole muutettu.

## Asennus
1. Siirry GitHubissa `feature/liiga365`-branchiin.
2. Korvaa vain `KalPa365_palvelin.py` tässä ZIPissä olevalla uudella tiedostolla.
3. Julkaise oma Liiga365-testipalvelu Renderissä.
4. Testaa esimerkiksi `/api/news?team=jyp`, `/api/news?team=ilves`, `/api/news?team=kalpa`.
5. Ensimmäinen kysely voi palauttaa `refreshing: true`; päivitä rajapintakyselyä, kunnes haku valmistuu.

## Testit
Paikallisesti `python -m unittest discover -s tests -v`: **18/18 OK**. Lisäksi Python-tiedoston syntaksi tarkistettu. Näitä ei ole testattu käyttäjän Render-palvelussa.

## Huomioitavat rajoitteet
Jokainen seura käyttää omanlaistaan sivurakennetta. Osa voi olla JavaScriptillä toteutettu, eikä artikkelilistoja tai julkaisupäiviä voi välttämättä lukea ilman sivustokohtaista hakijaa. RSS-osoitteita ei ole vahvistettu kaikille seuroille. Virhelähteet eivät keskeytä muiden uutisten hakua. Virallisen sivun teksti ei aina ole luettavissa julkisesti lukutilaan. Ei oleteta julkaisuajaksi nykyhetkeä eikä näytetä tekaistuja uutisia. Uutisten tuotantokattavuus edellyttää erillistä seura- ja lähdekohtaista testausta Renderissä.

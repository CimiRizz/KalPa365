# KalPa365 v5.1 – julkaisupäivien tunnistus

Pohjana v5.0. Korjaa tilanteen, jossa artikkelin julkaisupäivä näkyy alkuperäisellä sivulla mutta KalPa365 ei sitä tunnista.

- Hakee päivämäärättömien uutisten alkuperäisen HTML-sivun.
- Lukee ensisijaisesti JSON-LD:n `datePublished`-kentän, sen jälkeen julkaisuajan meta-tiedot ja `<time datetime>` -arvot.
- Ei käytä `dateModified`-kenttää julkaisupäivänä eikä keksi puuttuvaa päivää.
- Päivittää myös tietokantahistoriasta löytyvien päivämäärättömien uutisten näyttötiedot.
- Säilyttää 30 päivän rajauksen, maksuttomuustarkistuksen ja kaksoiskappaleiden poiston.
- Rajoittaa sivulataukset 120 uuteen ja 120 vanhaan päivämäärättömään ehdokkaaseen per päivitys ja välimuistittaa tulokset 6 tunniksi.

Rajoitus: jos julkaisija näyttää päivämäärän vain JavaScriptillä tai epästandardissa muodossa, artikkeli voidaan edelleen jättää pois.

**Julkaisu:** korvaa GitHubissa vain `KalPa365_palvelin.py`. Renderin toimivuutta ei ole testattu.


## v5.2
Google News -haku poistettu kokonaan. Uutiset haetaan vain alkuperäisten julkaisijoiden RSS-syötteistä, suorilta sivuilta ja Liigan rajapinnasta. Vanhoja Google News -linkkejä ei näytetä historiasta.

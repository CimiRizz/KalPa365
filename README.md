# KalPa365 v6.24 – KalPa.fi:n tuoreiden uutisten korjaus

Pohjana v6.23. KalPa365:n hyväksytty ulkoasu ja vaiheittainen uutishaku säilyvät.

## Korjaukset

1. KalPa.fi:n uutisia haetaan nyt myös suoraan kauden 2026–2027 uutislistalta: https://kalpa.fi/fi-fi/cg/2026-2027/60/ . Tämä on ensisijainen hakusivu; KalPan etusivu säilyy toisena lähteenä.
2. Korjattu uutishaun loppuvaiheessa oleva vanhan `outcomes`-muuttujan viittaus. Se saattoi keskeyttää uutishaun ennen lopullista tulosjoukkoa.
3. Nykyinen päivämäärän tarkistus, uusimpien uutisten järjestäminen ja välimuistista vaiheittain päivittyminen säilyvät.

## Asennus

Korvaa GitHubissa **vain `KalPa365_palvelin.py`**, odota Render-julkaisua ja paina KalPa365:n **Päivitä**-painiketta. Tarkista sitten `/api/news`: `sources` → `KalPa.fi` → `direct_pages` → `pages`. Kauden uutislistan pitäisi näkyä siinä omana tarkistettuna sivunaan. Uusien artikkelien pitää näkyä, jos julkaisija tarjoaa ne sivun HTML:ssä ja julkaisuajat löytyvät artikkelista.

## Testit ja rajoitteet

- Python-syntaksi tarkistettu.
- HTML-testillä tarkistettu, että kauden uutissivun artikkelilinkit tunnistuvat ja muut linkit hylätään.
- GitHub- ja Render-ympäristöissä toimintaa ei ole testattu. KalPa.fi:n live-HTML:ää ei voitu lukea tästä suoritusympäristöstä; sivun nykyiset uutiset vahvistettiin julkisista hakutuloksista.
- Ei muutoksia `index.html`-tiedostoon eikä ulkoasun lukittuihin asetuksiin.

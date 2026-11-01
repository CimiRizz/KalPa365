# KalPa365 v3.8 – joukkueiden logot näkyviin

Kaikkien 17 joukkueen JPG-logot on upotettu suoraan `index.html`-tiedostoon data-URI-kuvina. Selain ei enää pyydä erillisiä `/logos/*.jpg`-osoitteita, joten logot näkyvät myös silloin, kun `logos`-kansio ei ole päätynyt julkaisuun tai palvelimen reititys ei ole päivittynyt. Nykyinen CSP sallii `img-src data:`.

## Asennus

1. Päivitä vähintään `index.html` GitHubiin.
2. Varmista Renderissä uusi julkaisu ja päivitä sivu Ctrl+F5.
3. Säilytä halutessasi muutkin paketin tiedostot; Yle-uutiset, musta yläpalkki ja ottelut säilyvät.

Tarkistus: jokainen 17 upotetusta JPG-kuvasta on luettu lähdetiedostosta. HTML:n JavaScriptin syntaksitarkistus tehty Node.js:llä, mikäli käytettävissä.

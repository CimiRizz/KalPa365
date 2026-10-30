# KalPa365 v2.7 — Liiga.fi:n uutisten tarkka diagnostiikka

Korvaa GitHub-projektin viisi tiedostoa tämän ZIP-paketin tiedostoilla.

## Mikä muuttui?

Liiga.fi:n onnistuneiden hakujen yhteydessä `/api/news` → `sources` → `Liiga.fi` → `pages` → `rejected_samples` näyttää kunkin 30 päivän sisällä hylätyn uutisen:

- `title`: uutisen otsikko
- `reason`: miksi hylättiin
- `lead`: johdannon tai tekstin alku
- `kalpa_in_title` ja `kalpa_in_body`: esiintyykö KalPa
- `mention_context`: katkelma ensimmäisen KalPa-maininnan ympäriltä
- `structured_fields`: mahdolliset erilliset joukkuetunnisteet

**Tämä on diagnostiikkaversio:** se ei hyväksy uutista pelkän tekstimaininnan vuoksi. Tarkoitus on tunnistaa väärin hylätyt artikkelit ennen suodattimen muuttamista. Näin vältetään aiemman v2.4:n epäolennaisten uutisten tulva.

Builder.io-lukutila ja muiden lähteiden toiminta ovat ennallaan.

Kun julkaisu on valmis, avaa `https://kalpa365.onrender.com/api/news` ja kopioi `sources` → `Liiga.fi` → `pages` → `rejected_samples` tänne analysoitavaksi.

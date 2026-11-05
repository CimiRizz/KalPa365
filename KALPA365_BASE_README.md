# KalPa365 v6.25 – KalPa.fi:n tuoreiden uutisten päivämääräkorjaus

## Mikä meni vikaan?
KalPa.fi:n artikkelit saatettiin tunnistaa, mutta poistettiin uutislistalta, koska HTML-päivämäärän varatunnistin etsi päivämäärää vain otsikon alapuolelta. KalPan sivupohjissa se voi sijaita ennen H1-otsikkoa.

## Korjaus
- Etsii julkaisupäivän ensisijaisesti alkuperäisen artikkelin koneellisesta metadatasta ja vaihtoehtoisesti otsikon välittömästä läheisyydestä myös sen yläpuolelta.
- Tarkistaa lisäksi KalPan etusivun `?lang=fi-FI`-version ja kauden 2026–2027 uutislistan.
- Ei käytä hakuhetkeä artikkelin julkaisuaikana eikä tuo vanhoja uutisia uusina.
- Muut uutislähteet, nopea vaiheittainen haku ja `index.html` säilyvät ennallaan.

## Asennus
Korvaa GitHub-repositoriossa **vain `KalPa365_palvelin.py`** ja odota Render-julkaisua. Päivitä uutishaku ja tarkista `/api/news` → `sources` → `KalPa.fi` → `direct_pages` sekä `articles`.

## Testaus ja rajaus
Pythonin syntaksi ja paikalliset HTML-esimerkit testattu. KalPa.fi:n todellinen live-HTML ja Render-päivitys tulee vielä tarkistaa julkaisun jälkeen; tämän ympäristön suorat verkkopyynnöt KalPa.fi-palveluun eivät onnistu.

# KalPa365 v6.22 – vaiheittainen uutishaku, koodisiivous

## Asennus
Korvaa GitHubissa `KalPa365_palvelin.py` ja `index.html` tästä paketista. Säilytä nykyiset `ottelut.json`, logot, `render.yaml`, `render-build.sh` ja muut julkaisuasetukset ennallaan. GitHubiin ei tarvitse lisätä ZIP-pakettia.

## Muutokset
- `/api/news` vastaa heti. Jos uutiset löytyvät paikallisesta historian välimuistista, ne tulevat näkyviin välittömästi; ellei välimuistia ole, sivu näyttää lataustilan.
- Uutislähteet haetaan rinnakkain, ja ensimmäiset päivätyt, tarkistetut uutiset julkaistaan vaiheittain. Selain tarkistaa tilanteen 2,5 sekunnin välein aktiivisen haun aikana.
- Haun lopuksi suoritetaan olemassa oleva päivämäärien, otsikoiden, kaksoiskappaleiden ja julkisesti luettavien linkkien tarkistus.
- Jatkoajan keskustelun kerääjä, viestien tallennusrajapinnat ja niiden PostgreSQL-riippuvuus poistettu palvelinkoodista. Muutokset eivät poista olemassa olevaa Render-tietokantaa automaattisesti.
- Käyttöliittymän HTML-rakenne ja CSS jätetty ennalleen (lukittu ulkoasu).

## Rajapintatarkistus
`/api/news` palauttaa `refreshing: true` kesken haun ja `partial: true`, kun näkyvissä on vaiheittainen tulos. Lopuksi `refreshing: false`, `partial: false`. `updated` kertoo snapshotin päivitysajan, ei välttämättä uusimman uutisen julkaisuaikaa.

## Huomio
Renderin ilmaisessa ympäristössä tiedostopohjainen uutishistoria ei ole pysyvä uudelleenkäynnistysten yli. Tällöin ensimmäiset uutiset tulevat näkyviin vasta ensimmäisten onnistuneiden lähdehakujen jälkeen. PostgreSQL:n aiempia keskusteluviestejä ei enää käytetä.

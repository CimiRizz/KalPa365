# KalPa365 v4.2 – päällekkäisten uutisten poisto

Korjaus tehdään palvelimessa myös vanhaan 30 päivän uutishistoriaan. Samat otsikot, URL:n eri versiot ja erittäin samankaltaiset otsikot yhdistetään. Eri uutisia samasta pelistä ei poisteta pelkän joukkueen tai aiheen perusteella.

Uutiset säilyvät uusimmasta vanhimpaan. Musta yläpalkki, logot, ottelut ja kaikki v4.1:n uutislähteet säilyvät.

**Asennus:** Korvaa GitHubissa `KalPa365_palvelin.py` tämän paketin versiolla. Odota Renderin julkaisua, päivitä sivu Ctrl+F5. Uutishistoriaa ei tarvitse tyhjentää.

Tarkistukset: Pythonin syntaksi, deduplikoinnin yksikkötestit ja ZIP-tiedoston eheys. Renderin live-toimintaa ei ole vahvistettu.

## v4.3 Artikkelien lukeminen
Uutiskortissa on nyt erillinen **Avaa alkuperäinen** -linkki. Google News -hakutuloksista artikkelin sisältöä ei yleensä voi hakea oman lukutilan kautta, koska linkki on news.google.com-osoitteessa ja palvelin hyväksyy vain alkuperäiset julkaisijat. Google News -linkki avautuu selaimessa, jossa Google ohjaa artikkelin julkaisijalle. Lukutila säilyy suorille lähteille. Maksumuuria ei kierretä.

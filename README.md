# KalPa365 v5.4 — KalPa.fi:n oikeat uutisotsikot

- KalPa.fi:n kuvien alt-tekstejä ei enää käsitellä uutisotsikkoina.
- KalPa.fi:n artikkelin oikea otsikko luetaan artikkelisivun h1-/JSON-LD-/og:title-kentistä, ensisijaisesti h1:stä.
- Korjaus päivittää myös vanhaan paikalliseen uutishistoriaan tallentuneet virheelliset otsikot näytettäessä.
- Jos artikkelista ei löydy kelvollista otsikkoa ja listan otsikko on "Kuva ...", uutista ei näytetä väärällä otsikolla.
- 30 päivän rajaus, muut suodatukset, Google Newsin poisto, muut uutislähteet, lukutila, pelit ja logot säilyvät.

Asennus: vaihda GitHubissa vain KalPa365_palvelin.py ja odota Renderin automaattinen julkaisu.

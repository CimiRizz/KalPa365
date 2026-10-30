# KalPa365 v1.5

Viisi uutislähdettä: IS, IL, Jatkoaika, Savon Sanomat ja Liiga.fi.

Liiga.fi luetaan julkiselta uutislistaussivulta HTML-linkkien perusteella. Koska sivusto on JavaScript-pohjainen, lähde voi näyttää `empty` eikä uutisten löytymistä voi taata. Lähteen diagnostiikka näkyy `/api/news`-vastauksen `sources["Liiga.fi"]`-kohdassa.

IS:n 100 luettua uutista ilman KalPa-osumia, IL:n 0 luettua uutista ja Jatkoajan HTTP 403 ovat erillisiä ratkaisemattomia lähdeongelmia. Savon Sanomien RSS säilyy ennallaan.

## Päivitys
Lataa ZIP-tiedoston viisi tiedostoa olemassa olevaan KalPa365-GitHub-projektiin. Render start command: `python KalPa365_palvelin.py`.

Renderin ilmaisversion paikallinen SQLite-historia voi kadota uudelleenkäynnistyksessä.

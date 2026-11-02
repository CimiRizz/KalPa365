# KalPa365 v6.17 — keskusteluviestien pysyvä tallennus

Korjaus: kolmen uusimman keskusteluviestin tiedot tallennetaan Render PostgreSQL -tietokantaan. Niitä ei enää säilytetä pelkästään Pythonin muistissa. Päivityksen jälkeen /api/forum-posts lukee tiedot tietokannasta myös Renderin uudelleenkäynnistyksen jälkeen.

## TÄRKEÄÄ: Ota tietokanta käyttöön Renderissä

1. Render Dashboard → **New** → **Postgres**. Luo uusi PostgreSQL-tietokanta, valitse KalPa365:n kanssa sama region ja varmista hinnoittelu Renderin näkymästä ennen hyväksymistä.
2. Avaa tietokannan **Connections** / **Info** -osio ja kopioi **Internal Database URL**. Renderin sisäinen URL toimii samassa regionissa olevalta Render-palvelulta. Älä jaa URL:ia julkisesti.
3. Render Dashboard → KalPa365 (Web Service) → **Environment** → lisää muuttuja `DATABASE_URL`, arvoksi tietokannan Internal Database URL. Säilytä myös nykyinen `KALPA_FORUM_TOKEN` muuttumattomana.
4. Vie ZIP-paketin `KalPa365_palvelin.py` ja `requirements.txt` GitHubin KalPa365-repositorioon. Tallenna muutokset ja julkaise Renderin uusi versio. `index.html` on identtinen v6.16:n kanssa eikä sen ulkoasua muutettu.
5. Avaa `https://kalpa365.onrender.com/api/forum-posts`. Ennen ensimmäistä lähetystä tuloksena on `messages: []` ja `storage_status: "empty"`. Jos `storage_status: "database_not_configured"`, `DATABASE_URL` ei ole asetettu. Jos 503, katso Renderin lokista tietokantavirhe.
6. Käynnistä jo käytössä oleva Windows-hakija, joka lähettää viestit 5 minuutin välein. Älä luo uutta tokenia: käytä Renderin nykyistä `KALPA_FORUM_TOKEN`-arvoa. Onnistunut lähetys tallentaa viestit tietokantaan, `storage_status: "persistent"` vahvistaa asian.
7. Uudelleenkäynnistä Render-palvelu ja tarkista API uudelleen: tallennettujen kolmen viestin tulee näkyä edelleen.

## Rajaukset
- PostgreSQL-tietokanta pitää luoda: ZIP ei voi itsenäisesti ottaa pilvitietokantaa käyttöön. Ilman DATABASE_URL-asetusta lähettäjä saa 503-virheen (ei harhaanjohtavaa 'Päivitetty'-kuittausta).
- Viestit eivät päivity, jos Windows-hakija on suljettu; palvelin säilyttää viimeksi lähetetyt viestit.
- Renderin mahdollisen maksuttoman Postgres-kannan elinkaarirajoitukset on tarkistettava Renderistä. Valitse säilyvyyteen sopiva tietokantapalvelu ja varmuuskopiointi.
- Ulkoasu, asemoinnit ja `index.html` pysyvät ennallaan.
- Koska aiempi token on näkynyt keskustelussa, se tulee vaihtaa sekä Renderissä että Windowsissa turvallisesti.

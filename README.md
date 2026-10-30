KalPa365 2.1 — Liiga.fi:n uutisdatan poiminta

Korvaa GitHubissa KalPa365_palvelin.py. Muut tiedostot pysyvät samoina.

Uusi poiminta:
- Liigan uutisluettelo ja etusivu
- julkiset HTML-artikkelilinkit
- sivuun upotettu JSON (application/json ja JSON-LD)
- diagnostiset html_links, json_records, json_scripts, bytes /api/news → sources → Liiga.fi → pages

HUOM. Tämä on kokeellinen poiminta: Liigan julkisen sivun todellista HTML-vastausta
Render-ympäristössä ei ole vielä tarkistettu. Nolla tulosta voi tarkoittaa,
että uutiset tulevat erillisestä verkkopyynnöstä. Tässä versiossa ei arvata API-osoitetta.

Jos edelleen 0: selaimen F12 → Network → Fetch/XHR → päivitä Liigan uutiset -sivu
ja kopioi uutislistan palauttavan pyynnön URL ja vastausrakenteen esimerkki.
Älä lähetä evästeitä tai kirjautumistunnuksia.

KalPa365 2.0 — suorien uutislähteiden haku

Sisältö:
- RSS: IS, IL, Savon Sanomat, Yle. Kaikki määritellyt RSS-syötteet luetaan.
- Jatkoaika: julkisen KalPa-joukkuesivun artikkelilinkit, jos sivu sallii palvelinpyynnöt.
- Liiga.fi: julkisen uutisluettelon artikkelilinkit, jos ne sisältyvät HTML-vastaukseen.
- Kokotekstin lukutila ja SQLite-historia ennallaan.
- /api/news → sources sisältää lähdekohtaisen tilan ja sivudiagnostiikan.

Rajoitukset: Jatkoajan HTTP 403 -estoa ei kierretä. Liiga.fi:n JS:llä ladattuja artikkeleita ei välttämättä löydy. IS/IL:n RSS:ssä voi edelleen olla 0 KalPa-osumaa. Lähdekohtaisten julkisten sivujen toteutus on kokeellinen, ei tuotannossa vahvistettu.

Asennus: Korvaa GitHubissa neljä tiedostoa ja tee commit. Render Start Command: python KalPa365_palvelin.py

# KalPa365 v6.11 — Jatkoajan KalPa-keskustelujen RSS-kokeilu

- Vaihda GitHubissa vain `KalPa365_palvelin.py` ja `index.html`. Muut tiedostot voi säilyttää nykyisinä.
- `/api/forum` lukee `https://keskustelu.jatkoaika.com/forums/kalpa.161/index.rss`.
- Näyttää kolme viimeksi päivittynyttä KESKUSTELUKETJUA — RSS:n sisältökenttä on ketjun aloitusviesti eikä viimeisin viesti.
- Toimivaa XML-rakennetta testattu käyttäjän toimittamalla RSS-tiedostolla. Renderin suoraa RSS-pääsyä ei ole vahvistettu.
- Jos Render saa 403-virheen myös RSS-osoitteesta, pääsivu näyttää selkeän linkin keskustelupalstalle eikä yritä kiertää estoa.
- Muut uutislähteet ja käyttäjäliittymän järjestys säilyvät.

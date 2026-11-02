# KalPa365 v6.7 — Jatkoaika ja UrheiluSuomi

Korvaa GitHubissa vain `KalPa365_palvelin.py`. `index.html` pidetään ennallaan.

- UrheiluSuomi poistettu lähteistä, tarkistuksista ja historiasta.
- Jatkoaika: vanha, 403-virheen palauttanut RSS-osoite korvattu Liigan RSS-ehdokkaalla ja virallisiin julkisiin joukkue-/hakusivuihin lisätty hakupolut.
- Jos Jatkoaika estää Render-palvelimen pyynnöt edelleen (HTTP 403), uutisia ei pystytä hakemaan ja tilanne näkyy `/api/sources`-diagnostiikassa.
- Muut lähteet, MTV, KalPa365 v6.2:n käyttöliittymä, maksuttomuus- ja 30 päivän rajaukset sekä Google Newsin poisto säilyvät.

Huom: Jatkoajan uusien hakureittien toimivuutta Renderistä ei ole voitu testata.

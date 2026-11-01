KalPa365 v5.7 — MTV Uutiset (yksi uusi lähde)

Muutokset verrattuna toimivaan v5.6-versioon:
- MTV Uutisten vanha 404-virheen palauttava RSS-osoite korvattu julkaisijan omalla syötteellä: https://www.mtvuutiset.fi/api/feed/rss/uutiset_uusimmat
- Lisätty MTV:n oma urheilusivu: https://www.mtvuutiset.fi/tuoreimmat/urheilu
- Vain /artikkeli/<otsake>/<numero>-muotoisia MTV:n artikkeleita poimitaan suoralta sivulta.
- KalPa-aiheisuus, alkuperäinen julkaisuajankohta (30 päivää), maksuttomuus ja luettavuus tarkistetaan ennallaan.
- Muut v5.6-lähteet ja käyttöliittymä ennallaan. Ei Google Newsia.

Asennus: korvaa GitHubissa vain KalPa365_palvelin.py. Render-julkaisun jälkeen tarkista /api/sources -> MTV Uutiset.

Rajoitus: paikallisen työtilan internet-yhteys MTV:n palvelimille on estetty. MTV:n RSS-osoite on tarkistettu julkisesta RSS-hakemistosta, mutta varsinaisia artikkeleita ei ole voitu hakea paikallisesti. MTV:n urheiluetusivun rajaus ei välttämättä löydä kaikkia KalPa-uutisia, jos ne eivät ole tuoreimpien joukossa.

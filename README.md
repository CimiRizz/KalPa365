KalPa365 v6.5 — Pallomeri-hakukorjaus

Asennus: korvaa GitHubissa VAIN KalPa365_palvelin.py. Säilytä nykyinen index.html.

Lähettämäsi /api/sources osoitti, että Pallomeren RSS-osoitteet palauttivat
virheellistä XML:ää eikä Pallomeren suorilta sivuilta löydetty artikkeleita.

Uutta:
- Pallomeren julkaisijan oma WordPress-hakurajapinta kahdella osoitevaihtoehdolla
- Muutama julkaisijan oman sivuston tunnettu uutisosoite varmistuskeinona
  (eivät saa automaattista julkaisupäivää eivätkä ohita maksuttomuustarkistusta)
- /api/sources -> Pallomeri.net -> publisher_search näyttää onnistumiset,
  virheet, ehdokkaat ja artikkeleiden hylkäyssyyt.
- Kaikille Pallomeren uutisille edelleen 30 vrk, oikea päiväys, tekstin
  luettavuus ja KalPa-aiheisuus.
- Ei Google Newsia. Muiden lähteiden käsittelyyn ei tehty muutoksia.

Huom. Suoraa Render-testiyhteyttä tai live-verkkoyhteyttä ei käytetty tämän
ZIP-version validointiin. Jos Pallomeri edelleen 0, lähetä /api/sources-palvelun
Pallomeri.net-osio, erityisesti publisher_search.

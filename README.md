# KalPa365 v6.12 – RSS-tiedoston tuonti selaimessa

## Asennus
Vaihda GitHubissa **vain `index.html`**. Python-palvelin ja Renderin asetukset säilyvät.

## Käyttö
1. Avaa https://keskustelu.jatkoaika.com/forums/kalpa.161/index.rss omalla selaimellasi.
2. Lataa `index.rss` tietokoneelle tai puhelimeen.
3. KalPa365:ssä paina **Tuo RSS-tiedosto** kolmen uusimman uutisen alapuolelta.
4. Valitse lataamasi tiedosto. Kolme viimeksi päivittynyttä keskusteluketjua näkyy osiossa.

Tiedosto luetaan **vain käyttäjän selaimessa** ja kolme keskustelutietuetta tallennetaan selaimen `localStorage`-muistiin. Mitään ei lähetetä Renderille. Tiedot säilyvät sivun latausten välillä samalla selaimella ja laitteella, mutta eivät siirry automaattisesti toiselle laitteelle. Uusi RSS pitää tuoda käsin päivitystä varten.

RSS näyttää ketjut ja niiden päivitysajat, ei kolmea uusinta yksittäistä viestiä. Jatkoajan 403-esto ei vaikuta tähän tiedostotuontiin. Nykyiset uutistoiminnot eivät muutu.

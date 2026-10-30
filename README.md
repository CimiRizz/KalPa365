KalPa365 v2.8 — Liiga-ottelut mukaan\n\nKorjaus: hyväksyy KalPan ottelutapahtumat myös Liigan koosteartikkeleista. Ei hyväksy pelkkiä historiallisia listamainintoja. Muut uutislähteet ja Builder-lukutila ennallaan.\n\nAsennus: lataa ZIP, pura ja korvaa GitHubissa viisi tiedostoa. Render julkaisee päivityksen. Tarkista /api/news → sources → Liiga.fi → pages → matches.\n

## v2.9 — Ampparit / Liiga

Ampparit (https://www.ampparit.com/liiga) toimii täydentävänä uutisten löytölähteenä.
Ohjelma lukee julkisen sivun otsikkolinkkejä ja hyväksyy KalPa-nimen sisältävät
otsikot. Artikkelit avautuvat alkuperäisiltä julkaisijoilta; Ampparit ei ole
artikkelien julkaisija. Aiemmat uutislähteet, Liiga.fi ja lukutila säilyvät.

Tarkista `/api/news` -> `sources` -> `Ampparit / Liiga`: `status`, `count` ja
`message`. Jos sivusto estää automaattisen haun tai muuttaa HTML-rakennettaan,
lähde voi palauttaa 0 uutista, mutta muut lähteet jatkavat toimintaansa.
Ampparitista löytyvien otsikoiden aikaleima on hakuaika, koska julkaisuaikaa ei
ole luotettavasti saatavissa otsikkolinkeistä. Tämä on väliaikainen rajoitus.
Käytä lähdettä sivuston käyttöehtojen mukaisesti.

# KalPa365 v4.6 – uusia maksuttomia lähteitä

Pohjana toimivaksi todettu v4.5. Lisätty:
- KalPa.fi: seuran julkisen etusivun artikkelilinkit. KalPa.fi:n omat otteluraportit ja ennakot hyväksytään KalPa-aiheisiksi ilman otsikon KalPa-sanaa.
- UrheiluSuomi: jääkiekkosivun KalPa-aiheiset artikkelilinkit.
- Molemmat lisätty sallittuihin HTTPS-julkaisijoihin, jotta julkisen kokotekstin tarkistus ja lukutila voivat toimia.

Maksuttomuus tarkistetaan edelleen v4.5:n tiukalla sisällön tarkistuksella: pelkkä linkki ei riitä. Jos sivusto muuttaa HTML-rakennettaan tai estää hakemisen, kyseisen lähteen artikkelit jäävät pois, eivätkä muut lähteet lakkaa toimimasta. Ulkoisten sivujen käytännön toimivuutta Renderissä ei ole vahvistettu.

Ylen aiempi uutishaku säilyy. Erillisiä aggregaattoreita (Tolkkua/Uutiskynnys) ei lisätty lukutilan uutisjulkaisijoiksi, sillä niiden tiivistelmät eivät ole alkuperäisiä kokonaisia artikkeleita.

## Asennus
Päivitä GitHubissa vain `KalPa365_palvelin.py`; muut tiedostot säilyvät. Renderin julkaisun jälkeen tarkista `/api/sources` sekä uutislista.

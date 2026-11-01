# KalPa365 v4.5 – vain maksuttomat uutiset

Uutislistalle hyväksytään vain artikkelit, joiden julkisesti saatavilla oleva sisältö voidaan varmistaa palvelimelta. Google News -välityslinkit ja maksumuurin merkityt artikkelit jätetään pois. Jos sivu estää automaattisen lukemisen tai artikkelin maksuttomuutta ei voi vahvistaa, uutista **ei näytetä**. Tämä voi vähentää uutisten määrää merkittävästi.

Tarkistus kattaa enintään 100 uusinta ehdokasta, suoritetaan enintään 10 rinnakkaisella pyynnöllä ja tulos tallennetaan tunniksi välimuistiin. Maksumuuritunnistus perustuu sivun ilmoittamiin tietoihin ja saatavilla olevaan sisältöön: se ei ole täydellinen eikä kierrä maksumuureja.

Asennus: korvaa GitHubissa `KalPa365_palvelin.py`; `index.html` voidaan säilyttää ennallaan. Renderin uudelleenjulkaisun jälkeen tarkista `/api/news`.

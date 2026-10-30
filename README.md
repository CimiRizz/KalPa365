# KalPa365 v2.5 — KalPa pääaiheena

Tämä versio korjaa Liiga.fi:n uutisvalinnan. Pelkkä KalPa-maininta koko artikkelin `searchText`-kentässä ei enää riitä. Mukaan hyväksytään KalPaan keskittyvät otsikot ja KalPa-aiheiset ingressit tai artikkelin aloituskappaleet. Yleiset Liiga-tiedotteet ja otteluohjelmakoosteet rajataan pois.

Muut uutislähteet, Builder.io-artikkelilukija ja 30 päivän uutishistoria säilyvät.

## Asennus
Korvaa GitHub-repositorion viisi tiedostoa tämän ZIP:n vastaavilla ja odota Renderin julkaisua. Testaa `/api/news`-osoitteessa Liiga.fi:n `count` ja uutisten otsikot.

## Testaus
Python-syntaksi ja kuusi paikallista relevanssitestiä läpäisty. Live-Render-testin tulos selviää vasta julkaisun jälkeen.

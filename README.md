KalPa365 v5.6 — SuomiKiekko-hakujen korjaus

- Google News ei ole käytössä.
- SuomiKiekon suoran haun rinnalle lisätty julkaisijan omat RSS-vaihtoehdot (jos julkaisija tarjoaa ne).
- SuomiKiekon etusivu mukana hakupaikoissa.
- Artikkelitekstin lisäpoiminta, jos sivulta puuttuu tyypillinen article/main-HTML-merkintä.
- /api/sources: SuomiKiekko -> direct_pages -> pages -> rejection_samples kertoo miksi haetut artikkelit hylätään.
- Vain aidosti alle 30 päivän ikäiset, KalPaa koskevat, julkisesti luettavat artikkelit hyväksytään.
- Muut lähteet, ottelut, logot ja käyttöliittymä säilytetty.

Asennus: vaihda GitHubissa KalPa365_palvelin.py, odota Render-julkaisua ja tarkista /api/sources.
Huom.: SuomiKiekon live-HTML:ää ei voitu suorittaa paikallisessa työtilassa verkkorajoituksen takia.

# KalPa365 v5.5 — SuomiKiekko

Pohjana v5.4. Vain SuomiKiekon suoraa uutishakua laajennettu.

- SuomiKiekon hakutulokset tarkistetaan alkuperäiseltä artikkelisivulta.
- Otsikko luetaan artikkelin otsikkokentästä, ei kuvan alt-tekstistä.
- KalPa-relevanssi tarkistetaan artikkelin varsinaisesta otsikosta/tekstistä.
- Julkaisupäivä poimitaan artikkelista; yli 30 päivän uutiset hylätään.
- Maksullinen, liian lyhyt tai lukukelvoton artikkeli hylätään.
- Google News ei ole käytössä.
- Muita lähteitä, ottelunäkymää eikä HTML-ulkoasua muutettu.

## Asennus
Korvaa GitHubissa vain `KalPa365_palvelin.py`, Render julkaisee sen.
Tarkista `/api/sources` -> `SuomiKiekko` -> `direct_pages`.

## Testaus
Koodi voidaan tarkistaa paikallisesti; live-julkaisijan ja Renderin toimintaa ei ole vahvistettu.

# KalPa365 v5.9 – suorituskyky

Pohjana v5.8. Vaihda GitHubissa vain `KalPa365_palvelin.py`.

- RSS-, sivu- ja Liiga-lähteet haetaan rinnakkain (enintään 8 lähdettä kerrallaan).
- 5 min tuore välimuisti; sen jälkeen enintään tunnin vanha lista näytetään heti ja päivitetään erillisessä palvelinsäikeessä.
- Kylmäkäynnistyksessä tai yli tunnin vanhoilla tiedoilla odotetaan haun valmistumista.
- Yksi päivitys kerrallaan (single flight).
- `/api/sources` kertoo `duration_ms`-ajat ja `/api/news` koko koostamisen `build_duration_ms`-ajan.
- Uutislähteitä, niiden säännöstöä, lukutilaa ja käyttöliittymää ei muutettu.

Huom. Artikkelikohtaiset tunnistevälimuistit olivat jo käytössä v5.8:ssa. Live-Render-nopeutta ei ole tässä todennettu.

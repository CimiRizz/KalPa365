KalPa365 v6.9.1 — Chromium-asennuksen korjaus

Käyttäjän /api/sources osoitti: Playwright on asennettu, mutta Chromium-binääri puuttuu Renderistä. Jatkoajan verkkoyhteyttä ei vielä testattu.

GitHub: lisää/korvaa KalPa365_palvelin.py, requirements.txt ja render-build.sh.
Render -> Settings -> Build Command: bash render-build.sh
Render -> Manual Deploy -> Clear build cache & deploy (tai deploy ja tarkista loki).

Lokissa täytyy näkyä "Chromium OK:". Jos kirjastoihin liittyvä virhe estää käynnistyksen, Renderin palvelinympäristö voi vaatia erillisen järjestelmäriippuvuuksien asennuksen tai Docker-kuvan. Älä oleta että Jatkoaika toimii ennen /api/sources -testiä.

Muut lähteet ja käyttöliittymä pysyvät v6.9 mukaisina. Ei CAPTCHA-kiertoa.

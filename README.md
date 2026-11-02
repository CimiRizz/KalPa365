KalPa365 v6.9 — Jatkoaika Chromium -kokeilu

Päivitys v6.8:sta. Nykyinen index.html ennallaan. Jatkoajan keskustelupalsta ei sisälly.

HUOM: Vain KalPa365_palvelin.py:n korvaaminen EI riitä, ellei Renderissä ole
Playwright + Chromium asennettu. Renderin Build Command esimerkiksi:

    pip install -r requirements.txt && python -m playwright install chromium

Jos järjestelmäkirjastot puuttuvat, Chromium voi vaatia yhteensopivan Render-
ympäristön tai erilliset käyttöjärjestelmäriippuvuudet. Paketti ei muuta
Renderin asetuksia automaattisesti.

Asetus JATKOAIKA_BROWSER=1 (oletus) yrittää Chromium-hakua. Kytke
pois JATKOAIKA_BROWSER=0, jos työympäristössä ei ole selainta.

/api/sources -> Jatkoaika näyttää status: ok / blocked / error /
dependency_missing ja http_status-arvon. Jos 403 toistuu myös selaimessa,
keräin ei yritä ohittaa estoa eikä näytä keksittyjä artikkeleita.

Säilyttää alkuperäiset 30 päivän ja maksuttomuussuodatukset,
muut uutislähteet ja kolmen uutisen käyttöliittymän.

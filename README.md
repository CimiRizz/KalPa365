KalPa365 v6.9.2 — Chromium mukana Render-julkaisussa

Edellisen raportin Jatkoaika-virhe: "Executable doesn't exist at /opt/render/.cache/ms-playwright/...". Vaikka build-vaiheessa näytettiin Chromium OK, selain saattoi päätyä rakennusvaiheen kotihakemiston välimuistiin, joka ei säily ajonaikaisessa palvelussa.

Tämä paketti käyttää PLAYWRIGHT_BROWSERS_PATH=0 sekä asennuksessa että palvelimessa. Chromium asennetaan Playwright-paketin sisälle, jolloin se kulkee palvelun julkaisuartifaktin mukana.

1. GitHub: korvaa KalPa365_palvelin.py ja render-build.sh. Varmista että requirements.txt on mukana.
2. Render Build Command: bash render-build.sh
3. Render: Clear build cache & deploy. Varmista lokista "Chromium bundled OK:".
4. Kun Render sanoo Live, avaa /api/sources ja tarkista Jatkoaika-status.

Jatkoaika voi edelleen vastata 403, jolloin tämä asennuskorjaus ei poista julkaisijan estoa. Muut lähteet ja index.html säilyvät ennallaan. Ei CAPTCHA-kiertoa.

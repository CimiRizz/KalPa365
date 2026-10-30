# KalPa365 v2.6 — Liiga.fi-uutisten tarkennettu suodatus

Korvaa GitHub-projektin viisi tiedostoa tämän paketin tiedostoilla.

- Hyväksyy KalPa-otsikon tai selvästi KalPaa käsittelevän uutisen aloitusvirkkeen.
- Hyväksyy yhden vastustajan ottelujutut, mutta hylkää yleiset Liiga-tiedotteet ja usean joukkueen koosteet.
- Ei hyväksy pelkkää KalPa-mainintaa pitkän artikkelin keskellä.
- `/api/news` → `sources` → `Liiga.fi` → `pages` näyttää hylkäysten syyt (`rejected`).
- Builder.io-lukutila ja muiden lähteiden haku ovat ennallaan.

Huom. Jos Liiga.fi ei julkaise KalPa-aiheisia uutisia tarkastelujaksolla, tulos voi edelleen olla nolla.

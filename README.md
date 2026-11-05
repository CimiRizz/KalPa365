# KalPa365 v6.20 – keskustelupalstaosio poistettu

Keskustelupalstan koko osio poistettu käyttöliittymästä: otsikot, viestit, linkit, RSS-tuonti sekä keskusteluviestien päivityspyynnöt.

Muu käyttöliittymä (yläpalkki, ottelut, uutiskortit, hakukenttä, päivityspainike, muut uutiset) säilyy alkuperäisen v6.17-version mukaisena. Osion poiston vuoksi sitä seuraava uutisalue siirtyy ylöspäin, mutta sen omaa asemointia tai tyylejä ei muutettu.

## Asennus

Korvaa GitHub-repositoriossa vain index.html tällä versiolla. Render julkaisee sen normaalisti. Päivitä selaimessa Ctrl+F5.

Paketin muut palvelintiedostot ovat v6.17:stä sellaisinaan, eikä niitä tarvitse vaihtaa tämän muutoksen vuoksi. Taustapalvelimen vanha /api/forum-posts -rajapinta voi olla olemassa taaksepäin yhteensopivuuden vuoksi, mutta käyttöliittymä ei käytä sitä. Windows-hakijan voi pysäyttää eikä sitä enää tarvita.

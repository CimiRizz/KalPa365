# KalPa365 — versio 1.0

Epävirallinen KalPa-uutisten koontipalvelu. Kerää Google Newsin julkisista RSS-hakusyötteistä KalPaa koskevat uutiset, näyttää julkaisijan ja ajankohdan sekä avaa alkuperäisen artikkelin. Ei ohita maksumuureja eikä kopioi kokotekstejä.

## Paikallinen käynnistys

Asenna Python 3.9+ ja aja:

```powershell
python KalPa365_palvelin.py
```

Avaa http://localhost:8766

## Render-julkaisu (erillinen Uutisvirrasta)

1. Luo **uusi GitHub-repositorio** `KalPa365` ja lisää tämän kansion viisi tiedostoa sen juureen.
2. Renderissä **New → Blueprint** ja valitse uusi `KalPa365`-repo. `render.yaml` määrittää ilmaisen Python Web Servicen.
3. Vahvista palvelun luonti. Render antaa uuden `onrender.com`-osoitteen; nimi `kalpa365` voi olla jo varattu.
4. Odota tilaa **Live** ja avaa Renderin näyttämä URL.

Älä muokkaa vanhaa `NewsPaper`-repositoriota tai Uutisvirran Render-palvelua.

## Huomioita

- Uutiset tulevat Google News RSS -haun kautta; yksittäisten julkaisijoiden näkyminen ja hakutulosten kattavuus eivät ole taattuja.
- RSS-haku voi ajoittain epäonnistua, jolloin sivulla näkyy virheilmoitus.
- Uutiset avautuvat alkuperäisillä sivuilla. Tämä versio ei sisällä kokotekstilukutilaa.
- Uutisia päivitetään palvelimella enintään viiden minuutin välein.
- Otteluohjelma on suunniteltu versioon 2.0.

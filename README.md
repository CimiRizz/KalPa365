# KalPa365 v6.10 – KalPa-keskustelujen kolme uusinta viestiä

Perustuu v6.9.2-versioon. Uusi erillinen `/api/forum`-rajapinta hakee KalPan Jatkoaika-keskustelupalstan kolmea tuoreinta luettavissa olevaa viestiä. Näyttöjärjestys: kolme ottelua, kolme uutista, kolme keskusteluviestiä, haku ja loput uutiset.

## Asennus

Korvaa GitHubissa `KalPa365_palvelin.py`, `index.html` ja `requirements.txt`. Säilytä nykyinen `render-build.sh` ja Build Command `bash render-build.sh`.

Keskusteluviestien haku ei kierrä mahdollista HTTP 403 -estoa. Jos palsta estää palvelimen, osio ilmoittaa ettei viestejä saatu; muita uutislähteitä ei rikota.

Uusi päätepiste: `/api/forum`. Tämä on oikeiden viestien, ei pelkkien otsikoiden, kokeilu. Ajonaikaista toimintaa Renderissä ei ole vahvistettu.

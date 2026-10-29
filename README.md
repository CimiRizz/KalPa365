# KalPa365 1.3 — suorat lähteet

Vain KalPa-uutiset: IS, IL, Jatkoaika ja Savon Sanomat. Ei Google Newsia.

Render Start Command: `python KalPa365_palvelin.py`.

HUOM: Jatkoajan ja Savon Sanomien RSS-osoitteet ovat kokeellisia ja niiden toimivuus on tarkistettava Renderin `/api/news`-vastauksen `sources`-kentästä. Syöte voi vastata mutta sisältää nolla KalPa-uutista. IS/IL-syötteissäkin voi olla vain vähän KalPa-uutisia, koska haetaan uusimpia julkaisuja.

Lukutila yrittää erottaa julkisesti saatavilla olevan artikkelitekstin. Se ei kierrä maksumuuria. Jos tekstiä ei saada, näytetään syötteen tiivistelmä tai otsikko.

Asennus: päivitä nämä tiedostot KalPa365:n GitHub-repositorion juureen ja odota Renderin automaattista julkaisua. Säilytä vanha commit palautusta varten.

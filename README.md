# Liiga365 v0.10 – nopeampi seuran uutishaku

Pohjautuu v0.9-versioon: selaimen uutisvälimuisti, oikeat latausilmoitukset, lukutilan Liiga365-nimi ja joukkuekohtainen uutishaku säilyvät.

## Uudet muutokset
- Seuran RSS-syötteet ja uutislistasivut haetaan rinnakkain (eivät enää peräkkäin).
- RSS:stä löydetyt päivätyt uutiset julkaistaan heti myös kesken virallisen haun.
- Jos syöte sisältää vähintään kolme päivättyä artikkelia, turhat yksittäisten artikkelisivujen pyynnöt ohitetaan.
- Muussa tapauksessa tarkistetaan ensin 12 artikkelia rinnakkain ja enintään toinen 12 artikkelin erä, jos kolmea uutista ei vielä löydy.
- Tilapäinen tyhjä lähdevastaus ei poista viimeksi onnistuneesti haettuja virallisia uutisia palvelinmuistista.
- Muiden medioiden haku käynnistyy edelleen virallisen seuran haun valmistuttua.

## Asennus
GitHub-branch: `feature/liiga365`. Korvaa ainoastaan `KalPa365_palvelin.py`. `index.html` on sama kuin v0.9:ssä. Renderin käynnistysasetuksia ei muuteta.

## Testaus
34 paikallista Python-testiä. Todellista Render-viivettä ei ole mitattu; seurakohtaisten sivustojen vastausajat voivat vaihdella. Nämä muutokset koskevat muiden joukkueiden virallista hakua; KalPan vanha kerääjä on ennallaan.

# KalPa365 v6.15 – keskusteluviestien ajan käsittelyn korjaus

Korjattu Windows-hakijan kaatuminen, kun Jatkoajan aikaleima on esimerkiksi `08.45` eikä Unix-aikaleima. Uusi hakija hyväksyy Unix-aikaleimat sekä kokonaiset ISO-/RFC-päiväykset ja ohittaa epäselvät kellonajat. Näin viesteille ei arvata virheellistä päivämäärää.

**Nopein päivitys:** Korvaa vain Windows-koneen `C:\Users\kimir\Desktop\GIT\KalPa365_automaattinen_keskusteluhaku.py` tällä versiolla. GitHubia tai Renderiä ei tarvitse päivittää tämän korjauksen vuoksi. Sulje vanha hakija ensin Ctrl+C:llä.

PowerShellissä (uusi ikkuna):
```powershell
cd 'C:\Users\kimir\Desktop\GIT'
$env:KALPA365_URL='https://kalpa365.onrender.com'
$env:KALPA_FORUM_TOKEN='UUSI_RENDERISSA_MÄÄRITETTY_SALAINEN_TUNNISTE'
py -u .\KalPa365_automaattinen_keskusteluhaku.py
```

Koska aiempi tunniste näkyi keskustelussa, vaihda se **sekä Renderissä että Windowsissa** uuteen satunnaiseen arvoon. Älä lähetä tunnistetta keskusteluun.

Huom: Viestien haku onnistuu vain, jos Jatkoaika näyttää koneella luettavissa olevat keskustelusivut ja päiväykset. Kolme uusinta viestiä tarkoittaa hakijan tarkistamista ketjuista löydettyjä kolmea uusinta päivättyä viestiä.

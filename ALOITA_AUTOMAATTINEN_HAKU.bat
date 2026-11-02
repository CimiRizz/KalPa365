@echo off
cd /d "%~dp0"
if "%KALPA365_URL%"=="" (
  echo Aseta ensin KALPA365_URL ja KALPA_FORUM_TOKEN taman ikkunan ymparistoon.
  echo Esimerkiksi: set KALPA365_URL=https://OMA-PALVELU.onrender.com
  pause
  exit /b 1
)
python KalPa365_automaattinen_keskusteluhaku.py
pause

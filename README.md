# KalPa365 v6.23 – uutistekstien siivous

Pohjana toimiva KalPa365 v6.22.

## Muutos
- Poistaa X/Twitterin, Instagramin, TikTokin ja vastaavien sosiaalisten upotusten HTML-lohkot ja upotusskriptit uutisten teksteistä ennen niiden näyttämistä.
- Siivoaa uutistiivistelmät, tavallisen HTML-artikkelilukutilan, JSON-LD-tekstin ja Liigan Builder.io-lukutekstin.
- Säilyttää uutisartikkelin varsinaiset tekstikappaleet ja linkin alkuperäiseen artikkeliin.
- Ei muuta uutishaun toimintatapaa eikä hyväksyttyä käyttöliittymän ulkoasua.

## Asennus
1. Ota talteen toimivan v6.22:n varmuuskopio.
2. Korvaa GitHubissa **vain** `KalPa365_palvelin.py` tällä versiolla.
3. Render julkaisee päivitetyn palvelimen. Käynnistä sivu uudelleen Ctrl+F5 tarvittaessa.

`index.html` on mukana vertailua varten, mutta sen sisältö on muuttumaton v6.22:een nähden.

## Testattu
- Python-syntaksi
- X/Twitterin HTML-upotuksen ja skriptin poisto
- Muiden tekstikappaleiden säilyminen

Julkaistun Render-ympäristön ajonaikaista testausta ei ole tehty.

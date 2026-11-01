# KalPa365 v4.9 – uutislähteiden löydettävyyden korjaus

**Miksi v4.8 ei tuonut uutisia:** Etusivun uusimmissa uutisissa ei välttämättä ole KalPaa käsitteleviä artikkeleita. Lisäksi sovellus varmisti maksuttomuuden vain 100 ensimmäisestä artikkeliehdokkaasta; suorilta sivuilta löydettyjen artikkelien aikaleima on 0, joten ne jäävät usein tarkistusrajan ulkopuolelle.

**Korjaukset:**
- SuomiKiekko: KalPa-aiheinen sivustohaku `/?s=KalPa` sekä uusimpien uutisten sivu.
- Kiekkouutiset: KalPa-aiheinen sivustohaku `/?s=KalPa` sekä Liiga-sivu.
- Maksuttomuustarkistuksen ehdokasraja nostettu 100:sta 500:aan.
- `/api/news`-vastauksen `sources`-tiedoissa `candidate_count`, `verified_free_count` ja `rejected_count`, jotta hylkäyksen syy voidaan rajata.
- Maksuttomuussuodatus, otsikkosuodatus, kaksoiskappaleiden poisto, Yle, KalPa ja Liiga säilyvät.

**Rajoitukset:** Sivustohakujen toimivuutta ja maksuttomuustarkistuksen hyväksymiä tuloksia ei voitu testata live-Renderissä. Sivustojen rakenteet ja estot voivat estää haun. 500 ehdokkaan tarkistus voi kasvattaa ensimmäisen haun kestoa. Varmista julkaisun jälkeen `/api/news`-osoitteen `sources`-diagnostiikasta uusien lähteiden luvut.

**Asennus:** Päivitä GitHubiin vain `KalPa365_palvelin.py`. Odota Render-julkaisua, ja tarvittaessa 5 minuutin välimuistin vanhenemista.

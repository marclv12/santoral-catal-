# Guia pas a pas: GitHub + Telegram

Aquesta guia està pensada per muntar **Bon Dia Catalunya íntegrament des del navegador**, sense Visual Studio, terminal ni servidor propi.

## Abans de començar

Necessites:

- un compte de GitHub;
- Telegram obert al mòbil o a l’ordinador;
- el fitxer ZIP del projecte descomprimit al teu ordinador;
- uns 10 minuts per fer la configuració inicial.

> **Important:** el token de Telegram és una contrasenya. No l’enganxis mai en cap fitxer del repositori, missatge públic o captura de pantalla. Només s’ha de guardar com a secret de GitHub.

---

# Part A. Crear el bot amb BotFather

## 1. Obre el BotFather oficial

A Telegram, busca exactament:

```text
@BotFather
```

Comprova que sigui el compte verificat de Telegram.

Prem **Start** o escriu:

```text
/start
```

## 2. Crea un bot nou

Escriu:

```text
/newbot
```

BotFather et demanarà dues coses.

### Nom visible

Pots posar:

```text
Bon Dia Catalunya
```

Aquest nom es pot repetir i el podràs canviar més endavant.

### Nom d’usuari

Ha de ser únic i acabar en `bot`. Exemples:

```text
BonDiaCatalunyaMarcBot
BonDiaCatalunyaDiariBot
ElMeuBonDiaCatBot
```

Telegram et dirà si el nom ja està ocupat.

## 3. Desa el token

Quan el bot s’hagi creat, BotFather mostrarà una cadena semblant a aquesta:

```text
1234567890:AAExempleDeTokenMoltLlarg
```

Copia-la temporalment en un lloc segur. Aquest valor serà el secret:

```text
TELEGRAM_BOT_TOKEN
```

No afegeixis cometes ni espais al principi o al final.

### Si el token queda exposat

Torna a BotFather i utilitza:

```text
/revoke
```

Selecciona el bot i genera un token nou. Després actualitza el secret a GitHub.

## 4. Personalitza la fitxa del bot — opcional

A BotFather pots utilitzar:

```text
/setdescription
```

Text suggerit:

```text
Cada matí, santoral català, refranyer, aliments de temporada i efemèrides dels Països Catalans, Espanya, Europa i el món.
```

També pots utilitzar:

```text
/setabouttext
```

Text suggerit:

```text
Santoral, terra, cultura i història cada matí.
```

De moment **no cal configurar ordres** amb `/setcommands`, perquè aquesta versió envia el missatge automàticament però encara no respon a `/avui`, `/dema` o altres comandes.

---

# Part B. Obtenir el teu `chat_id`

El `chat_id` diu al bot a quin xat ha d’enviar el missatge.

## 5. Obre el bot que acabes de crear

BotFather et mostrarà un enllaç semblant a:

```text
https://t.me/BonDiaCatalunyaMarcBot
```

Obre’l i prem **Start**. També pots enviar-li qualsevol missatge, per exemple:

```text
Hola
```

No passa res si el bot encara no respon. El missatge quedarà disponible perquè Telegram ens en mostri l’identificador.

## 6. Comprova primer el token

Al navegador, enganxa aquesta adreça substituint `EL_TEU_TOKEN` pel token real:

```text
https://api.telegram.org/botEL_TEU_TOKEN/getMe
```

Exemple de format — no facis servir aquest token fictici:

```text
https://api.telegram.org/bot1234567890:AAExemple/getMe
```

Hauries de veure:

```json
{"ok":true,"result":{...}}
```

Si apareix `Unauthorized`, el token està mal copiat o ha estat revocat.

## 7. Consulta els missatges rebuts

Obre:

```text
https://api.telegram.org/botEL_TEU_TOKEN/getUpdates
```

Busca un fragment semblant a:

```json
"chat": {
  "id": 123456789,
  "first_name": "Marc",
  "type": "private"
}
```

El número de `chat.id` és el valor que necessitem:

```text
123456789
```

Aquest valor serà el secret:

```text
TELEGRAM_CHAT_ID
```

### Si `result` surt buit

1. Torna al xat del bot.
2. Prem **Start**.
3. Envia-li un missatge nou.
4. Actualitza la pàgina `getUpdates`.

### Per enviar a més d’un xat

Pots guardar diversos identificadors separats per comes:

```text
123456789,-1001234567890
```

Els identificadors dels grups i canals acostumen a ser negatius. En un grup, primer has d’afegir-hi el bot i enviar-hi un missatge. En un canal, el bot ha de ser administrador per poder publicar.

---

# Part C. Crear el repositori de GitHub

## 8. Crea un repositori nou

A GitHub:

1. Prem el botó `+` de la part superior dreta.
2. Selecciona **New repository**.
3. A **Repository name**, posa:

```text
bon-dia-catalunya
```

4. Pots posar aquesta descripció:

```text
Bot de Telegram i web diari amb santoral, refranyer i efemèrides.
```

5. Recomanació inicial: marca **Public**.

El codi pot ser públic perquè el token i el `chat_id` no es guarden als fitxers, sinó als secrets de GitHub. GitHub Pages és disponible gratuïtament per a repositoris públics; en repositoris privats depèn del pla de GitHub.

6. **No** marquis `Add a README file`, perquè el projecte ja en porta un.
7. Prem **Create repository**.

## 9. Descomprimeix el projecte

Al teu ordinador:

1. Clica amb el botó dret sobre el ZIP.
2. Tria **Extreu-ho tot** o **Extract all**.
3. Obre la carpeta resultant.

A dins hi has de veure directament elements com:

```text
.github
src
data
docs
README.md
requirements.txt
```

No has de pujar una carpeta que contingui una segona carpeta `bon-dia-catalunya`. Has d’entrar fins al nivell on es veuen `.github`, `src`, `data` i `docs`.

## 10. Puja els fitxers des del navegador

A la pàgina del repositori buit:

1. Prem **uploading an existing file**, o bé **Add file → Upload files**.
2. Arrossega **tots els fitxers i carpetes** de dins del projecte a la finestra del navegador.
3. Comprova que també aparegui la carpeta:

```text
.github/workflows
```

Aquesta carpeta és imprescindible: conté les automatitzacions.

4. A **Commit changes**, escriu:

```text
Primera versió de Bon Dia Catalunya
```

5. Selecciona **Commit directly to the main branch**.
6. Prem **Commit changes**.

Quan acabi, el repositori ha de mostrar les carpetes `.github`, `data`, `docs`, `src` i `tests`.

---

# Part D. Permetre les automatitzacions

## 11. Revisa els permisos de GitHub Actions

Al repositori:

1. Ves a **Settings**.
2. Al menú lateral, entra a **Actions → General**.
3. A **Actions permissions**, deixa activada l’opció que permet executar les accions utilitzades pel projecte.
4. Baixa fins a **Workflow permissions**.
5. Selecciona:

```text
Read and write permissions
```

6. Prem **Save**.

Això permet que l’automatització arxivi cada dia al repositori la fitxa generada. El workflow també declara explícitament només els permisos que necessita.

---

# Part E. Guardar els secrets

## 12. Crea `TELEGRAM_BOT_TOKEN`

Al repositori:

1. Ves a **Settings**.
2. Entra a **Secrets and variables → Actions**.
3. Prem **New repository secret**.
4. A **Name**, escriu exactament:

```text
TELEGRAM_BOT_TOKEN
```

5. A **Secret**, enganxa el token de BotFather.
6. Prem **Add secret**.

## 13. Crea `TELEGRAM_CHAT_ID`

Repeteix el procés:

**Name**

```text
TELEGRAM_CHAT_ID
```

**Secret**

```text
123456789
```

Substitueix l’exemple pel teu identificador real.

GitHub només et mostrarà el nom del secret. Un cop desat, no tornarà a mostrar-ne el contingut.

---

# Part F. Activar GitHub Pages

## 14. Configura la publicació

Al repositori:

1. Ves a **Settings**.
2. Entra a **Pages**.
3. A **Build and deployment → Source**, selecciona:

```text
GitHub Actions
```

No seleccionis `Deploy from a branch`: el projecte utilitza el desplegament oficial de GitHub Pages des del mateix workflow de les 06.40 h.

No cal escriure manualment l’adreça a `data/config.json`. Si `web_url` està buit, el bot dedueix automàticament l’adreça habitual:

```text
https://EL_TEU_USUARI.github.io/bon-dia-catalunya/
```

Només hauràs d’emplenar `web_url` si més endavant utilitzes un domini personalitzat.

---

# Part G. Fer les proves inicials

## 15. Comprova el codi

1. Obre la pestanya **Actions**.
2. A l’esquerra, selecciona **Comprova el projecte**.
3. Prem **Run workflow**.
4. Deixa la branca `main`.
5. Torna a prémer **Run workflow**.

Al cap d’uns instants, la prova ha d’acabar amb una marca verda.

## 16. Comprova Telegram

1. A **Actions**, selecciona **Comprova la connexió amb Telegram**.
2. Prem **Run workflow**.
3. Deixa activat **Envia també un missatge breu de prova**.
4. Prem **Run workflow**.

El workflow comprovarà:

- que existeixin els dos secrets;
- que el token correspongui a un bot real;
- que el bot pugui accedir al `chat_id`;
- que pugui enviar-hi un missatge.

Hauries de rebre a Telegram:

```text
Bon Dia Catalunya està connectat
```

## 17. Genera i publica el web

1. A **Actions**, selecciona **Actualitza la fitxa diària**.
2. Prem **Run workflow**.
3. Deixa buida la data per generar el dia actual.
4. Prem **Run workflow**.

Aquest procés:

- consulta les fonts;
- genera el missatge;
- actualitza `docs/`;
- arxiva la fitxa del dia;
- publica GitHub Pages.

Quan acabi, a la pàgina del workflow veuràs l’enllaç del desplegament. També el trobaràs a **Settings → Pages**.

## 18. Envia el missatge complet

1. A **Actions**, selecciona **Envia el bon dia a Telegram**.
2. Prem **Run workflow**.
3. Deixa la data buida.
4. Prem **Run workflow**.

Hauries de rebre el missatge complet del dia.

---

# Part H. Provar una data concreta

Els workflows `Actualitza la fitxa diària` i `Envia el bon dia a Telegram` tenen un camp opcional de data.

Utilitza el format:

```text
AAAA-MM-DD
```

Exemples:

```text
2026-04-23
2026-09-11
2026-10-09
2026-12-31
```

Això permet provar Sant Jordi, la Diada, l’entrada de Jaume I a València o la conquesta de Mallorca sense canviar el rellotge del sistema.

> Una prova amb data antiga també pot substituir temporalment la portada del web i crear l’arxiu d’aquella data. Després torna a executar el workflow amb la data buida per restaurar el dia actual.

---

# Part I. Funcionament automàtic

Un cop superades les proves, no cal fer res més.

| Hora de Madrid | Acció |
|---|---|
| 06.40 h | Genera la fitxa, actualitza l’arxiu i publica el web. |
| 07.00 h | Genera de nou les dades i envia el missatge a Telegram. |
| Dilluns 09.17 h | Comprova que les fonts externes continuïn funcionant. |

GitHub pot retardar excepcionalment alguns workflows programats en períodes de molta càrrega. Les 06.40 h s’han triat per tenir marge abans de l’enviament de les 07.00 h.

En repositoris públics, GitHub pot desactivar els workflows programats després de 60 dies sense cap activitat. Una edició o execució manual els reactiva. Com que aquest bot genera commits diaris, normalment hi haurà activitat continuada.

---

# Solució ràpida de problemes

## El workflow no apareix a Actions

Comprova que existeixi:

```text
.github/workflows
```

I que la branca principal es digui `main`.

## `Bad credentials` o `Unauthorized`

El token és incorrecte o ha estat revocat. Genera’n un de nou amb BotFather i actualitza `TELEGRAM_BOT_TOKEN`.

## `chat not found`

- Prem **Start** al xat privat amb el bot.
- Torna a obtenir el `chat.id` amb `getUpdates`.
- Comprova que no hi hagi espais o cometes al secret.
- En un grup o canal, comprova que el bot encara hi sigui i que tingui els permisos necessaris.

## `bot was blocked by the user`

Has bloquejat el bot o n’has aturat el xat. Desbloqueja’l i torna a prémer **Start**.

## Error en fer `git push`

Ves a:

```text
Settings → Actions → General → Workflow permissions
```

I activa **Read and write permissions**.

## El web mostra un 404

- Comprova que **Settings → Pages → Source** sigui `GitHub Actions`.
- Executa manualment **Actualitza la fitxa diària**.
- Obre el pas **Publica el web** i comprova que hagi acabat en verd.

## El web s’actualitza però Telegram no

Executa **Comprova la connexió amb Telegram**. El registre indicarà si falla el token, el `chat_id` o l’enviament.

## Telegram funciona però falta l’enllaç al web

Primer executa **Actualitza la fitxa diària** i comprova que Pages estigui actiu. El projecte dedueix l’URL automàticament quan s’executa a GitHub.

---

# Enllaços oficials de referència

- Crear bots amb BotFather: https://core.telegram.org/bots/tutorial
- Telegram Bot API: https://core.telegram.org/bots/api
- Pujar fitxers a GitHub: https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository
- Secrets de GitHub Actions: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
- Configurar GitHub Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- Workflows programats: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

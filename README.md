# Bon Dia Catalunya 🌿

Bot de Telegram i web diari amb santoral català, refranyer, calendari de la terra i efemèrides de **Catalunya i els Països Catalans, Espanya, Europa i el món**.

Tot funciona des del navegador i GitHub Actions: no cal Visual Studio, un ordinador encès ni un servidor propi.

## Horari automàtic

| Hora local | Procés |
|---|---|
| 06.40 h | Consulta les fonts, genera la fitxa, arxiva el dia i desplega GitHub Pages. |
| 07.00 h | Torna a generar les dades i envia el missatge a Telegram. |
| Dilluns 09.17 h | Comprova que les fonts externes continuïn responent. |

Els workflows utilitzen `timezone: Europe/Madrid`, de manera que GitHub gestiona els canvis entre CET i CEST.

## Exemple de missatge

```text
🌿 Bon dia, Catalunya!

📅 Dimarts, 14 de juliol de 2026
🗓 Dia 195 de l’any · Setmana 29 · En falten 170
🌞 Sol a Barcelona: 06:30–21:23 · 🌙 lluna nova

🙏 Santoral català
Sant Camil de Lel·lis
També: Sant Francesc Solano, Santa Adela.

🌾 Refrany del dia
Al juliol, pobres dels qui són al sol.

🌱 Calendari de la terra
Al juliol continuen la sega, la collita de fruita dolça i les feines de reg...

🏛 Tal dia com avui
🇪🇸 Espanya
El 1931, s’obriren les Corts Constituents de la Segona República.

🇪🇺 Europa
El 1789, la població de París assaltà la Bastilla.

🌍 Món
El 1965, la sonda Mariner 4 completà el primer sobrevol reeixit de Mart.
```

Quan hi ha una efemèride catalana prou rellevant, apareix sempre abans de la resta:

```text
🟨🟥 Països Catalans → 🇪🇸 Espanya → 🇪🇺 Europa → 🌍 Món
```

## D’on surt cada bloc

### Santoral català

Consulta diària en cascada:

1. **Conferència Episcopal Tarraconense**, com a font institucional principal del sant o celebració litúrgica del dia.
2. **Santoral Català — Llauradó**, per completar noms secundaris del santoral popular.
3. **eCampmany**, reserva per al dia corrent.
4. `data/santoral_fallback.json`, reserva local per a dies especialment rellevants.

El Bloc Maragall i el Calendari dels Pagesos són calendaris editorials populars: solen coincidir en el sant principal, però poden seleccionar un nombre diferent de sants. El projecte no afirma una coincidència literal amb cap edició impresa.

Si una font canvia de format o cau, es prova automàticament la següent. El bot no deixa d’enviar la resta del missatge.

### Efemèrides

El sistema combina dues capes:

**Base pròpia revisada** — `data/efemerides.json`

- prioritat absoluta;
- text redactat en català;
- àmbit geogràfic explícit;
- importància de l’1 al 5;
- font obligatòria;
- només es publiquen entrades amb `verified: true`.

**Complement automàtic** — Wikimedia On This Day

- es consulta cada matinada en català;
- cerca esdeveniments i, com a reserva, naixements i morts;
- aplica un filtre de geografia, història, institucions, guerra, diplomàcia i política;
- classifica els candidats com `CAT`, `ESP`, `EUR` o `GLOBAL`;
- només omple els àmbits on no hi ha una efemèride pròpia revisada;
- la web identifica aquestes entrades com a «Selecció automàtica».

La selecció automàtica és una xarxa de seguretat, no substitueix la construcció progressiva d’una base editorial pròpia dels 366 dies.

### Calendari dels Pagesos, refranyer i productes de temporada

El **Calendari dels Pagesos** és el referent d’estil i tradició, però no se’n fa una còpia massiva ni una extracció automàtica. Els refranys i les notes estacionals es desen en bases pròpies:

- `data/refranys.json`
- `data/notes_estacionals.json`

Les fruites, hortalisses i espècies de pesca de temporada provenen del calendari oficial del Departament d’Agricultura de la Generalitat i es desen a `data/aliments_temporada.json`. A Telegram se’n mostra una selecció diària; al web apareix la llista mensual completa. La temporada pot variar segons la comarca i la meteorologia.

### Astronomia

La sortida i la posta del sol i la fase lunar es calculen localment amb `Astral`, a partir de les coordenades de `data/config.json`. No depenen d’una web externa.

### Dies internacionals i cites

Són bases pròpies revisables:

- `data/dies_internacionals.json`
- `data/cites.json`

## Posada en marxa només des del navegador

La configuració completa està explicada, clic per clic, a:

- **[GUIA_CONFIGURACIO.md](GUIA_CONFIGURACIO.md)** — BotFather, `chat_id`, repositori, secrets, GitHub Pages, proves i errors habituals.
- **[CHECKLIST_POSADA_EN_MARXA.md](CHECKLIST_POSADA_EN_MARXA.md)** — llista breu per no deixar-se cap pas.

El recorregut és aquest:

1. Crear el bot amb `@BotFather` i copiar-ne el token.
2. Prémer **Start** al bot i obtenir el `chat.id` amb `getUpdates`.
3. Crear el repositori i pujar-hi les carpetes del projecte.
4. Desar `TELEGRAM_BOT_TOKEN` i `TELEGRAM_CHAT_ID` com a secrets.
5. A GitHub Pages, seleccionar **Source: GitHub Actions**.
6. Executar `Comprova la connexió amb Telegram`.
7. Executar `Actualitza la fitxa diària` i `Envia el bon dia a Telegram`.

La URL habitual de GitHub Pages es dedueix automàticament a partir del repositori. El camp `web_url` de `data/config.json` només cal emplenar-lo si s’utilitza un domini personalitzat.

## Arxius principals

```text
.github/workflows/       Automatitzacions de GitHub
src/generate.py          Generació del missatge i del web
src/send_telegram.py     Enviament a Telegram
src/validate_data.py     Control de la base editorial
src/sources/             Santoral i Wikimedia
data/efemerides.json     Efemèrides pròpies verificades
data/SCHEMA.md           Regles per afegir-ne de noves
docs/                    Web de GitHub Pages
docs/archive/            Arxiu diari automàtic
```

## Com afegir una efemèride

Consulta `data/SCHEMA.md`. Exemple:

```json
{
  "id": "cat-1705-carles-iii-constitucions",
  "year": 1705,
  "scope": "CAT",
  "territory": "Principat de Catalunya",
  "category": "institucions",
  "importance": 5,
  "featured": true,
  "title": "Carles III jura les constitucions catalanes",
  "text": "l’arxiduc Carles d’Àustria jurà les constitucions catalanes a Barcelona.",
  "source_name": "Font historiogràfica",
  "source_url": "https://...",
  "verified": true
}
```

Abans de publicar, GitHub executa automàticament:

```bash
python src/validate_data.py
pytest -q
```

## Principis editorials

1. El missatge és íntegrament en català.
2. L’ordre és sempre `CAT → ESP → EUR → GLOBAL`.
3. No s’omple espai amb efemèrides irrellevants: un àmbit es pot ometre.
4. Cap entrada pròpia sense font i verificació.
5. No es confonen fet històric, commemoració, tradició i llegenda.
6. Telegram és breu; el web conserva les fonts i el context.

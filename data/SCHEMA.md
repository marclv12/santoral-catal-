# Esquema editorial de les efemèrides

Cada entrada de `efemerides.json` ha de tenir:

```json
{
  "id": "cat-1705-carles-iii",
  "year": 1705,
  "scope": "CAT",
  "territory": "Principat de Catalunya",
  "category": "historia_politica",
  "importance": 5,
  "featured": true,
  "title": "Títol breu",
  "text": "Text en català, autosuficient i rigorós.",
  "source_name": "Institució o obra",
  "source_url": "https://...",
  "verified": true
}
```

## Àmbits i ordre

1. `CAT`: Catalunya i el conjunt dels Països Catalans.
2. `ESP`: Espanya.
3. `EUR`: Europa.
4. `GLOBAL`: món.

## Importància

- `5`: fet fonamental.
- `4`: molt rellevant.
- `3`: rellevant.
- `2`: secundari.
- `1`: curiositat, normalment exclosa de Telegram.

## Categories admeses

`historia_politica`, `geografia`, `institucions`, `guerra_i_diplomacia`, `cultura`, `ciencia`, `societat`.

Les entrades manuals han d'estar verificades i tenir una font consultable. La selecció automàtica de Wikimedia només actua quan falta una entrada revisada en un àmbit.

from __future__ import annotations

from datetime import date, datetime
from html import escape
import json
import os
from pathlib import Path
import random
from typing import Any

from astral import LocationInfo
from astral.moon import phase
from astral.sun import sun
from zoneinfo import ZoneInfo

try:
    from .sources.efemerides import SCOPE_ORDER, fetch_dynamic_events, select_events
    from .sources.santoral import get_santoral
except ImportError:  # Execució directa: python src/generate.py
    from sources.efemerides import SCOPE_ORDER, fetch_dynamic_events, select_events
    from sources.santoral import get_santoral

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
ARCHIVE = DOCS / "archive"

SCOPE_META = {
    "CAT": {"label": "Països Catalans", "icon": "🟨🟥"},
    "ESP": {"label": "Espanya", "icon": "🇪🇸"},
    "EUR": {"label": "Europa", "icon": "🇪🇺"},
    "GLOBAL": {"label": "Món", "icon": "🌍"},
}


def load_json(name: str, default: Any = None) -> Any:
    path = DATA / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def catalan_date(day: date) -> str:
    weekdays = ["dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte", "diumenge"]
    months = ["gener", "febrer", "març", "abril", "maig", "juny", "juliol", "agost", "setembre", "octubre", "novembre", "desembre"]
    return f"{weekdays[day.weekday()].capitalize()}, {day.day} de {months[day.month - 1]} de {day.year}"


def moon_phase_name(value: float) -> str:
    if value < 1.75 or value >= 26.25:
        return "lluna nova"
    if value < 5.25:
        return "creixent"
    if value < 8.75:
        return "quart creixent"
    if value < 12.25:
        return "gibosa creixent"
    if value < 15.75:
        return "lluna plena"
    if value < 19.25:
        return "gibosa minvant"
    if value < 22.75:
        return "quart minvant"
    return "minvant"


def _local_day(config: dict[str, Any]) -> date:
    if os.getenv("TARGET_DATE"):
        return date.fromisoformat(os.environ["TARGET_DATE"])
    return datetime.now(ZoneInfo(config["timezone"])).date()


def _seasonal_selection(day: date, data: dict[str, Any]) -> dict[str, Any] | None:
    entry = data.get(f"{day.month:02d}")
    if not entry:
        return None
    rng = random.Random(day.isoformat() + "-aliments")

    def choose(values: list[str], limit: int) -> list[str]:
        if len(values) <= limit:
            return list(values)
        return rng.sample(values, limit)

    return {
        "fruites": choose(entry.get("fruites", []), 4),
        "hortalisses": choose(entry.get("hortalisses", []), 5),
        "pesca": choose(entry.get("pesca", []), 3),
        "all": {
            "fruites": entry.get("fruites", []),
            "hortalisses": entry.get("hortalisses", []),
            "pesca": entry.get("pesca", []),
        },
        "source": entry.get("source", {}),
    }


def build_payload(day: date | None = None) -> dict[str, Any]:
    config = load_json("config.json", {})
    day = day or _local_day(config)
    key = day.strftime("%m-%d")
    tz = ZoneInfo(config["timezone"])
    location_data = config["location"]
    location = LocationInfo(
        location_data["name"],
        location_data.get("region", "Catalunya"),
        config["timezone"],
        location_data["latitude"],
        location_data["longitude"],
    )
    solar = sun(location.observer, date=day, tzinfo=tz)
    santoral = get_santoral(day)

    curated = load_json("efemerides.json", {}).get(key, [])
    dynamic = [] if os.getenv("DISABLE_DYNAMIC_SOURCES") == "1" else fetch_dynamic_events(day)
    events = select_events(curated, dynamic, int(config.get("message", {}).get("max_events", 4)))

    refranys = load_json("refranys.json", {}).get(key, [])
    dies = load_json("dies_internacionals.json", {}).get(key, [])
    cites = load_json("cites.json", [])
    seasonal = load_json("notes_estacionals.json", {}).get(f"{day.month:02d}", [])
    seasonal_foods = _seasonal_selection(day, load_json("aliments_temporada.json", {}))

    random.seed(day.isoformat())
    return {
        "date": day.isoformat(),
        "date_ca": catalan_date(day),
        "day_of_year": day.timetuple().tm_yday,
        "days_remaining": (date(day.year, 12, 31) - day).days,
        "week": day.isocalendar().week,
        "location": location_data["name"],
        "sunrise": solar["sunrise"].strftime("%H:%M"),
        "sunset": solar["sunset"].strftime("%H:%M"),
        "moon_phase": moon_phase_name(phase(day)),
        "saints": santoral.saints,
        "saint_source": {
            "name": santoral.source_name,
            "url": santoral.source_url,
            "status": santoral.status,
        },
        "efemerides": events,
        "scope_order": list(SCOPE_ORDER),
        "refrany": random.choice(refranys) if refranys else None,
        "seasonal_note": random.choice(seasonal) if seasonal else None,
        "seasonal_foods": seasonal_foods,
        "international_days": dies[:2],
        "quote": random.choice(cites) if cites else None,
        "generated_at": datetime.now(tz).isoformat(timespec="seconds"),
    }


def _event_sentence(event: dict[str, Any]) -> str:
    text = str(event["text"]).strip()
    if len(text) > 360:
        text = text[:357].rsplit(" ", 1)[0] + "…"
    if not text:
        return ""
    prefix = f"El {event['year']}, " if event.get("year") else ""
    if text.lower().startswith(("l'any ", "aquest dia")):
        prefix = ""
    return prefix + text[0].lower() + text[1:]


def telegram_html(payload: dict[str, Any]) -> str:
    saints = payload["saints"]
    lines = [
        "🌿 <b>Bon dia, Catalunya!</b>",
        "",
        f"📅 <b>{escape(payload['date_ca'])}</b>",
        f"🗓 Dia {payload['day_of_year']} de l’any · Setmana {payload['week']} · En falten {payload['days_remaining']}",
        f"🌞 Sol a {escape(payload['location'])}: {payload['sunrise']}–{payload['sunset']} · 🌙 {escape(payload['moon_phase'])}",
        "",
        "🙏 <b>Santoral català</b>",
        escape(saints[0]) if saints else "Sense dades disponibles",
    ]
    if len(saints) > 1:
        lines.append("També: " + escape(", ".join(saints[1:6])) + ".")

    if payload.get("refrany"):
        lines += ["", "🌾 <b>Refrany del dia</b>", f"<i>{escape(payload['refrany'])}</i>"]
    if payload.get("seasonal_note"):
        lines += ["", "🌱 <b>Calendari de la terra</b>", escape(payload["seasonal_note"])]

    foods = payload.get("seasonal_foods")
    if foods:
        lines += ["", "🍅 <b>Aliments de temporada</b>"]
        if foods.get("fruites"):
            lines.append("Fruita: " + escape(", ".join(foods["fruites"])) + ".")
        if foods.get("hortalisses"):
            lines.append("Horta: " + escape(", ".join(foods["hortalisses"])) + ".")
        if foods.get("pesca"):
            lines.append("Mar: " + escape(", ".join(foods["pesca"])) + ".")

    if payload.get("efemerides"):
        lines += ["", "🏛 <b>Tal dia com avui</b>"]
        for event in payload["efemerides"]:
            meta = SCOPE_META[event["scope"]]
            lines.append(f"{meta['icon']} <b>{meta['label']}</b>")
            lines.append(escape(_event_sentence(event)))

    if payload.get("international_days"):
        lines += ["", "🌍 <b>Avui també és</b>"] + [f"• {escape(x)}" for x in payload["international_days"]]
    if payload.get("quote"):
        q = payload["quote"]
        lines += ["", "💬 <b>Paraules del país</b>", f"«{escape(q['text'])}» — {escape(q['author'])}"]

    web_url = load_json("config.json", {}).get("web_url", "").strip()
    if not web_url:
        repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
        if "/" in repository:
            owner, repository_name = repository.split("/", 1)
            if repository_name.lower() == f"{owner.lower()}.github.io":
                web_url = f"https://{owner}.github.io/"
            else:
                web_url = f"https://{owner}.github.io/{repository_name}/"

    source_link = f'<a href="{escape(payload["saint_source"]["url"])}">Santoral</a>'
    footer = source_link
    if web_url:
        footer += f' · <a href="{escape(web_url)}">Fitxa i fonts</a>'
    lines += ["", footer]
    return "\n".join(lines)


def _event_cards(events: list[dict[str, Any]]) -> str:
    if not events:
        return "<p>Avui no hi ha cap efemèride amb prou rellevància o verificació.</p>"
    cards: list[str] = []
    for event in events:
        meta = SCOPE_META[event["scope"]]
        origin = "Base revisada" if event.get("origin") == "curated" else "Selecció automàtica"
        cards.append(
            "<article class='event'>"
            f"<div class='scope'>{meta['icon']} {escape(meta['label'])}</div>"
            f"<h3>{escape(str(event['year'])) + ' · ' if event.get('year') else ''}{escape(event['title'])}</h3>"
            f"<p>{escape(event['text'])}</p>"
            f"<p class='meta'>{escape(origin)} · {escape(event.get('territory', meta['label']))} · "
            f"<a href='{escape(event['source_url'])}' rel='noopener'>{escape(event['source_name'])}</a></p>"
            "</article>"
        )
    return "".join(cards)


def _food_block(payload: dict[str, Any]) -> str:
    foods = payload.get("seasonal_foods")
    if not foods:
        return "<p>—</p>"
    full = foods.get("all", {})
    source = foods.get("source", {})
    sections = []
    for key, label in (("fruites", "Fruites"), ("hortalisses", "Hortalisses"), ("pesca", "Peix i marisc")):
        values = full.get(key, [])
        sections.append(f"<h3>{label}</h3><p>{escape(', '.join(values)) if values else '—'}</p>")
    if source.get("url"):
        sections.append(
            f"<p class='meta'><a href='{escape(source['url'])}' rel='noopener'>{escape(source.get('name', 'Font'))}</a>. "
            f"{escape(source.get('note', ''))}</p>"
        )
    return "".join(sections)


def _render_page(payload: dict[str, Any]) -> str:
    saints_secondary = ", ".join(payload["saints"][1:8])
    days = "".join(f"<li>{escape(item)}</li>" for item in payload.get("international_days", []))
    quote = payload.get("quote") or {}
    return f"""<!doctype html>
<html lang="ca">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="Santoral català, refranyer i efemèrides diàries de Catalunya, Espanya, Europa i el món.">
  <title>Bon Dia Catalunya · {escape(payload['date_ca'])}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
<main>
  <header>
    <span class="brand">🌿</span>
    <h1>Bon Dia Catalunya</h1>
    <p>{escape(payload['date_ca'])}</p>
    <div class="calendar-line">Dia {payload['day_of_year']} · Setmana {payload['week']} · Sol {payload['sunrise']}–{payload['sunset']} · {escape(payload['moon_phase'])}</div>
  </header>
  <section>
    <h2>🙏 Santoral català</h2>
    <p class="lead">{escape(payload['saints'][0] if payload['saints'] else 'Sense dades')}</p>
    <p>{escape(saints_secondary)}</p>
    <p class="meta"><a href="{escape(payload['saint_source']['url'])}">{escape(payload['saint_source']['name'])}</a></p>
  </section>
  <section class="two-columns">
    <div><h2>🌾 Refrany</h2><blockquote>{escape(payload.get('refrany') or '—')}</blockquote></div>
    <div><h2>🌱 Calendari de la terra</h2><p>{escape(payload.get('seasonal_note') or '—')}</p></div>
  </section>
  <section>
    <h2>🍅 Aliments de temporada</h2>
    {_food_block(payload)}
  </section>
  <section>
    <h2>🏛 Tal dia com avui</h2>
    <p class="intro">Selecció en ordre: Països Catalans, Espanya, Europa i món.</p>
    {_event_cards(payload.get('efemerides', []))}
  </section>
  <section class="two-columns">
    <div><h2>🌍 Avui també és</h2><ul>{days or '<li>—</li>'}</ul></div>
    <div><h2>💬 Paraules del país</h2><blockquote>{('«' + escape(quote.get('text', '')) + '»') if quote else '—'}</blockquote><p>{escape(quote.get('author', ''))}</p></div>
  </section>
  <footer>Actualitzat: {escape(payload['generated_at'])} · <a href="today.json">Dades JSON</a></footer>
</main>
</body>
</html>"""


def write_outputs(payload: dict[str, Any]) -> None:
    DOCS.mkdir(exist_ok=True)
    ARCHIVE.mkdir(exist_ok=True)
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    (DOCS / "today.json").write_text(json_text, encoding="utf-8")
    (DOCS / "message.html").write_text(telegram_html(payload), encoding="utf-8")
    page = _render_page(payload)
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    archive_page = page.replace('href="style.css"', 'href="../style.css"').replace(
        'href="today.json"', f'href="{payload["date"]}.json"'
    )
    (ARCHIVE / f"{payload['date']}.html").write_text(archive_page, encoding="utf-8")
    (ARCHIVE / f"{payload['date']}.json").write_text(json_text, encoding="utf-8")

    archive_index_path = DOCS / "archive.json"
    archive_items = []
    if archive_index_path.exists():
        try:
            archive_items = json.loads(archive_index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            archive_items = []
    archive_items = [item for item in archive_items if item.get("date") != payload["date"]]
    archive_items.insert(0, {"date": payload["date"], "date_ca": payload["date_ca"], "url": f"archive/{payload['date']}.html"})
    archive_index_path.write_text(json.dumps(archive_items[:400], ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    result = build_payload()
    write_outputs(result)
    print(telegram_html(result))

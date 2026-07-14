from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Any, Iterable

import requests

USER_AGENT = "BonDiaCatalunya/2.0 (+https://github.com/marclopezventura/bon-dia-catalunya)"
SCOPE_ORDER = ("CAT", "ESP", "EUR", "GLOBAL")

CAT_TERMS = {
    "catalunya", "català", "catalana", "catalans", "barcelona", "girona", "lleida",
    "tarragona", "valència", "valenciana", "mallorca", "menorca", "eivissa", "formentera",
    "illes balears", "país valencià", "catalunya nord", "rosselló", "andorra", "l'alguer",
    "alguer", "franja de ponent", "corona d'aragó", "generalitat", "principat de catalunya",
}
ESP_TERMS = {
    "espanya", "espanyol", "espanyola", "madrid", "castella", "andalusia", "galícia",
    "astúries", "navarra", "aragó", "canàries", "extremadura", "murcia", "cantàbria",
    "país basc", "corts constituents", "monarquia hispànica",
}
EUR_TERMS = {
    "europa", "frança", "parís", "alemanya", "berlín", "itàlia", "roma", "portugal",
    "lisboa", "regne unit", "londres", "irlanda", "bèlgica", "brussel·les", "països baixos",
    "àustria", "viena", "hongria", "polònia", "varsòvia", "txèquia", "praga", "eslovàquia",
    "suècia", "noruega", "dinamarca", "finlàndia", "grècia", "atenes", "romanía", "romania",
    "bulgària", "croàcia", "sèrbia", "ucraïna", "rússia", "moscou", "unió europea",
    "imperi romà", "imperi austrohongarès", "sacre imperi",
}
HISTORY_TERMS = {
    "guerra", "batalla", "setge", "tractat", "pau", "revolució", "independència", "república",
    "constitució", "parlament", "corts", "govern", "president", "rei", "reina", "emperador",
    "imperi", "eleccions", "cop d'estat", "dictadura", "ocupació", "conquesta", "capitulació",
    "annexió", "frontera", "estat", "nacions unides", "otan", "ue", "unió europea", "referèndum",
    "proclam", "fundació", "fundà", "inaugur", "descobr", "expedició", "mapa", "geògraf",
    "explor", "colònia", "abolició", "decret", "autonomia", "estatut", "atemptat",
}


@dataclass(frozen=True)
class DynamicEvent:
    year: int | None
    title: str
    text: str
    scope: str
    territory: str
    category: str
    importance: int
    source_name: str
    source_url: str
    verified: bool = False
    origin: str = "automatic"

    def as_dict(self) -> dict[str, Any]:
        return {
            "year": self.year,
            "title": self.title,
            "text": self.text,
            "scope": self.scope,
            "territory": self.territory,
            "category": self.category,
            "importance": self.importance,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "verified": self.verified,
            "origin": self.origin,
        }


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    folded = text.casefold()
    return any(term in folded for term in terms)


def classify_scope(text: str) -> str:
    if _contains_any(text, CAT_TERMS):
        return "CAT"
    if _contains_any(text, ESP_TERMS):
        return "ESP"
    if _contains_any(text, EUR_TERMS):
        return "EUR"
    return "GLOBAL"


def relevance_score(text: str, pages_count: int = 0) -> int:
    folded = text.casefold()
    matches = sum(1 for term in HISTORY_TERMS if term in folded)
    score = matches * 3 + min(pages_count, 4)
    if len(text) < 55:
        score -= 1
    if len(text) > 420:
        score -= 2
    return score


def _page_url(event: dict[str, Any], language: str, day: date) -> str:
    pages = event.get("pages") or []
    for page in pages:
        urls = page.get("content_urls") or {}
        desktop = urls.get("desktop") or {}
        if desktop.get("page"):
            return desktop["page"]
    months = {
        "ca": ["gener", "febrer", "març", "abril", "maig", "juny", "juliol", "agost", "setembre", "octubre", "novembre", "desembre"],
        "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    }
    month = months.get(language, months["ca"])[day.month - 1]
    return f"https://{language}.wikipedia.org/wiki/{day.day}_de_{month}"


def _event_title(event: dict[str, Any]) -> str:
    pages = event.get("pages") or []
    if pages and pages[0].get("normalizedtitle"):
        return _normalise(str(pages[0]["normalizedtitle"]))
    if pages and pages[0].get("title"):
        return _normalise(str(pages[0]["title"]).replace("_", " "))
    text = _normalise(str(event.get("text") or "Efemèride històrica"))
    return text[:90].rstrip(" .")


def _fetch_language(day: date, language: str, kind: str) -> list[dict[str, Any]]:
    urls = [
        f"https://api.wikimedia.org/feed/v1/wikipedia/{language}/onthisday/{kind}/{day.month:02d}/{day.day:02d}",
        f"https://{language}.wikipedia.org/api/rest_v1/feed/onthisday/{kind}/{day.month:02d}/{day.day:02d}",
    ]
    last_error: Exception | None = None
    for url in urls:
        try:
            response = requests.get(
                url,
                timeout=25,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
            items = payload.get(kind) or []
            if items:
                return items
        except Exception as exc:
            last_error = exc
    if last_error:
        raise last_error
    return []


def _historical_text(raw_text: str, kind: str) -> str:
    text = _normalise(raw_text).rstrip(".")
    if kind == "births":
        return f"naixia {text}."
    if kind == "deaths":
        return f"moria {text}."
    return text + ("" if text.endswith(".") else ".")


def fetch_dynamic_events(day: date) -> list[dict[str, Any]]:
    candidates: list[DynamicEvent] = []
    seen: set[tuple[int | None, str]] = set()

    # El missatge final és íntegrament en català; per això només publiquem text de la Viquipèdia catalana.
    # Naixements i morts només actuen com a reserva per omplir àmbits sense un fet històric general.
    for language in ("ca",):
        for kind in ("events", "births", "deaths"):
            try:
                events = _fetch_language(day, language, kind)
            except Exception:
                continue
            for raw in events:
                source_text = _normalise(str(raw.get("text") or ""))
                if not source_text:
                    continue
                pages = raw.get("pages") or []
                classification_text = source_text + " " + " ".join(
                    " ".join(
                        str(p.get(field, ""))
                        for field in ("title", "normalizedtitle", "description", "extract")
                    )
                    for p in pages
                )
                scope = classify_scope(classification_text)
                score = relevance_score(classification_text, len(pages))
                minimum = 4 if kind == "events" else 5
                if score < minimum:
                    continue
                year = raw.get("year")
                try:
                    year = int(year) if year is not None else None
                except (TypeError, ValueError):
                    year = None
                text = _historical_text(source_text, kind)
                key = (year, text.casefold())
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(
                    DynamicEvent(
                        year=year,
                        title=_event_title(raw),
                        text=text,
                        scope=scope,
                        territory={"CAT": "Països Catalans", "ESP": "Espanya", "EUR": "Europa", "GLOBAL": "Món"}[scope],
                        category="historia_politica_geografia",
                        importance=max(2, min(4 if kind == "events" else 3, 2 + score // 6)),
                        source_name=f"Viquipèdia ({language})",
                        source_url=_page_url(raw, language, day),
                    )
                )

    candidates.sort(key=lambda item: (item.importance, relevance_score(item.text)), reverse=True)
    return [item.as_dict() for item in candidates]

def select_events(
    curated: list[dict[str, Any]],
    dynamic: list[dict[str, Any]],
    max_events: int = 4,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used_keys: set[tuple[int | None, str]] = set()

    for scope in SCOPE_ORDER:
        curated_scope = [e for e in curated if e.get("scope") == scope and e.get("verified", False)]
        curated_scope.sort(
            key=lambda e: (bool(e.get("featured")), int(e.get("importance", 0))),
            reverse=True,
        )
        pool = curated_scope or [e for e in dynamic if e.get("scope") == scope]
        for event in pool:
            key = (event.get("year"), str(event.get("title", "")).casefold())
            if key in used_keys:
                continue
            item = dict(event)
            item.setdefault("origin", "curated" if event.get("verified") is True else "automatic")
            selected.append(item)
            used_keys.add(key)
            break
        if len(selected) >= max_events:
            break

    return selected

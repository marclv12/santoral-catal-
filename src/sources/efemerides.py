from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Any, Iterable
from urllib.parse import quote

from bs4 import BeautifulSoup, Tag
import requests


USER_AGENT = (
    "BonDiaCatalunya/2.1 "
    "(+https://github.com/marclv12/santoral-catal-)"
)

SCOPE_ORDER = ("CAT", "ESP", "EUR", "GLOBAL")

CAT_TERMS = {
    "catalunya",
    "català",
    "catalana",
    "catalans",
    "barcelona",
    "girona",
    "lleida",
    "tarragona",
    "valència",
    "valenciana",
    "mallorca",
    "menorca",
    "eivissa",
    "formentera",
    "illes balears",
    "país valencià",
    "catalunya nord",
    "rosselló",
    "andorra",
    "l'alguer",
    "alguer",
    "franja de ponent",
    "corona d'aragó",
    "generalitat",
    "principat de catalunya",
    "mossos d'esquadra",
    "diputació del general",
    "furs valencians",
    "constitucions catalanes",
}

ESP_TERMS = {
    "espanya",
    "espanyol",
    "espanyola",
    "espanyols",
    "madrid",
    "castella",
    "andalusia",
    "galícia",
    "astúries",
    "navarra",
    "aragó",
    "canàries",
    "extremadura",
    "múrcia",
    "murcia",
    "cantàbria",
    "país basc",
    "corts constituents",
    "monarquia hispànica",
    "república espanyola",
    "guerra civil espanyola",
}

EUR_TERMS = {
    "europa",
    "frança",
    "parís",
    "alemanya",
    "berlín",
    "itàlia",
    "roma",
    "portugal",
    "lisboa",
    "regne unit",
    "londres",
    "irlanda",
    "bèlgica",
    "brussel·les",
    "països baixos",
    "utrecht",
    "àustria",
    "viena",
    "hongria",
    "polònia",
    "varsòvia",
    "txèquia",
    "praga",
    "eslovàquia",
    "suècia",
    "noruega",
    "dinamarca",
    "finlàndia",
    "grècia",
    "atenes",
    "romanía",
    "romania",
    "bulgària",
    "croàcia",
    "sèrbia",
    "ucraïna",
    "rússia",
    "moscou",
    "unió europea",
    "imperi romà",
    "imperi austrohongarès",
    "sacre imperi",
    "bordeus",
}

HISTORY_TERMS = {
    "guerra",
    "batalla",
    "setge",
    "tractat",
    "pau",
    "revolució",
    "independència",
    "república",
    "constitució",
    "parlament",
    "corts",
    "govern",
    "president",
    "rei",
    "reina",
    "emperador",
    "imperi",
    "eleccions",
    "cop d'estat",
    "dictadura",
    "ocupació",
    "conquesta",
    "capitulació",
    "annexió",
    "frontera",
    "estat",
    "nacions unides",
    "otan",
    "unió europea",
    "referèndum",
    "proclam",
    "fundació",
    "fundà",
    "inaugur",
    "descobr",
    "expedició",
    "mapa",
    "geògraf",
    "explor",
    "colònia",
    "abolició",
    "decret",
    "autonomia",
    "estatut",
    "atemptat",
    "exili",
    "invasió",
    "envaeix",
    "signa",
    "aprova",
    "derrota",
    "allibera",
    "reconeix",
    "jura",
}

MONTHS_CA = [
    "gener",
    "febrer",
    "març",
    "abril",
    "maig",
    "juny",
    "juliol",
    "agost",
    "setembre",
    "octubre",
    "novembre",
    "desembre",
]

SCOPE_TERRITORY = {
    "CAT": "Països Catalans",
    "ESP": "Espanya",
    "EUR": "Europa",
    "GLOBAL": "Món",
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
    score: int = 0

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
            "score": self.score,
        }


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    folded = text.casefold()
    return any(term in folded for term in terms)


def classify_scope(text: str) -> str:
    """
    Classifica una efemèride per proximitat territorial.

    L'ordre és intencionadament:
    CAT → ESP → EUR → GLOBAL.
    """
    if _contains_any(text, CAT_TERMS):
        return "CAT"

    if _contains_any(text, ESP_TERMS):
        return "ESP"

    if _contains_any(text, EUR_TERMS):
        return "EUR"

    return "GLOBAL"


def relevance_score(text: str, pages_count: int = 0) -> int:
    """
    Puntua els fets per ordenar-los.

    Important: aquesta puntuació ja no s'utilitza per eliminar
    totes les efemèrides que no contenen determinades paraules.
    """
    folded = text.casefold()

    matches = sum(
        1
        for term in HISTORY_TERMS
        if term in folded
    )

    score = matches * 3 + min(pages_count, 4)

    if len(text) < 45:
        score -= 1

    if len(text) > 500:
        score -= 2

    return score


def _date_page_title(day: date) -> str:
    month = MONTHS_CA[day.month - 1]
    return f"{day.day} de {month}"


def _date_page_url(day: date) -> str:
    title = _date_page_title(day).replace(" ", "_")
    return f"https://ca.wikipedia.org/wiki/{quote(title)}"


def _api_get(params: dict[str, Any]) -> dict[str, Any]:
    """
    Executa una consulta a la MediaWiki Action API.
    """
    response = requests.get(
        "https://ca.wikipedia.org/w/api.php",
        params={
            "format": "json",
            "formatversion": "2",
            **params,
        },
        timeout=25,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))

    return payload


def _clean_heading(value: Any) -> str:
    text = BeautifulSoup(
        str(value or ""),
        "html.parser",
    ).get_text(" ", strip=True)

    text = re.sub(r"\[\d+\]", "", text)

    return _normalise(text).casefold()


def _find_section_index(
    day: date,
    accepted_names: tuple[str, ...],
) -> str | None:
    """
    Busca l'índex de la secció «Esdeveniments» de la pàgina
    corresponent a la data.
    """
    payload = _api_get(
        {
            "action": "parse",
            "page": _date_page_title(day),
            "prop": "tocdata",
            "redirects": "1",
        }
    )

    tocdata = payload.get("parse", {}).get("tocdata", {})
    sections = tocdata.get("sections", [])

    accepted = tuple(
        name.casefold()
        for name in accepted_names
    )

    for section in sections:
        line = _clean_heading(section.get("line"))

        if any(
            line == name or line.startswith(name + " ")
            for name in accepted
        ):
            return str(section.get("index"))

    return None


def _fetch_section_html(
    day: date,
    accepted_names: tuple[str, ...],
) -> str:
    """
    Recupera l'HTML d'una secció concreta de la pàgina de la data.
    """
    section_index = _find_section_index(
        day,
        accepted_names,
    )

    if section_index is None:
        return ""

    payload = _api_get(
        {
            "action": "parse",
            "page": _date_page_title(day),
            "prop": "text",
            "section": section_index,
            "redirects": "1",
            "disableeditsection": "1",
        }
    )

    return str(
        payload.get("parse", {}).get("text", "")
    )


def _is_reference_item(li: Tag) -> bool:
    """
    Evita confondre les referències bibliogràfiques amb fets històrics.
    """
    item_id = str(li.get("id", ""))

    if item_id.startswith("cite_note"):
        return True

    for parent in li.parents:
        if not isinstance(parent, Tag):
            continue

        classes = set(parent.get("class", []))

        if {"references", "reflist"} & classes:
            return True

    return False


def _extract_year_and_text(
    raw_text: str,
) -> tuple[int | None, str]:
    """
    Separa l'any del text.

    Exemple:
    1713 - Utrecht: Se signa...
    """
    text = _normalise(raw_text)

    text = re.sub(
        r"\s*\[(?:\d+|nota\s+\d+)\]\s*",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = _normalise(text)

    pattern = re.compile(
        r"^(?P<year>\d{1,4})"
        r"(?:\s*(?P<bc>a\.?\s*C\.?|abans de Crist))?"
        r"\s*[-–—:]\s*"
        r"(?P<body>.+)$",
        re.IGNORECASE,
    )

    match = pattern.match(text)

    if not match:
        return (
            None,
            text.rstrip(" .") + ".",
        )

    year = int(match.group("year"))

    if match.group("bc"):
        year = -year

    body = (
        _normalise(match.group("body"))
        .rstrip(" .")
        + "."
    )

    return year, body


def _short_title(text: str) -> str:
    title = text.rstrip(" .")

    if len(title) > 96:
        title = (
            title[:93]
            .rsplit(" ", 1)[0]
            + "…"
        )

    return title


def _iter_event_items(
    html: str,
) -> list[tuple[str | None, Tag]]:
    """
    Localitza les llistes d'esdeveniments.

    També conserva el subtítol anterior, per exemple
    «Països Catalans» o «Resta del món».
    """
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    root = (
        soup.select_one(".mw-parser-output")
        or soup
    )

    output: list[tuple[str | None, Tag]] = []
    current_heading: str | None = None

    for child in root.children:
        if not isinstance(child, Tag):
            continue

        if child.name in {
            "h2",
            "h3",
            "h4",
            "dl",
            "p",
        }:
            heading_text = _normalise(
                child.get_text(" ", strip=True)
            )

            if heading_text:
                current_heading = heading_text

        if child.name == "ul":
            for li in child.find_all(
                "li",
                recursive=False,
            ):
                if not _is_reference_item(li):
                    output.append(
                        (current_heading, li)
                    )

    # Reserva per si la Viquipèdia canvia l'estructura.
    if not output:
        for li in root.find_all("li"):
            if not _is_reference_item(li):
                output.append((None, li))

    return output


def _events_from_date_page(
    day: date,
) -> list[dict[str, Any]]:
    """
    Font principal: secció «Esdeveniments» de la pàgina catalana
    de la data.
    """
    html = _fetch_section_html(
        day,
        (
            "esdeveniments",
            "fets",
            "efemèrides",
        ),
    )

    if not html:
        return []

    source_url = _date_page_url(day)

    candidates: list[DynamicEvent] = []
    seen: set[tuple[int | None, str]] = set()

    for heading, li in _iter_event_items(html):
        for unwanted in li.select(
            "sup.reference, "
            ".mw-editsection, "
            "style, "
            "script"
        ):
            unwanted.decompose()

        raw_text = _normalise(
            li.get_text(" ", strip=True)
        )

        if not raw_text:
            continue

        year, text = _extract_year_and_text(
            raw_text
        )

        if len(text) < 18:
            continue

        linked_text = " ".join(
            (
                _normalise(
                    link.get_text(" ", strip=True)
                )
                + " "
                + str(link.get("title", ""))
            )
            for link in li.find_all("a")
        )

        classification_text = (
            text + " " + linked_text
        )

        heading_folded = (
            heading or ""
        ).casefold()

        if (
            "països catalans" in heading_folded
            or "catalunya" in heading_folded
        ):
            scope = "CAT"
        else:
            scope = classify_scope(
                classification_text
            )

        score = relevance_score(
            classification_text,
            len(li.find_all("a")),
        )

        # Ja no hi ha cap llindar mínim.
        # Tots els elements de la secció Esdeveniments
        # són candidats vàlids.
        importance = max(
            2,
            min(
                4,
                2 + max(score, 0) // 6,
            ),
        )

        key = (
            year,
            text.casefold(),
        )

        if key in seen:
            continue

        seen.add(key)

        candidates.append(
            DynamicEvent(
                year=year,
                title=_short_title(text),
                text=text,
                scope=scope,
                territory=SCOPE_TERRITORY[scope],
                category=(
                    "historia_politica_geografia"
                ),
                importance=importance,
                source_name=(
                    "Viquipèdia catalana — "
                    "efemèrides del dia"
                ),
                source_url=source_url,
                score=score,
            )
        )

    candidates.sort(
        key=lambda item: (
            item.importance,
            item.score,
            item.year or -99999,
        ),
        reverse=True,
    )

    return [
        item.as_dict()
        for item in candidates
    ]


def _page_url(
    event: dict[str, Any],
    language: str,
    day: date,
) -> str:
    pages = event.get("pages") or []

    for page in pages:
        urls = page.get("content_urls") or {}
        desktop = urls.get("desktop") or {}

        if desktop.get("page"):
            return str(desktop["page"])

    return _date_page_url(day)


def _event_title(
    event: dict[str, Any],
) -> str:
    pages = event.get("pages") or []

    if (
        pages
        and pages[0].get("normalizedtitle")
    ):
        return _normalise(
            str(
                pages[0]["normalizedtitle"]
            )
        )

    if pages and pages[0].get("title"):
        return _normalise(
            str(
                pages[0]["title"]
            ).replace("_", " ")
        )

    text = _normalise(
        str(
            event.get("text")
            or "Efemèride històrica"
        )
    )

    return _short_title(text)


def _fetch_wikifeeds(
    day: date,
    language: str,
    kind: str,
) -> list[dict[str, Any]]:
    """
    Font de reserva.

    Només s'utilitza si la pàgina de la data no proporciona
    esdeveniments.
    """
    urls = [
        (
            "https://api.wikimedia.org/feed/v1/"
            f"wikipedia/{language}/onthisday/"
            f"{kind}/{day.month:02d}/{day.day:02d}"
        ),
        (
            f"https://{language}.wikipedia.org/"
            "api/rest_v1/feed/onthisday/"
            f"{kind}/{day.month:02d}/{day.day:02d}"
        ),
    ]

    last_error: Exception | None = None

    for url in urls:
        try:
            response = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                },
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


def _historical_text(
    raw_text: str,
    kind: str,
) -> str:
    text = _normalise(
        raw_text
    ).rstrip(".")

    if kind == "births":
        return f"naixia {text}."

    if kind == "deaths":
        return f"moria {text}."

    return text + "."


def _events_from_wikifeeds(
    day: date,
) -> list[dict[str, Any]]:
    candidates: list[DynamicEvent] = []
    seen: set[tuple[int | None, str]] = set()

    for kind in (
        "events",
        "births",
        "deaths",
    ):
        try:
            events = _fetch_wikifeeds(
                day,
                "ca",
                kind,
            )
        except Exception:
            continue

        for raw in events:
            source_text = _normalise(
                str(raw.get("text") or "")
            )

            if not source_text:
                continue

            pages = raw.get("pages") or []

            classification_text = (
                source_text
                + " "
                + " ".join(
                    " ".join(
                        str(
                            page.get(field, "")
                        )
                        for field in (
                            "title",
                            "normalizedtitle",
                            "description",
                            "extract",
                        )
                    )
                    for page in pages
                )
            )

            scope = classify_scope(
                classification_text
            )

            score = relevance_score(
                classification_text,
                len(pages),
            )

            year_value = raw.get("year")

            try:
                year = (
                    int(year_value)
                    if year_value is not None
                    else None
                )
            except (TypeError, ValueError):
                year = None

            text = _historical_text(
                source_text,
                kind,
            )

            key = (
                year,
                text.casefold(),
            )

            if key in seen:
                continue

            seen.add(key)

            if kind == "events":
                base_importance = 2
                maximum_importance = 4
            else:
                base_importance = 1
                maximum_importance = 3

            importance = max(
                base_importance,
                min(
                    maximum_importance,
                    2 + max(score, 0) // 6,
                ),
            )

            candidates.append(
                DynamicEvent(
                    year=year,
                    title=_event_title(raw),
                    text=text,
                    scope=scope,
                    territory=(
                        SCOPE_TERRITORY[scope]
                    ),
                    category=(
                        "historia_politica_geografia"
                        if kind == "events"
                        else kind
                    ),
                    importance=importance,
                    source_name=(
                        "Viquipèdia catalana — "
                        "Wikifeeds"
                    ),
                    source_url=_page_url(
                        raw,
                        "ca",
                        day,
                    ),
                    score=score,
                )
            )

    candidates.sort(
        key=lambda item: (
            item.importance,
            item.score,
        ),
        reverse=True,
    )

    return [
        item.as_dict()
        for item in candidates
    ]


def fetch_dynamic_events(
    day: date,
) -> list[dict[str, Any]]:
    """
    Recupera les efemèrides automàtiques.

    Ordre de fonts:

    1. Pàgina catalana de la data.
    2. Wikifeeds com a reserva.
    3. Retorna una llista buida només si fallen totes dues.
    """
    try:
        events = _events_from_date_page(
            day
        )
    except Exception:
        events = []

    if events:
        return events

    try:
        return _events_from_wikifeeds(
            day
        )
    except Exception:
        return []


def select_events(
    curated: list[dict[str, Any]],
    dynamic: list[dict[str, Any]],
    max_events: int = 4,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []

    used_keys: set[
        tuple[int | None, str]
    ] = set()

    def add_event(
        event: dict[str, Any],
    ) -> bool:
        key = (
            event.get("year"),
            str(
                event.get("title")
                or event.get("text")
                or ""
            ).casefold(),
        )

        if key in used_keys:
            return False

        item = dict(event)

        item.setdefault(
            "origin",
            (
                "curated"
                if event.get("verified") is True
                else "automatic"
            ),
        )

        selected.append(item)
        used_keys.add(key)

        return True

    # Primera volta:
    # una efemèride per àmbit,
    # en l'ordre CAT → ESP → EUR → GLOBAL.
    for scope in SCOPE_ORDER:
        curated_scope = [
            event
            for event in curated
            if (
                event.get("scope") == scope
                and event.get(
                    "verified",
                    False,
                )
            )
        ]

        curated_scope.sort(
            key=lambda event: (
                bool(event.get("featured")),
                int(
                    event.get(
                        "importance",
                        0,
                    )
                ),
            ),
            reverse=True,
        )

        dynamic_scope = [
            event
            for event in dynamic
            if event.get("scope") == scope
        ]

        dynamic_scope.sort(
            key=lambda event: (
                int(
                    event.get(
                        "importance",
                        0,
                    )
                ),
                int(
                    event.get(
                        "score",
                        0,
                    )
                ),
            ),
            reverse=True,
        )

        pool = (
            curated_scope
            or dynamic_scope
        )

        if pool:
            add_event(pool[0])

        if len(selected) >= max_events:
            return selected

    # Reserva:
    # encara que no s'hagin pogut cobrir els quatre àmbits,
    # mostra com a mínim dos fets si la font en té.
    minimum_visible = min(
        2,
        max_events,
    )

    if len(selected) < minimum_visible:
        remaining = sorted(
            [
                *curated,
                *dynamic,
            ],
            key=lambda event: (
                bool(
                    event.get("verified")
                ),
                bool(
                    event.get("featured")
                ),
                int(
                    event.get(
                        "importance",
                        0,
                    )
                ),
                int(
                    event.get(
                        "score",
                        0,
                    )
                ),
            ),
            reverse=True,
        )

        for event in remaining:
            add_event(event)

            if (
                len(selected)
                >= minimum_visible
                or len(selected)
                >= max_events
            ):
                break

    # Ordre final fix.
    order = {
        scope: index
        for index, scope
        in enumerate(SCOPE_ORDER)
    }

    selected.sort(
        key=lambda event: order.get(
            str(event.get("scope")),
            99,
        )
    )

    return selected[:max_events]

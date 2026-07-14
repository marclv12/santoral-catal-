from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import os
import re
from typing import Callable, Iterable
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER_AGENT = "BonDiaCatalunya/2.0 (+https://github.com/marclopezventura/bon-dia-catalunya)"
MONTHS = [
    "gener", "febrer", "marc", "abril", "maig", "juny",
    "juliol", "agost", "setembre", "octubre", "novembre", "desembre",
]


@dataclass(frozen=True)
class SantoralResult:
    saints: list[str]
    source_name: str
    source_url: str
    status: str = "live"


def _request(url: str) -> requests.Response:
    response = requests.get(
        url,
        timeout=25,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "ca,en;q=0.7"},
    )
    response.raise_for_status()
    return response


def _clean(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = re.sub(r"\s+", " ", item).strip(" .·-–—\n\t")
        value = re.sub(r"\s+,", ",", value)
        if not value:
            continue
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _looks_like_saint(text: str) -> bool:
    prefixes = (
        "sant ", "santa ", "sants ", "santes ", "beat ", "beata ",
        "beats ", "beates ", "mare de déu", "nostra senyora",
    )
    return text.casefold().startswith(prefixes)


def fetch_llaurado(day: date) -> SantoralResult:
    month = MONTHS[day.month - 1]
    # La pàgina diària és molt més estable que intentar tallar la pàgina mensual.
    url = f"https://www.llaurado.info/santoral/{month}/{day.day}/"
    soup = BeautifulSoup(_request(url).text, "html.parser")

    candidates: list[str] = []
    for node in soup.select("main a, article a, .entry-content a, .post-content a, li, h2, h3"):
        text = node.get_text(" ", strip=True)
        if _looks_like_saint(text):
            candidates.append(text)

    # Reserva per a canvis de plantilla.
    if not candidates:
        for line in soup.get_text("\n", strip=True).splitlines():
            if _looks_like_saint(line):
                candidates.append(line)

    saints = _clean(candidates)
    if not saints:
        raise ValueError("Llauradó no ha retornat cap sant")
    return SantoralResult(saints[:15], "Santoral Català — Llauradó", url)


def fetch_tarraconense(day: date) -> SantoralResult:
    # Font institucional de l'Església catòlica a Catalunya.
    url = (
        "https://santoral.tarraconense.cat/Calendari/"
        f"{day.year}/{day.month}/{day.day}"
    )
    soup = BeautifulSoup(_request(url).text, "html.parser")
    candidates: list[str] = []

    for node in soup.select("h1, h2, h3, article a, article li, main a, main li"):
        text = node.get_text(" ", strip=True)
        if _looks_like_saint(text):
            candidates.append(text)

    if not candidates:
        text = soup.get_text("\n", strip=True)
        candidates = [line for line in text.splitlines() if _looks_like_saint(line)]

    saints = _clean(candidates)
    if not saints:
        raise ValueError("La Tarraconense no ha retornat cap sant")
    return SantoralResult(saints[:12], "Conferència Episcopal Tarraconense", url)


def fetch_ecampmany(day: date) -> SantoralResult:
    # La portada mostra el dia corrent. La fem servir només quan coincideix amb la data sol·licitada.
    if day != date.today():
        raise ValueError("eCampmany només s'utilitza com a reserva per al dia corrent")
    url = "https://www.ecampmany.com/santoral/"
    soup = BeautifulSoup(_request(url).text, "html.parser")
    text = soup.get_text("\n", strip=True)
    candidates = [line for line in text.splitlines() if _looks_like_saint(line)]
    saints = _clean(candidates)
    if not saints:
        raise ValueError("eCampmany no ha retornat cap resultat")
    return SantoralResult(saints[:12], "Santoral català — eCampmany", url)



def _local_fallback(day: date) -> SantoralResult | None:
    path = Path(__file__).resolve().parents[2] / "data" / "santoral_fallback.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    entry = payload.get(day.strftime("%m-%d"))
    if not entry:
        return None
    return SantoralResult(
        list(entry["saints"]),
        entry.get("source_name", "Base local de santoral"),
        entry.get("source_url", "https://santoral.tarraconense.cat/Calendari"),
        status="cached",
    )

def get_santoral(day: date) -> SantoralResult:
    if os.getenv("DISABLE_LIVE_SOURCES") == "1":
        fallback = _local_fallback(day)
        if fallback:
            return fallback
        return SantoralResult(
            ["Santoral no consultat en mode de prova"],
            "Mode de prova",
            "https://santoral.tarraconense.cat/Calendari",
            status="offline",
        )

    # 1) El sant principal prové de la font institucional catalana.
    # 2) Llauradó només complementa amb noms secundaris del santoral popular.
    try:
        official = fetch_tarraconense(day)
        try:
            popular = fetch_llaurado(day)
            combined = _clean([*official.saints, *popular.saints])[:12]
            return SantoralResult(
                combined,
                "Conferència Episcopal Tarraconense · complement Llauradó",
                official.source_url,
            )
        except Exception:
            return official
    except Exception:
        pass

    fetchers: tuple[Callable[[date], SantoralResult], ...] = (
        fetch_llaurado,
        fetch_ecampmany,
    )
    for fetcher in fetchers:
        try:
            return fetcher(day)
        except Exception:
            continue

    fallback = _local_fallback(day)
    if fallback:
        return fallback
    return SantoralResult(
        ["Santoral temporalment no disponible"],
        "Consulta manual del santoral",
        "https://santoral.tarraconense.cat/Calendari",
        status="unavailable",
    )

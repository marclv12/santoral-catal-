from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
VALID_SCOPES = {"CAT", "ESP", "EUR", "GLOBAL"}
VALID_CATEGORIES = {
    "historia_politica", "geografia", "institucions", "guerra_i_diplomacia",
    "cultura", "ciencia", "societat", "historia_politica_geografia",
}


def fail(message: str) -> None:
    raise ValueError(message)


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_efemerides() -> int:
    payload = json.loads((DATA / "efemerides.json").read_text(encoding="utf-8"))
    total = 0
    ids: set[str] = set()
    for key, events in payload.items():
        if len(key) != 5 or key[2] != "-":
            fail(f"Clau de data incorrecta: {key}")
        if not isinstance(events, list):
            fail(f"{key}: s'esperava una llista")
        for index, event in enumerate(events):
            total += 1
            prefix = f"{key}[{index}]"
            for required in ("id", "title", "text", "scope", "territory", "category", "importance", "source_name", "source_url", "verified"):
                if required not in event:
                    fail(f"{prefix}: falta {required}")
            if event["id"] in ids:
                fail(f"ID duplicat: {event['id']}")
            ids.add(event["id"])
            if event["scope"] not in VALID_SCOPES:
                fail(f"{prefix}: àmbit invàlid {event['scope']}")
            if event["category"] not in VALID_CATEGORIES:
                fail(f"{prefix}: categoria invàlida {event['category']}")
            if not 1 <= int(event["importance"]) <= 5:
                fail(f"{prefix}: importància fora de rang")
            if not valid_url(event["source_url"]):
                fail(f"{prefix}: URL invàlida")
            if event["verified"] is not True:
                fail(f"{prefix}: una entrada de la base pròpia ha d'estar verificada")
    return total


if __name__ == "__main__":
    count = validate_efemerides()
    print(f"Dades correctes: {count} efemèrides verificades")

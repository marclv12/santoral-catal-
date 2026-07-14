from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from sources.santoral import fetch_tarraconense, fetch_llaurado

USER_AGENT = "BonDiaCatalunya/2.0 (+https://github.com/marclopezventura/bon-dia-catalunya)"


def main() -> None:
    today = datetime.now(ZoneInfo("Europe/Madrid")).date()
    working = []
    errors = []
    for fetcher in (fetch_tarraconense, fetch_llaurado):
        try:
            result = fetcher(today)
            working.append(f"{result.source_name}: {len(result.saints)} entrades")
        except Exception as exc:
            errors.append(f"{fetcher.__name__}: {exc}")
    if not working:
        raise RuntimeError("Cap font viva de santoral respon: " + " | ".join(errors))
    print("Santoral: " + " | ".join(working))

    url = f"https://ca.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month:02d}/{today.day:02d}"
    response = requests.get(url, timeout=25, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    response.raise_for_status()
    payload = response.json()
    print(f"Wikimedia On This Day: {len(payload.get('events') or [])} esdeveniments")


if __name__ == "__main__":
    main()

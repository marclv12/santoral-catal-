from __future__ import annotations

import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
message = (ROOT / "docs" / "message.html").read_text(encoding="utf-8")
token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
chat_ids = [item.strip() for item in os.environ["TELEGRAM_CHAT_ID"].split(",") if item.strip()]

if not token or not chat_ids:
    raise RuntimeError("Falten TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")

for chat_id in chat_ids:
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram ha rebutjat el missatge per a {chat_id}")
    print(f"Missatge enviat correctament a {chat_id}")

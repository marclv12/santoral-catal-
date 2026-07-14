from __future__ import annotations

import os
import sys
from typing import Any

import requests

API_BASE = "https://api.telegram.org"


def call_telegram(token: str, method: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE}/bot{token}/{method}",
        json=json or {},
        timeout=30,
    )
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Telegram ha retornat una resposta no vàlida ({response.status_code}).") from exc

    if not response.ok or not payload.get("ok"):
        description = payload.get("description", f"HTTP {response.status_code}")
        raise RuntimeError(f"Error de Telegram a {method}: {description}")
    return payload


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    raw_chat_ids = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    send_test = os.environ.get("SEND_TEST_MESSAGE", "false").lower() == "true"

    if not token:
        print("❌ No existeix el secret TELEGRAM_BOT_TOKEN.")
        return 1
    if not raw_chat_ids:
        print("❌ No existeix el secret TELEGRAM_CHAT_ID.")
        return 1

    chat_ids = [item.strip() for item in raw_chat_ids.split(",") if item.strip()]
    if not chat_ids:
        print("❌ TELEGRAM_CHAT_ID no conté cap identificador vàlid.")
        return 1

    bot = call_telegram(token, "getMe")["result"]
    print(f"✅ Token correcte: @{bot.get('username', 'sense_username')} ({bot.get('first_name', 'bot')}).")

    for chat_id in chat_ids:
        chat = call_telegram(token, "getChat", json={"chat_id": chat_id})["result"]
        label = chat.get("title") or " ".join(
            part for part in (chat.get("first_name"), chat.get("last_name")) if part
        ) or chat.get("username") or "xat sense nom"
        print(f"✅ Xat accessible: {label} · id {chat.get('id')} · tipus {chat.get('type')}.")

        if send_test:
            call_telegram(
                token,
                "sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": (
                        "✅ <b>Bon Dia Catalunya està connectat</b>\n\n"
                        "GitHub pot comunicar-se correctament amb aquest xat de Telegram. "
                        "Ara ja pots executar el workflow d’enviament complet."
                    ),
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            print(f"✅ Missatge de prova enviat a {chat_id}.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.RequestException as exc:
        print(f"❌ No s'ha pogut contactar amb Telegram: {exc}")
        raise SystemExit(1)
    except RuntimeError as exc:
        print(f"❌ {exc}")
        raise SystemExit(1)

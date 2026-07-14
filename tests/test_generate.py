from datetime import date
from unittest.mock import patch

from src.generate import build_payload, telegram_html
from src.sources.santoral import SantoralResult


def test_message_orders_scopes_and_is_in_catalan(monkeypatch):
    monkeypatch.setenv("DISABLE_DYNAMIC_SOURCES", "1")
    saint = SantoralResult(["Sant Camil de Lel·lis", "Sant Francesc Solano"], "Prova", "https://example.com")
    with patch("src.generate.get_santoral", return_value=saint):
        payload = build_payload(date(2026, 7, 14))
    message = telegram_html(payload)
    assert "🇪🇸 <b>Espanya</b>" in message
    assert "🇪🇺 <b>Europa</b>" in message
    assert "🌍 <b>Món</b>" in message
    assert message.index("🇪🇸") < message.index("🇪🇺") < message.index("🌍")
    assert "Sant Camil" in message

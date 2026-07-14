from src.sources.efemerides import classify_scope, select_events


def test_scope_classifier_prioritises_catalan_scope():
    assert classify_scope("El Parlament de Catalunya es reuneix a Barcelona") == "CAT"
    assert classify_scope("Les Corts d'Espanya es reuneixen a Madrid") == "ESP"
    assert classify_scope("Una revolució transforma França i Europa") == "EUR"
    assert classify_scope("Una missió arriba a Mart") == "GLOBAL"


def test_selection_uses_fixed_order_and_curated_priority():
    curated = [
        {"year": 1, "scope": "EUR", "title": "Europa", "importance": 5, "verified": True},
        {"year": 2, "scope": "CAT", "title": "Catalunya", "importance": 5, "verified": True},
    ]
    dynamic = [
        {"year": 3, "scope": "CAT", "title": "CAT automàtica", "importance": 4, "verified": False},
        {"year": 4, "scope": "ESP", "title": "Espanya", "importance": 4, "verified": False},
        {"year": 5, "scope": "GLOBAL", "title": "Món", "importance": 4, "verified": False},
    ]
    selected = select_events(curated, dynamic)
    assert [item["scope"] for item in selected] == ["CAT", "ESP", "EUR", "GLOBAL"]
    assert selected[0]["title"] == "Catalunya"
    assert selected[0]["origin"] == "curated"

from src.validate_data import validate_efemerides


def test_curated_database_is_valid():
    assert validate_efemerides() >= 20

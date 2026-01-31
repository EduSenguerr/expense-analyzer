import pytest
from expense_analyzer.validators import validate_month


def test_validate_month_ok() -> None:
    assert validate_month("2026-01") == "2026-01"


def test_validate_month_bad() -> None:
    with pytest.raises(ValueError):
        validate_month("2026/01")

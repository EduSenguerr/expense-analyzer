from datetime import date

from expense_analyzer.parser import Transaction
from expense_analyzer.analyze import detect_unusual_spending


def test_detect_unusual_spending_flags_large_outlier() -> None:
    # Category "Groceries" average will be around 40, then one 200 should be flagged
    txns = [
        Transaction(date(2026, 1, 1), "Whole Foods", -35.0),
        Transaction(date(2026, 1, 2), "Whole Foods", -45.0),
        Transaction(date(2026, 1, 3), "Whole Foods", -40.0),
        Transaction(date(2026, 1, 4), "Whole Foods", -200.0),
    ]

    alerts = detect_unusual_spending(txns)
    jan = alerts.get("2026-01", [])
    assert len(jan) == 1
    assert jan[0].amount == 200.0

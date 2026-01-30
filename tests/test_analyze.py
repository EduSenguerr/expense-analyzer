from datetime import date

from expense_analyzer.parser import Transaction
from expense_analyzer.analyze import build_monthly_summary


def test_build_monthly_summary_math() -> None:
    txns = [
        Transaction(posted_date=date(2026, 1, 1), description="Salary", amount=1000.0),
        Transaction(posted_date=date(2026, 1, 2), description="STARBUCKS", amount=-5.0),
        Transaction(posted_date=date(2026, 1, 3), description="RENT", amount=-400.0),
    ]

    summaries = build_monthly_summary(txns)
    s = summaries["2026-01"]

    assert s.income_total == 1000.0
    assert s.expense_total == 405.0
    assert s.net_total == 595.0

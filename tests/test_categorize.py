from expense_analyzer.parser import Transaction
from expense_analyzer.categorize import categorize_transaction
from datetime import date


def test_income_category_by_amount() -> None:
    txn = Transaction(posted_date=date(2026, 1, 1), description="Salary", amount=100.0)
    assert categorize_transaction(txn) == "Income"


def test_keyword_category() -> None:
    txn = Transaction(posted_date=date(2026, 1, 2), description="STARBUCKS #1234", amount=-5.0)
    assert categorize_transaction(txn) == "Coffee"

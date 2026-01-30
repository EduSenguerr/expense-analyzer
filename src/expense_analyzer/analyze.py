from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from collections import defaultdict

from expense_analyzer.parser import Transaction
from expense_analyzer.categorize import categorize_transaction


@dataclass(frozen=True)
class Summary:
    month: str  # YYYY-MM
    income_total: float
    expense_total: float
    net_total: float
    by_category: dict[str, float]


def month_key(d: date) -> str:
    """
    Convert a date to YYYY-MM (monthly bucket key).
    """
    return f"{d.year:04d}-{d.month:02d}"


def build_monthly_summary(transactions: list[Transaction]) -> dict[str, Summary]:
    """
    Build one Summary per month.

    Conventions:
    - Income: amount > 0
    - Expense: amount < 0 (stored as positive totals in expense_total and by_category)
    """
    # group transactions by month
    buckets: dict[str, list[Transaction]] = defaultdict(list)
    for txn in transactions:
        buckets[month_key(txn.posted_date)].append(txn)

    results: dict[str, Summary] = {}

    for month, txns in sorted(buckets.items()):
        income = 0.0
        expenses = 0.0
        by_cat: dict[str, float] = defaultdict(float)

        for txn in txns:
            cat = categorize_transaction(txn)

            if txn.amount > 0:
                income += txn.amount
            else:
                spent = abs(txn.amount)
                expenses += spent
                by_cat[cat] += spent

        net = income - expenses
        results[month] = Summary(
            month=month,
            income_total=round(income, 2),
            expense_total=round(expenses, 2),
            net_total=round(net, 2),
            by_category={k: round(v, 2) for k, v in sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)},
        )

    return results

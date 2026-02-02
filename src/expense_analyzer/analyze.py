from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from collections import defaultdict

from expense_analyzer.parser import Transaction
from expense_analyzer.categorize import categorize_transaction
from expense_analyzer.normalize import normalize_description


@dataclass(frozen=True)
class Summary:
    month: str  # YYYY-MM
    income_total: float
    expense_total: float
    net_total: float
    by_category: dict[str, float]

@dataclass(frozen=True)
class Alert:
    month: str
    category: str
    posted_date: str
    merchant: str
    amount: float
    reason: str


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


def detect_unusual_spending(
    transactions: list[Transaction],
    multiplier: float = 2.5,
    min_amount: float = 50.0,
    min_samples: int = 3,
) -> dict[str, list[Alert]]:
    """
    Detect unusually large expenses per month and category.

    Rule (v1):
    - Only expenses (amount < 0)
    - For each month+category, compute the average expense amount
    - Flag any single expense that is >= 2.5x the average and >= 50.00
    Returns a dict keyed by month -> list[Alert]
    """
    # Build month/category buckets of expense amounts
    buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
    expense_items: list[tuple[str, str, Transaction]] = []

    for txn in transactions:
        if txn.amount >= 0:
            continue

        month = month_key(txn.posted_date)
        category = categorize_transaction(txn)
        buckets[(month, category)].append(abs(txn.amount))
        expense_items.append((month, category, txn))

    # Compute averages
    avg_by_bucket: dict[tuple[str, str], float] = {}
    for key, values in buckets.items():
        avg_by_bucket[key] = sum(values) / len(values)

    # Detect outliers
    alerts_by_month: dict[str, list[Alert]] = defaultdict(list)
    for month, category, txn in expense_items:
        spent = abs(txn.amount)
        avg = avg_by_bucket[(month, category)]

        if spent >= min_amount and spent >= multiplier * avg and len(buckets[(month, category)]) >= min_samples:
            merchant = normalize_description(txn.description)
            alerts_by_month[month].append(
                Alert(
                    month=month,
                    category=category,
                    posted_date=str(txn.posted_date),
                    merchant=merchant,
                    amount=round(spent, 2),
                    reason=f"High spend vs category average (${avg:.2f})",
                )
            )

    return alerts_by_month


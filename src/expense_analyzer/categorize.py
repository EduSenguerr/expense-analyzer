from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from expense_analyzer.parser import Transaction
from expense_analyzer.normalize import normalize_description



@dataclass(frozen=True)
class CategoryRule:
    category: str
    keywords: tuple[str, ...]


DEFAULT_RULES: list[CategoryRule] = [
    CategoryRule(category="Income", keywords=("salary", "payroll", "deposit")),
    CategoryRule(category="Rent", keywords=("rent", "landlord")),
    CategoryRule(category="Groceries", keywords=("whole foods", "trader joe", "grocery", "supermarket")),
    CategoryRule(category="Coffee", keywords=("starbucks", "coffee")),
    CategoryRule(category="Transport", keywords=("uber", "lyft", "taxi", "bus", "metro")),
    CategoryRule(category="Subscriptions", keywords=("netflix", "spotify", "prime", "subscription")),
]


def categorize_description(description: str, rules: Iterable[CategoryRule] = DEFAULT_RULES) -> str:
    """
    Categorize a transaction description using keyword matching.

    Rules:
    - Keyword match is case-insensitive.
    - First matching rule wins.
    - If nothing matches, returns "Uncategorized".
    """
    text = description.strip().lower()

    for rule in rules:
        if any(keyword in text for keyword in rule.keywords):
            return rule.category

    return "Uncategorized"


def categorize_transaction(txn: Transaction) -> str:
    """
    Categorize a transaction.
    - Income is determined by amount > 0
    - Expenses use normalized merchant text for better matching
    """
    if txn.amount > 0:
        return "Income"

    merchant = normalize_description(txn.description)
    return categorize_description(merchant)

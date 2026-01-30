from __future__ import annotations

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from expense_analyzer.parser import load_transactions
from expense_analyzer.categorize import categorize_transaction
from expense_analyzer.analyze import build_monthly_summary


app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def preview(csv_path: Path) -> None:
    """
    Preview parsed transactions and inferred categories from a CSV file.
    """
    txns = load_transactions(csv_path)

    table = Table(title=f"Preview: {csv_path.name}")
    table.add_column("Date", style="bold")
    table.add_column("Amount", justify="right")
    table.add_column("Category")
    table.add_column("Description", overflow="fold")

    for txn in txns[:20]:
        category = categorize_transaction(txn)
        table.add_row(str(txn.posted_date), f"{txn.amount:.2f}", category, txn.description)

    console.print(table)
    console.print(f"[bold]Loaded:[/bold] {len(txns)} transactions")

@app.command()
def summary(csv_path: Path) -> None:
    """
    Print a monthly summary (income, expenses, net) and category breakdown.
    """
    txns = load_transactions(csv_path)
    summaries = build_monthly_summary(txns)

    for month, s in summaries.items():
        console.print(f"\n[bold]{month}[/bold]")
        console.print(f"Income:   [green]{s.income_total:.2f}[/green]")
        console.print(f"Expenses: [red]{s.expense_total:.2f}[/red]")
        console.print(f"Net:      [bold]{s.net_total:.2f}[/bold]")

        table = Table(title="Spending by category")
        table.add_column("Category")
        table.add_column("Total", justify="right")

        for cat, total in s.by_category.items():
            table.add_row(cat, f"{total:.2f}")

        console.print(table)



def main() -> None:
    app()


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from expense_analyzer.parser import load_transactions
from expense_analyzer.categorize import categorize_transaction
from expense_analyzer.analyze import build_monthly_summary
from expense_analyzer.reporting import ensure_reports_dir, write_monthly_summary_json
from expense_analyzer.validators import validate_month
from expense_analyzer.normalize import normalize_description
from expense_analyzer.analyze import detect_unusual_spending


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
    table.add_column("Merchant")
    table.add_column("Category")
    table.add_column("Description", overflow="fold")

    for txn in txns[:20]:
        merchant = normalize_description(txn.description)
        category = categorize_transaction(txn)
        table.add_row(str(txn.posted_date), f"{txn.amount:.2f}", merchant, category, txn.description)

    console.print(table)
    console.print(f"[bold]Loaded:[/bold] {len(txns)} transactions")

@app.command()
def summary(
    csv_path: Path,
    month: str = typer.Option("", "--month", help="Filter results to a specific month (YYYY-MM)."),
) -> None:
    """
    Print a monthly summary (income, expenses, net) and category breakdown.
    """
    txns = load_transactions(csv_path)
    summaries = build_monthly_summary(txns)

    if month:
        month = validate_month(month)
        if month not in summaries:
            available = ", ".join(summaries.keys()) or "(none)"
            raise typer.BadParameter(f"Month not found. Available months: {available}")
        summaries = {month: summaries[month]}

    for month_key, s in summaries.items():
        console.print(f"\n[bold]{month_key}[/bold]")
        console.print(f"Income:   [green]{s.income_total:.2f}[/green]")
        console.print(f"Expenses: [red]{s.expense_total:.2f}[/red]")
        console.print(f"Net:      [bold]{s.net_total:.2f}[/bold]")

        table = Table(title="Spending by category")
        table.add_column("Category")
        table.add_column("Total", justify="right")

        for cat, total in s.by_category.items():
            table.add_row(cat, f"{total:.2f}")

        console.print(table)


@app.command()
def report(
    csv_path: Path,
    out_dir: Path = typer.Option(Path("reports"), "--out-dir", help="Output directory for report files."),
    month: str = typer.Option("", "--month", help="Generate report for a specific month (YYYY-MM)."),
) -> None:
    """
    Generate JSON reports for each month found in the CSV.
    """
    txns = load_transactions(csv_path)
    summaries = build_monthly_summary(txns)

    if month:
        month = validate_month(month)
        if month not in summaries:
            available = ", ".join(summaries.keys()) or "(none)"
            raise typer.BadParameter(f"Month not found. Available months: {available}")
        summaries = {month: summaries[month]}

    reports_dir = ensure_reports_dir(out_dir)

    created = []
    for _month, s in summaries.items():
        out_path = write_monthly_summary_json(reports_dir, s)
        created.append(out_path)

    console.print(f"[bold green]Created {len(created)} report file(s):[/bold green]")
    for p in created:
        console.print(f"- {p}")


@app.command()
def alerts(
    csv_path: Path,
    month: str = typer.Option("", "--month", help="Filter alerts to a specific month (YYYY-MM)."),
    multiplier: float = typer.Option(2.5, "--multiplier", help="Alert threshold multiplier vs category average."),
    min_amount: float = typer.Option(50.0, "--min-amount", help="Minimum expense amount to consider for alerts."),
    min_samples: int = typer.Option(3, "--min-samples", help="Minimum number of samples in a category to enable alerts."),
) -> None:
    """
    Show unusually large expenses based on category averages.
    """
    txns = load_transactions(csv_path)
    alerts_by_month = detect_unusual_spending(
        txns,
        multiplier=multiplier,
        min_amount=min_amount,
        min_samples=min_samples,
    )

    if month:
        month = validate_month(month)
        alerts_by_month = {month: alerts_by_month.get(month, [])}

    any_alerts = False
    for month_key, alerts_list in alerts_by_month.items():
        if not alerts_list:
            continue

        any_alerts = True
        console.print(f"\n[bold red]Alerts — {month_key}[/bold red]")

        table = Table(title="Unusual spending")
        table.add_column("Date", style="bold")
        table.add_column("Category")
        table.add_column("Merchant")
        table.add_column("Amount", justify="right")
        table.add_column("Reason", overflow="fold")

        for a in alerts_list:
            table.add_row(a.posted_date, a.category, a.merchant, f"{a.amount:.2f}", a.reason)

        console.print(table)

    if not any_alerts:
        console.print("[green]No unusual spending detected.[/green]")



def main() -> None:
    app()


if __name__ == "__main__":
    main()

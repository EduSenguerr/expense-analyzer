from __future__ import annotations

from pathlib import Path
import typer
from rich import print

from expense_analyzer.parser import load_transactions

app = typer.Typer(add_completion=False)


@app.command()
def preview(csv_path: Path) -> None:
    """
    Preview the parsed transactions from a CSV file.
    """
    txns = load_transactions(csv_path)
    print(f"[bold]Loaded:[/bold] {len(txns)} transactions")
    for t in txns[:10]:
        print(f"- {t.posted_date} | {t.amount:>8.2f} | {t.description}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()

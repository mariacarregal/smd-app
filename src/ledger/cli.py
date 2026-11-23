"""Command line: parses the arguments, calls storage and reports, prints."""

import argparse
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ledger import db, reports, storage

DEFAULT_FILE = Path("data/transactions.csv")


def print_totals(totals: dict[str, Decimal]) -> None:
    for name, total in totals.items():
        print(f"{name:<10} {total:>10}")


def print_spending(spending: dict[str, Decimal]) -> None:
    table = Table(title="Spending by category")
    table.add_column("Category")
    table.add_column("EUR", justify="right")
    for category, total in spending.items():
        table.add_row(category, f"{total:,.2f}")
    Console().print(table)


def parse_amount(text: str) -> Decimal:
    """Turns text such as `-12.50` into a Decimal, for argparse."""
    try:
        return Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"not an amount: {text!r}") from None


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ledger", description="Balances and spending of your accounts."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    import_cmd = commands.add_parser("import", help="store a CSV file in the database")
    import_cmd.add_argument("file", nargs="?", type=Path, default=DEFAULT_FILE)

    add_cmd = commands.add_parser("add", help="record one transaction")
    add_cmd.add_argument("account")
    add_cmd.add_argument("amount", type=parse_amount)
    add_cmd.add_argument("category")
    add_cmd.add_argument("description")
    add_cmd.add_argument("--date", type=date.fromisoformat, default=date.today())

    commands.add_parser("balance", help="balance of each account")
    commands.add_parser("spending", help="spending by category")
    commands.add_parser("months", help="net amount of each month")
    return parser


def main() -> None:
    args = make_parser().parse_args()
    db.create_tables()
    with db.get_session() as session:
        try:
            if args.command == "import":
                count = storage.import_csv(session, args.file)
                print(f"Imported {count} transactions from {args.file}")
            elif args.command == "add":
                storage.add_transaction(
                    session,
                    args.account,
                    args.amount,
                    args.category,
                    args.description,
                    args.date,
                )
                print(f"Added {args.amount} to {args.account}")
            else:
                transactions = storage.load_transactions(session)
                if args.command == "balance":
                    print_totals(reports.balances(transactions))
                elif args.command == "months":
                    print_totals(reports.net_by_month(transactions))
                else:
                    print_spending(reports.spending_by_category(transactions))
        except ValueError as error:
            print(f"ledger: {error}", file=sys.stderr)
            sys.exit(1)

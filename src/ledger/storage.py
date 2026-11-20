"""Reading transactions from a CSV file and storing them in the database."""

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ledger.db import Account, TransactionRow
from ledger.models import Transaction


def read_csv(path: Path) -> list[Transaction]:
    """Returns one Transaction per row of the CSV file."""
    with open(path, newline="") as f:
        return [
            Transaction(
                date=date.fromisoformat(row["date"]),
                account=row["account"],
                description=row["description"],
                category=row["category"],
                amount=Decimal(row["amount"]),
            )
            for row in csv.DictReader(f)
        ]


def find_account(session: Session, name: str) -> Account | None:
    """The account with this name, or None if there is none."""
    return session.scalar(select(Account).where(Account.name == name))


def get_or_create_account(session: Session, name: str) -> Account:
    """The account with this name, created if it does not exist yet."""
    account = find_account(session, name)
    if account is None:
        account = Account(name=name)
        session.add(account)
    return account


def import_csv(session: Session, path: Path) -> int:
    """Stores every transaction of the CSV file in one commit. Returns the count."""
    transactions = read_csv(path)
    for t in transactions:
        session.add(
            TransactionRow(
                date=t.date,
                description=t.description,
                category=t.category,
                amount=t.amount,
                account=get_or_create_account(session, t.account),
            )
        )
    session.commit()
    return len(transactions)


def load_transactions(session: Session) -> list[Transaction]:
    """Every transaction stored in the database, oldest first."""
    rows = session.scalars(
        select(TransactionRow).order_by(TransactionRow.date, TransactionRow.id)
    )
    return [
        Transaction(
            date=row.date,
            account=row.account.name,
            description=row.description,
            category=row.category,
            amount=row.amount,
        )
        for row in rows
    ]


def add_transaction(
    session: Session,
    account_name: str,
    amount: Decimal,
    category: str,
    description: str,
    day: date,
) -> None:
    """Stores one transaction in an existing account."""
    account = find_account(session, account_name)
    if account is None:
        raise ValueError(f"there is no account called {account_name!r}")
    if amount != round(amount, 2):
        raise ValueError(f"{amount} has more than two decimals")
    session.add(
        TransactionRow(
            date=day,
            description=description,
            category=category,
            amount=amount,
            account=account,
        )
    )
    session.commit()
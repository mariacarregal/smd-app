"""Data types used by the ledger."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Transaction:
    """A single movement of money. Negative amounts are money going out."""

    date: date
    account: str
    description: str
    category: str
    amount: Decimal
"""The database: tables, column types, engine and sessions."""

import datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, String, create_engine, event
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
)
from sqlalchemy.types import TypeDecorator

DATABASE_URL = "sqlite:///ledger.db"


class Money(TypeDecorator):
    """Stores amounts as whole cents (INTEGER) and returns them as Decimal."""

    impl = Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return int(Decimal(value) * 100)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Decimal(value).scaleb(-2)


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    rows: Mapped[list[TransactionRow]] = relationship(back_populates="account")


class TransactionRow(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Money)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    account: Mapped[Account] = relationship(back_populates="rows")


engine = create_engine(DATABASE_URL)


@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    """SQLite only checks foreign keys when asked to, on every connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_tables() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)

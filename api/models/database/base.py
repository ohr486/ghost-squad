"""ベースモデルクラス."""
from datetime import datetime
from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """すべてのモデルの基底クラス."""

    pass


class TimestampMixin:
    """タイムスタンプフィールドのミックスイン."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    """共通フィールドを持つベースモデル."""

    __abstract__ = True

    # Note: Using Integer instead of BigInteger for SQLite compatibility in tests
    # PostgreSQL will handle this as BIGINT via Alembic migrations
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

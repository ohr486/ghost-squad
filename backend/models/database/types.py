"""
Custom SQLAlchemy types for cross-database compatibility
"""
from sqlalchemy import BigInteger, Integer, TypeDecorator


class BigIntegerID(TypeDecorator):
    """
    Platform-independent BigInteger ID type.
    Uses BigInteger for PostgreSQL and Integer for SQLite to ensure
    proper autoincrement.
    """

    impl = BigInteger
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            # SQLite needs INTEGER PRIMARY KEY for autoincrement
            return dialect.type_descriptor(Integer())
        else:
            # PostgreSQL and other databases use BigInteger
            return dialect.type_descriptor(BigInteger())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return int(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return int(value)

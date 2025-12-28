"""Database connection and session management."""
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# データベースURL取得
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gs_user:gs_password@db:5432/gs_db",
)

# SQLAlchemy エンジン作成
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    pool_pre_ping=True,  # 接続の有効性を確認
)

# セッションファクトリー作成
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """データベースセッションを取得する依存性注入関数.

    FastAPI の Depends で使用する。

    Yields:
        Session: SQLAlchemy セッション
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

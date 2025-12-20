import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Docker Composeで定義したDB接続情報
# (docker-compose.ymlの environment 設定と一致させる必要があります)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://ghost:ghost_password@db:5432/ghost_db"
)

# Docker Composeなどで "postgresql://" と指定されてしまっても、
# SQLAlchemyが asyncpg を使うように強制的に書き換える
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 非同期エンジンの作成
engine = create_async_engine(DATABASE_URL, echo=False)

# セッションファクトリの作成
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# モデル定義のベースクラス
Base = declarative_base()


# 依存性注入（Dependency Injection）用関数
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

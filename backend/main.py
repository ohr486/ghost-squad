from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import check_database_connection, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # Startup
    print("🚀 Starting Ghost Squad API...")

    # データベース接続確認
    if not check_database_connection():
        print("⚠️  Warning: Database connection failed during startup")
    else:
        print("✅ Database connection established")

    yield

    # Shutdown
    print("🛑 Shutting down Ghost Squad API...")


# FastAPIアプリケーションの作成
app = FastAPI(
    title="Ghost Squad API",
    description="GhostSquadのバックエンドAPI",
    version="0.0.1",
    lifespan=lifespan,
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ルートエンドポイント
@app.get("/")
async def root():
    return {"message": "Hello, GhostSquad"}


# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    db_status = check_database_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "service": "ghost-squad-backend",
        "database": "connected" if db_status else "disconnected",
    }


# APIの基本情報エンドポイント
@app.get("/api/info")
async def api_info():
    return {
        "name": "Ghost Squad API",
        "version": "0.0.1",
        "description": "GhostSquadのバックエンドAPI",
    }


# データベーステストエンドポイント
@app.get("/api/db-test")
async def db_test(db: Session = Depends(get_db)):
    """データベース接続とデータ確認用のテストエンドポイント"""
    from models.database.inquiry import InquiryModel

    try:
        inquiry_count = db.query(InquiryModel).count()
        return {
            "database_status": "connected",
            "inquiry_count": inquiry_count,
            "message": "Database connection successful",
        }
    except Exception as e:
        return {
            "database_status": "error",
            "error": str(e),
            "message": "Database connection failed",
        }

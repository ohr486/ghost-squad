from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from api.inquiries import router as inquiry_router
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
    description="GhostSquadのバックエンドAPI - ストーリーボード機能",
    version="0.0.1",
    lifespan=lifespan,
)

# CORS設定（フロントエンド連携用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React開発サーバー
        "http://127.0.0.1:3000",  # 代替ローカルホスト
        "http://frontend:3000",  # Docker内部通信
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# APIルーター設定（/api プレフィックス）
api_router = APIRouter(prefix="/api")

# Include inquiry router
api_router.include_router(inquiry_router)


# APIの基本情報エンドポイント
@api_router.get("/info", tags=["system"])
async def api_info():
    return {
        "name": "Ghost Squad API",
        "version": "0.0.1",
        "description": "GhostSquadのストーリーボード機能API",
    }


# ヘルスチェックエンドポイント（API用）
@api_router.get("/health", tags=["system"])
async def api_health_check():
    """API用ヘルスチェックエンドポイント"""
    db_status = check_database_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "service": "ghost-squad-backend",
        "database": "connected" if db_status else "disconnected",
    }


# データベーステストエンドポイント
@api_router.get("/db-test", tags=["system"])
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


# APIルーターをアプリケーションに追加
app.include_router(api_router)


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

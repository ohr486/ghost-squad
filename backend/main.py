from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FastAPIアプリケーションの作成
app = FastAPI(
    title="Ghost Squad API",
    description="GhostSquadのバックエンドAPI",
    version="0.0.1"
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
    return {"status": "healthy", "service": "ghost-squad-backend"}

# APIの基本情報エンドポイント
@app.get("/api/info")
async def api_info():
    return {
        "name": "Ghost Squad API",
        "version": "0.0.1",
        "description": "GhostSquadのバックエンドAPI"
    }
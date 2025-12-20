from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import services

# 内部モジュールのインポート
from database import Base, engine, get_db
from schemas import MissionSchema, TaskUpdate


# --- 起動時の初期化処理 (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時: テーブルが存在しなければ作成する
    async with engine.begin() as conn:
        # 開発用: 全テーブル作成（既存データは消えませんが、スキーマ変更時は注意）
        await conn.run_sync(Base.metadata.create_all)
    print(">>> Database Tables Created (if not existed).")
    yield
    # 終了時: 特になし


# --- fast api app ---
app = FastAPI(title="Ghost Brain API", version="1.0.0", lifespan=lifespan)


# CORS設定
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- データモデル ---
class Task(BaseModel):
    id: str
    title: str
    status: str
    assignee: Optional[str] = None
    energy: float


class MissionRequest(BaseModel):
    instruction: str


class MissionResponse(BaseModel):
    mission_id: str
    status: str
    logs: List[str]
    energy_used: float = 0.0
    tasks: List[Task] = []


@app.get("/")
async def root():
    return {"status": "online", "message": "Ghost-Squad Systems: Ready."}


# --- 1. ミッション開始 API ---
@app.post("/mission/start", response_model=MissionResponse)
async def start_mission(
    req: MissionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # 1. DBにミッションを作成
    mission = await services.create_mission(db, req.instruction)

    # 2. バックグラウンドでAI思考プロセスを開始
    # (注意: ここでDBセッションを渡すと閉じてしまうため、IDだけ渡して向こうで開くのが正解ですが
    #  簡易実装として、ここでの処理は「DB保存」までとし、AI処理の統合は次のステップで行います)

    # 暫定対応: レスポンスを返す
    return {
        "mission_id": mission.id,
        "status": mission.status,
        "logs": mission.logs,
        "tasks": [],
    }


# --- 2. 状況確認 API ---
@app.get("/mission/current", response_model=Optional[MissionResponse])
async def get_current_mission(db: AsyncSession = Depends(get_db)):
    # DBから最新のミッションを取得して返す
    mission = await services.get_latest_mission(db)

    if not mission:
        return None

    return {
        "mission_id": mission.id,
        "status": mission.status,
        "logs": mission.logs,
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "assignee": t.assignee,
                "energy": t.energy,
            }
            for t in mission.tasks
        ],
    }


# --- タスク更新 ---
@app.patch("/mission/tasks/{task_id}")
async def update_task_status(
    task_id: str, req: TaskUpdate, db: AsyncSession = Depends(get_db)
):
    """タスクのステータスを更新する (DB対応版)"""
    updated_task = await services.update_task_status(db, task_id, req.status)

    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")

    return updated_task


# --- 全てのミッションを取得 ---
@app.get("/missions", response_model=list[MissionSchema])
async def get_missions_history(db: AsyncSession = Depends(get_db)):
    """ミッションの履歴を取得する"""
    missions = await services.get_all_missions(db)
    return missions


# --- (オプション) メモリリセット用 ---
@app.post("/mission/reset")
async def reset_memory():
    global GHOST_SESSION
    GHOST_SESSION = {
        "mission_id": "RESET",
        "status": "online",
        "logs": ["--- MEMORY WIPED ---", "SYSTEM READY."],
        "energy_used": 0.0,
        "tasks": [],
    }
    return GHOST_SESSION

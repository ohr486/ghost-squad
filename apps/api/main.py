from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from database import engine, Base, get_db
from models import MissionModel, TaskModel

from agents.graph import ghost_brain

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

app = FastAPI(title="ghost-squad API", version="0.1.0")

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


class TaskUpdate(BaseModel):
    status: str


class MissionRequest(BaseModel):
    instruction: str


class MissionResponse(BaseModel):
    mission_id: str
    status: str
    logs: List[str]
    energy_used: float
    tasks: List[Task] = []


# --- ★セッションメモリ (Session Memory) ---
# サーバー起動中はここにデータを蓄積し続ける
GHOST_SESSION = {
    "mission_id": "INIT",
    "status": "online",
    "logs": [
        "SYSTEM BOOT SEQUENCE INITIATED...",
        "GHOST-MEMORY: INITIALIZED.",
        "READY FOR MULTI-MISSION EXECUTION.",
    ],
    "energy_used": 0.0,
    "tasks": [],
}


@app.get("/")
async def root():
    return {"status": "online", "message": "Ghost-Squad Systems: Ready."}


@app.post("/mission/start", response_model=MissionResponse)
async def start_mission(req: MissionRequest):
    # ミッションID生成 (簡易版)
    import uuid

    mission_id = f"msn-{str(uuid.uuid4())[:4]}"

    # ログに開始を記録
    GHOST_SESSION["logs"].append(f"--- MISSION START: {mission_id} ---")
    GHOST_SESSION["logs"].append(f"INSTRUCTION: {req.instruction}")

    # 思考の初期状態
    initial_state = {
        "mission_id": mission_id,
        "task_input": req.instruction,
        "current_plan": [],
        "logs": [],  # 思考ログ用の一時バッファ
        "status": "working",
        "energy_used": 0.0,
    }

    # AI脳の起動
    final_state = ghost_brain.invoke(initial_state)

    # --- ★データのマージ（累積）処理 ---

    # 1. ログの追記
    new_logs = final_state.get("logs", [])
    GHOST_SESSION["logs"].extend(new_logs)

    # 2. タスクの追記（ID衝突回避のためミッションIDを付与）
    new_tasks = final_state.get("current_plan", [])
    for task in new_tasks:
        # IDをユニークにする (例: msn-a1b2-t-1)
        task["id"] = f"{mission_id}-{task['id']}"
        GHOST_SESSION["tasks"].append(task)

    # 3. エナジー加算
    GHOST_SESSION["energy_used"] += final_state.get("energy_used", 0.0)

    # 4. ステータス更新
    GHOST_SESSION["mission_id"] = mission_id
    GHOST_SESSION["status"] = "idle"  # 処理が終わったのでアイドルに戻す

    # レスポンス生成（現在のセッション全体を返す）
    return GHOST_SESSION


# --- タスク更新 ---
@app.patch("/mission/tasks/{task_id}")
async def update_task_status(task_id: str, update: TaskUpdate):
    target_task = None
    for task in GHOST_SESSION["tasks"]:
        if task["id"] == task_id:
            target_task = task
            break

    if not target_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # ステータスを更新
    old_status = target_task["status"]
    target_task["status"] = update.status

    # ログにも記録（誰かが動かしたことがわかるように）
    if old_status != update.status:
        GHOST_SESSION["logs"].append(
            f"[COMMANDER] Override: Task {task_id} -> {update.status.upper()}"
        )

    return target_task


# --- 最新状態の取得 ---
@app.get("/mission/current", response_model=Optional[MissionResponse])
async def get_current_mission():
    return GHOST_SESSION


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

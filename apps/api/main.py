from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from agents.graph import ghost_brain

app = FastAPI(title="ghost-squad API", version="0.1.0")

# CORS設定：localhost:3000 からのアクセスを全許可する
origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS すべて許可
    allow_headers=["*"],
)

class MissionRequest(BaseModel):
    instruction: str

class MissionResponse(BaseModel):
    mission_id: str
    status: str
    logs: List[str]
    energy_used: float

class Task(BaseModel):
    id: str
    title: str
    status: str
    assignee: Optional[str] = None
    energy: float

class MissionResponse(BaseModel):
    mission_id: str
    status: str
    logs: List[str]
    energy_used: float
    tasks: List[Task] = [] # 追加

@app.get("/")
async def root():
    return {"status": "online", "message": "Ghost-Squad Systems: Ready."}

@app.post("/mission/start", response_model=MissionResponse)
async def start_mission(req: MissionRequest):
    """
    司令官からの指示を受け、LangGraphを起動する
    """
    # 思考の初期状態
    initial_state = {
        "mission_id": "msn-001",
        "task_input": req.instruction,
        "current_plan": [],
        "logs": [],
        "status": "idle",
        "energy_used": 0.0
    }
    
    # グラフを実行（invoke）
    # ※本来は非同期ストリーミング(astream)を使うが、まずは同期実行で確認
    final_state = ghost_brain.invoke(initial_state)
    
    return {
        "mission_id": final_state["mission_id"],
        "status": final_state["status"],
        "logs": final_state["logs"],
        "energy_used": final_state["energy_used"],
        "tasks": final_state.get("current_plan", []) # タスクリストを返す
    }


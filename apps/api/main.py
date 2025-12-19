from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

# 作成した脳をインポート
from agents.graph import ghost_brain

app = FastAPI(title="ghost-squad API", version="0.1.0")

class MissionRequest(BaseModel):
    instruction: str

class MissionResponse(BaseModel):
    mission_id: str
    status: str
    logs: List[str]
    energy_used: float

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
        "status": final_state["status"], # 多分 'done' になっているはず
        "logs": final_state["logs"],
        "energy_used": final_state["energy_used"]
    }

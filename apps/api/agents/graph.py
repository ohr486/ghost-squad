import time
import random
from langgraph.graph import StateGraph, END
from .state import AgentState

# --- ノード（思考の各ステップ）の定義 ---

def node_planner(state: AgentState):
    """作戦を立て、具体的なタスクカードを生成する"""
    print("--- [GHOST] Planning Phase ---")
    time.sleep(1.0)
    
    new_logs = state['logs'] + [f"司令官の指示「{state['task_input']}」を受領。"]
    
    # ダミーのタスクカードを生成
    generated_tasks = [
        {"id": "t-1", "title": "要件定義書の作成", "status": "done", "assignee": "planner", "energy": 0.01},
        {"id": "t-2", "title": "UIコンポーネント実装", "status": "working", "assignee": "tachikoma-01", "energy": 0.05},
        {"id": "t-3", "title": "APIエンドポイント接続", "status": "backlog", "assignee": None, "energy": 0.0}
    ]
    
    return {
        "status": "planning",
        "current_plan": generated_tasks, # ここにタスクが入る
        "logs": new_logs,
        "energy_used": state['energy_used'] + 0.02
    }

def node_worker(state: AgentState):
    """作戦を実行に移す（Workingフェーズ）"""
    print("--- [GHOST] Working Phase ---")
    
    time.sleep(2.0) # 作業時間を演出
    
    # ランダムなエージェントが発言する演出
    agent_name = random.choice(["tachikoma-01", "expert-coder", "ghost-lead"])
    log_msg = f"[{agent_name}] 並列化を開始。タスクを処理中... (Sync Rate: {random.randint(80, 99)}%)"
    
    return {
        "status": "working",
        "logs": state['logs'] + [log_msg],
        "energy_used": state['energy_used'] + 0.05
    }

def node_reporter(state: AgentState):
    """完了報告を行う（Doneフェーズ）"""
    print("--- [GHOST] Reporting Phase ---")
    
    return {
        "status": "done",
        "logs": state['logs'] + ["全タスク完了。ミッションコンプリート。"],
        "energy_used": state['energy_used']
    }

# --- グラフ（脳の配線）の構築 ---

workflow = StateGraph(AgentState)

# ノードを登録
workflow.add_node("planner", node_planner)
workflow.add_node("worker", node_worker)
workflow.add_node("reporter", node_reporter)

# エッジ（つながり）を定義
workflow.set_entry_point("planner") # 開始点
workflow.add_edge("planner", "worker")
workflow.add_edge("worker", "reporter")
workflow.add_edge("reporter", END)  # 終了点

# コンパイル（実行可能な脳にする）
ghost_brain = workflow.compile()

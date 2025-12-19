import os
import time
import random
from typing import List
from dotenv import load_dotenv

# LangChain / OpenAI 関連
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from .state import AgentState

# 環境変数の読み込み
load_dotenv()

# --- データ構造定義 ---
class TaskSchema(BaseModel):
    id: str = Field(description="Unique ID like t-1")
    title: str = Field(description="Task title")
    status: str = Field(description="Must be 'planning', 'working', or 'done'")
    assignee: str = Field(description="Agent name e.g. 'tachikoma-01'")
    energy: float = Field(description="Estimated cost in USD")

class PlanSchema(BaseModel):
    tasks: List[TaskSchema]

# --- LLM初期化 ---
llm = ChatOpenAI(
    model=os.getenv("GHOST_MODEL_NAME", "gpt-3.5-turbo"),
    temperature=0.7
)

# --- ノード: Planner (安全装置付き) ---
def node_planner(state: AgentState):
    print(f"--- [GHOST] Real Planning for: {state['task_input']} ---")
    
    generated_tasks = []
    log_msg = ""
    
    try:
        # LLMへの問い合わせを試みる
        parser = PydanticOutputParser(pydantic_object=PlanSchema)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are the 'Ghost-Squad' Commander AI. 
            Break down the user's instruction into 3-5 concrete technical tasks.
            Assign them to agents like 'tachikoma-01', 'expert-coder', 'security-bot'.
            
            {format_instructions}
            """),
            ("user", "{instruction}")
        ])
        
        chain = prompt | llm | parser
        
        result = chain.invoke({
            "instruction": state['task_input'],
            "format_instructions": parser.get_format_instructions()
        })
        
        generated_tasks = [task.dict() for task in result.tasks]
        log_msg = f"作戦立案完了。{len(generated_tasks)}個のタスクを展開しました。"

    except Exception as e:
        print(f"LLM Error: {e}")
        # --- 安全装置発動 ---
        # APIエラー時は、シミュレーション用のタスクを生成してアプリを止めない
        log_msg = "!!! 通信障害発生 (API Error) !!! バックアッププランを実行します。"
        generated_tasks = [
            {"id": "t-err-1", "title": "APIクレジット残高の確認", "status": "planning", "assignee": "commander", "energy": 0.0},
            {"id": "t-err-2", "title": "【Simulation】DBスキーマ設計", "status": "working", "assignee": "tachikoma-01", "energy": 0.01},
            {"id": "t-err-3", "title": "【Simulation】API実装", "status": "planning", "assignee": "backend-ghost", "energy": 0.02}
        ]

    return {
        "status": "planning",
        "current_plan": generated_tasks,
        "logs": state['logs'] + [log_msg],
        "energy_used": state['energy_used'] + 0.01
    }

# --- ノード: Worker ---
def node_worker(state: AgentState):
    print("--- [GHOST] Working Phase ---")
    
    # 時間経過の演出 (import time が必要)
    time.sleep(1.5) 
    
    agent_name = random.choice(["tachikoma-01", "expert-coder", "ghost-lead"])
    log_msg = f"[{agent_name}] 並列化を開始。タスクを処理中... (Sync Rate: {random.randint(80, 99)}%)"
    
    return {
        "status": "working",
        "logs": state['logs'] + [log_msg],
        "energy_used": state['energy_used'] + 0.05
    }

# --- ノード: Reporter ---
def node_reporter(state: AgentState):
    print("--- [GHOST] Reporting Phase ---")
    
    return {
        "status": "done",
        "logs": state['logs'] + ["Mission Complete."],
        "energy_used": state['energy_used']
    }

# --- グラフ構築 ---
workflow = StateGraph(AgentState)
workflow.add_node("planner", node_planner)
workflow.add_node("worker", node_worker)
workflow.add_node("reporter", node_reporter)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "worker")
workflow.add_edge("worker", "reporter")
workflow.add_edge("reporter", END)

ghost_brain = workflow.compile()

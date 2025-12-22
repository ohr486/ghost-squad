from typing import List, TypedDict, Dict, Any


class AgentState(TypedDict):
    """
    Ghost-Squadの共有メモリ構造体
    LangGraph内でこのStateがリレーのように渡されていきます。
    """

    mission_id: str
    task_input: str  # ユーザーからの曖昧な指示
    current_plan: List[Dict[str, Any]]  # AIが立てた作戦（WBS）

    # 思考ログ（UIのチャット欄に表示される内容）
    logs: List[str]

    # 現在の状況
    status: str  # 'planning', 'working', 'done'
    energy_used: float  # 消費コスト ($)

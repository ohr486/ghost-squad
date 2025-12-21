import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from agents.graph import ghost_brain
from models import MissionModel, TaskModel


async def create_mission(db: AsyncSession, instruction: str):
    """新しいミッションを作成してDBに保存"""
    new_mission = MissionModel(
        id=str(uuid.uuid4()),
        instruction=instruction,
        status="planning",
        logs=["Mission Created in DB"],
    )
    db.add(new_mission)
    await db.commit()
    await db.refresh(new_mission)
    return new_mission


async def run_agent_for_mission(db: AsyncSession, mission_id: str):
    """特定のミッションに対してエージェントを実行し、結果をDBに保存する"""
    # 1. ミッションを取得
    result = await db.execute(select(MissionModel).where(MissionModel.id == mission_id))
    mission = result.scalar_one_or_none()

    if not mission:
        print(f"❌ [System] Mission not found for agent execution: {mission_id}")
        return

    print(f"🚀 [System] Triggering Ghost Brain for Mission ID: {mission.id}")

    try:
        # --- エージェント実行 ---
        inputs = {
            "task_input": mission.instruction,
            "messages": [("user", mission.instruction)],
            "logs": [],
            "tasks": [],
            "energy_used": 0.0,
        }
        config = {"configurable": {"thread_id": str(mission.id)}}

        result = await ghost_brain.ainvoke(inputs, config=config)
        print(f"✅ [System] Ghost Brain Finished: {result}")

        # 1. ミッション本体の更新
        mission.status = "done"  # または result.get("status", "done")
        mission.logs = result.get("logs", [])

        # 2. タスクの保存
        current_plan = result.get("current_plan", [])
        for task_data in current_plan:
            new_task = TaskModel(
                id=task_data.get("id", str(uuid.uuid4())),
                title=task_data["title"],
                status=task_data["status"],
                assignee=task_data.get("assignee"),
                energy=task_data.get("energy", 0.0),
                mission_id=mission.id,
            )
            db.add(new_task)

        # 3. 変更を確定
        await db.commit()

    except Exception as e:
        print(f"❌ [System] Error running agent: {e}")
        # エラーが発生した場合、ミッションのステータスを 'error' に更新
        mission.status = "error"
        mission.logs.append(f"Agent Execution Error: {str(e)}")
        await db.commit()
        import traceback

        traceback.print_exc()


async def get_latest_mission(db: AsyncSession):
    """最新のミッションを取得（タスク情報付き）"""
    # 日付の新しい順に1件取得
    result = await db.execute(
        select(MissionModel)
        .options(selectinload(MissionModel.tasks))  # タスクも一緒にロード
        .order_by(MissionModel.created_at.desc())
        .limit(1)
    )
    mission = result.scalars().first()
    return mission


async def get_all_missions(db: AsyncSession, limit: int = 10):
    """すべてのミッションを新しい順に取得 (タスクも一緒に読み込む)"""
    stmt = (
        select(MissionModel)
        .options(selectinload(MissionModel.tasks))
        .order_by(MissionModel.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def save_tasks_to_db(db: AsyncSession, mission_id: str, tasks_data: list):
    """生成されたタスクリストをDBに保存"""
    for t in tasks_data:
        task = TaskModel(
            id=t.get("id", str(uuid.uuid4())),
            mission_id=mission_id,
            title=t["title"],
            status="pending",
            energy=t.get("energy", 0.0),
            assignee=t.get("assignee", "AI"),
        )
        db.add(task)
    await db.commit()


async def update_task_status(db: AsyncSession, task_id: str, status: str):
    stmt = select(TaskModel).where(TaskModel.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if task:
        task.status = status
        await db.commit()
        await db.refresh(task)
        return task
    return None


async def append_log_to_db(db: AsyncSession, mission_id: str, message: str):
    """ログを追記する"""
    result = await db.execute(select(MissionModel).where(MissionModel.id == mission_id))
    mission = result.scalars().first()
    if mission:
        # SQLAlchemyでJSONカラムを更新する際の作法（コピーして代入）
        new_logs = list(mission.logs)
        new_logs.append(message)
        mission.logs = new_logs
        await db.commit()


async def delete_mission(db: AsyncSession, mission_id: str) -> bool:
    """ミッションを削除する (成功したら True, 失敗/無しなら False)"""
    stmt = select(MissionModel).where(MissionModel.id == mission_id)
    result = await db.execute(stmt)
    mission = result.scalar_one_or_none()

    if mission:
        await db.delete(mission)
        await db.commit()
        return True
    return False

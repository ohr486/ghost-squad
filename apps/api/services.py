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

    print(f"🚀 [System] Triggering Ghost Brain for Mission ID: {new_mission.id}")

    # --- エージェント実行 (非同期で実行して結果を待つ場合) ---
    # ※ 本番では BackgroundTasks 推奨ですが、まずはここで動くか確認
    try:
        inputs = {
            "task_input": new_mission.instruction,
            "messages": [("user", new_mission.instruction)],
            "logs": [],
            "tasks": [],
            "energy_used": 0.0,
        }
        config = {"configurable": {"thread_id": str(new_mission.id)}}

        result = await ghost_brain.ainvoke(inputs, config=config)
        print(f"✅ [System] Ghost Brain Finished: {result}")

        # 1. ミッション本体の更新
        new_mission.status = "done"  # または result.get("status", "done")
        new_mission.logs = result.get("logs", [])

        # もしMissionModelに energy_used カラムがあれば更新
        if hasattr(new_mission, "energy_used"):
            new_mission.energy_used = result.get("energy_used", 0.0)

        # 2. タスクの保存 (TaskModelがあると仮定)
        current_plan = result.get("current_plan", [])
        for task_data in current_plan:
            new_task = TaskModel(
                id=str(uuid.uuid4()),
                title=task_data["title"],
                status=task_data["status"],
                assignee=task_data.get("assignee"),
                energy=task_data.get("energy", 0.0),
                mission_id=new_mission.id,  # 紐付け
            )
            db.add(new_task)

        # 3. 変更を確定 (コミット)
        await db.commit()
        await db.refresh(new_mission)

    except Exception as e:
        print(f"❌ [System] Error running agent: {e}")

        # debug用
        import traceback

        traceback.print_exc()

    return new_mission


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
    """すべてのミッションを新しい順に取得"""
    # created_at が無い場合は id などで並び替え
    stmt = select(MissionModel).order_by(MissionModel.created_at.desc()).limit(limit)
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

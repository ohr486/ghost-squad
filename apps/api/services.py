import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from models import MissionModel, TaskModel


async def create_mission(db: AsyncSession, title: str):
    """新しいミッションを作成してDBに保存"""
    new_mission = MissionModel(
        title=title, status="planning", logs=["Mission Created in DB"]
    )
    db.add(new_mission)
    await db.commit()
    await db.refresh(new_mission)
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

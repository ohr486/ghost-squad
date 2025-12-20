import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class MissionModel(Base):
    __tablename__ = "missions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, default="Untitled Mission")
    status = Column(String, default="planning") # planning, running, done
    logs = Column(JSON, default=list)           # ログの配列をJSONとして保存
    created_at = Column(DateTime, default=datetime.utcnow)

    # リレーション: Mission は複数の Task を持つ
    tasks = relationship("TaskModel", back_populates="mission", cascade="all, delete-orphan")

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String, ForeignKey("missions.id"))
    
    title = Column(String, nullable=False)
    status = Column(String, default="pending") # pending, working, done
    assignee = Column(String, default="AI")
    energy = Column(Float, default=0.0)
    
    # リレーション: Task は一つの Mission に属する
    mission = relationship("MissionModel", back_populates="tasks")

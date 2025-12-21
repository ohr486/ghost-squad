import pytest
import pytest_asyncio
from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models import MissionModel, TaskModel

# --- Async Test Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
AsyncTestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


# --- Async Test Fixtures ---
@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Fixture to create a new async database session for each test function.
    Creates all tables and drops them after the test.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncTestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def test_client(db_session: AsyncSession):
    """
    Fixture to create a TestClient with an overridden async database dependency.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


# --- API Endpoint Tests ---

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


async def test_get_missions_history_empty(test_client: TestClient):
    """
    Test GET /missions when no missions exist.
    """
    response = test_client.get("/missions")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_and_get_mission(test_client: TestClient, mocker):
    """
    Test creating a mission and verify the background task is added.
    """
    # Mock BackgroundTasks.add_task to verify it's called
    mock_add_task = mocker.patch.object(BackgroundTasks, "add_task")

    # 1. Create a mission
    payload = {"instruction": "First test mission"}
    response = test_client.post("/mission/start", json=payload)

    # 2. Assertions
    assert response.status_code == 200
    created_mission_data = response.json()
    mission_id = created_mission_data["mission_id"]

    assert created_mission_data["status"] == "planning"
    mock_add_task.assert_called_once()  # Verify the agent was scheduled

    # 3. Get mission history
    response = test_client.get("/missions")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["id"] == mission_id
    assert history[0]["instruction"] == "First test mission"

    # 4. Get current mission
    response = test_client.get("/mission/current")
    assert response.status_code == 200
    current_mission = response.json()
    assert current_mission["mission_id"] == mission_id


async def test_delete_mission(test_client: TestClient, db_session: AsyncSession):
    """
    Test deleting a mission.
    """
    # 1. Create a mission to delete
    mission = MissionModel(instruction="To be deleted")
    db_session.add(mission)
    await db_session.commit()
    await db_session.refresh(mission)
    mission_id = mission.id

    # 2. Delete the mission
    response = test_client.delete(f"/mission/{mission_id}")
    assert response.status_code == 204

    # 3. Verify it's gone
    response = test_client.get("/missions")
    assert response.json() == []

    # 4. Verify deleting a non-existent mission returns 404
    response = test_client.delete("/mission/non-existent-id")
    assert response.status_code == 404


async def test_update_task_status(test_client: TestClient, db_session: AsyncSession):
    """
    Test updating a task's status.
    """
    # 1. Create a mission and a task manually
    mission = MissionModel(instruction="Mission with a task")
    task = TaskModel(id="task-1", title="My test task", mission=mission)
    db_session.add(mission)
    await db_session.commit()
    await db_session.refresh(task)

    # 2. Update the task status
    response = test_client.patch(
        f"/mission/tasks/{task.id}", json={"status": "working"}
    )
    assert response.status_code == 200
    updated_task = response.json()
    assert updated_task["status"] == "working"

    # 3. Verify the change in the database
    db_task = await db_session.get(TaskModel, task.id)
    assert db_task.status == "working"

    # 4. Test updating a non-existent task
    response = test_client.patch(
        "/mission/tasks/non-existent-task", json={"status": "done"}
    )
    assert response.status_code == 404

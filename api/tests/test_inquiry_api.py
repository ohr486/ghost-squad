"""問い合わせAPI統合テスト.

要件6.3: APIエンドポイントの統合テストを作成する
- 問い合わせ作成APIのテスト（正常系、バリデーションエラー）
- 問い合わせ一覧APIのテスト（ページネーション、フィルタリング、ソート）
- 問い合わせ詳細APIのテスト（存在する/しない）
- 問い合わせ更新APIのテスト（正常系、バリデーションエラー）
- 承認APIのテスト（正常系、無効なステータス遷移）
- 却下APIのテスト（正常系、却下理由あり/なし、無効なステータス遷移）
"""
from datetime import datetime, timezone

import pytest
from database import get_db
from fastapi import status
from fastapi.testclient import TestClient
from main import app
from models.database.base import BaseModel
from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# テスト用データベースの設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_inquiry_api.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """テスト用データベースセッションを提供する."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """テストごとにデータベースをセットアップする."""
    BaseModel.metadata.create_all(bind=engine)
    yield
    BaseModel.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """テスト用データベースセッション."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_inquiry(db_session: Session):
    """テスト用の問い合わせを作成する."""
    inquiry = InquiryModel(
        user_id="test_user",
        content="ログイン機能が欲しい",
        source_system="manual",
        timestamp=datetime.now(timezone.utc),
        status=InquiryStatus.RECEIVED,
        inquiry_metadata={},
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return inquiry


# POST /api/inquiries - 問い合わせ作成API


def test_create_inquiry_success():
    """問い合わせ作成の正常系テスト."""
    # Arrange
    inquiry_data = {
        "user_id": "test_user",
        "content": "ログイン機能が欲しい",
        "source_system": "manual",
    }

    # Act
    response = client.post("/api/inquiries", json=inquiry_data)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_id"] == "test_user"
    assert data["content"] == "ログイン機能が欲しい"
    assert data["source_system"] == "manual"
    assert data["status"] == "received"
    assert "id" in data
    assert "timestamp" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_inquiry_validation_error_empty_content():
    """問い合わせ作成のバリデーションエラーテスト（content空）."""
    # Arrange
    inquiry_data = {
        "user_id": "test_user",
        "content": "",
        "source_system": "manual",
    }

    # Act
    response = client.post("/api/inquiries", json=inquiry_data)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_inquiry_validation_error_whitespace_only_content():
    """問い合わせ作成のバリデーションエラーテスト（content空白のみ）."""
    # Arrange
    inquiry_data = {
        "user_id": "test_user",
        "content": "   ",
        "source_system": "manual",
    }

    # Act
    response = client.post("/api/inquiries", json=inquiry_data)

    # Assert - Pydanticのバリデーションエラーなので422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_inquiry_validation_error_invalid_user_id():
    """問い合わせ作成のバリデーションエラーテスト（user_id不正）."""
    # Arrange
    inquiry_data = {
        "user_id": "invalid user!",  # 英数字とアンダースコアのみ許可
        "content": "ログイン機能が欲しい",
        "source_system": "manual",
    }

    # Act
    response = client.post("/api/inquiries", json=inquiry_data)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# GET /api/inquiries - 問い合わせ一覧API


def test_list_inquiries_success(sample_inquiry):
    """問い合わせ一覧取得の正常系テスト."""
    # Act
    response = client.get("/api/inquiries")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert "timestamp" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == sample_inquiry.id
    assert data["meta"]["page"] == 1
    assert data["meta"]["limit"] == 20
    assert data["meta"]["total"] == 1
    assert data["meta"]["has_next"] is False


def test_list_inquiries_pagination():
    """問い合わせ一覧のページネーションテスト."""
    # Arrange - 30件の問い合わせを作成
    db = TestingSessionLocal()
    for i in range(30):
        inquiry = InquiryModel(
            user_id=f"user_{i}",
            content=f"問い合わせ内容 {i}",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
            inquiry_metadata={},
        )
        db.add(inquiry)
    db.commit()
    db.close()

    # Act - ページ1を取得
    response = client.get("/api/inquiries?page=1&limit=10")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["page"] == 1
    assert data["meta"]["limit"] == 10
    assert data["meta"]["total"] == 30
    assert data["meta"]["has_next"] is True

    # Act - ページ2を取得
    response = client.get("/api/inquiries?page=2&limit=10")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["page"] == 2
    assert data["meta"]["has_next"] is True

    # Act - ページ3を取得
    response = client.get("/api/inquiries?page=3&limit=10")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["page"] == 3
    assert data["meta"]["has_next"] is False


def test_list_inquiries_status_filter(sample_inquiry):
    """問い合わせ一覧のステータスフィルタリングテスト."""
    # Arrange - 別のステータスの問い合わせを追加
    db = TestingSessionLocal()
    inquiry2 = InquiryModel(
        user_id="user2",
        content="別の問い合わせ",
        source_system="manual",
        timestamp=datetime.now(timezone.utc),
        status=InquiryStatus.TASK_WORKING,
        inquiry_metadata={},
    )
    db.add(inquiry2)
    db.commit()
    db.close()

    # Act - receivedのみフィルタ
    response = client.get("/api/inquiries?status=received")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["status"] == "received"

    # Act - task_workingのみフィルタ
    response = client.get("/api/inquiries?status=task_working")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["status"] == "task_working"

    # Act - 複数ステータスフィルタ
    response = client.get("/api/inquiries?status=received,task_working")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 2


def test_list_inquiries_user_id_filter():
    """問い合わせ一覧のuser_idフィルタリングテスト."""
    # Arrange
    db = TestingSessionLocal()
    inquiry1 = InquiryModel(
        user_id="user1",
        content="User1の問い合わせ",
        source_system="manual",
        timestamp=datetime.now(timezone.utc),
        status=InquiryStatus.RECEIVED,
        inquiry_metadata={},
    )
    inquiry2 = InquiryModel(
        user_id="user2",
        content="User2の問い合わせ",
        source_system="manual",
        timestamp=datetime.now(timezone.utc),
        status=InquiryStatus.RECEIVED,
        inquiry_metadata={},
    )
    db.add_all([inquiry1, inquiry2])
    db.commit()
    db.close()

    # Act
    response = client.get("/api/inquiries?user_id=user1")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["user_id"] == "user1"


def test_list_inquiries_sort():
    """問い合わせ一覧のソートテスト."""
    # Arrange
    db = TestingSessionLocal()
    inquiry1 = InquiryModel(
        user_id="user1",
        content="問い合わせ1",
        source_system="manual",
        timestamp=datetime.now(timezone.utc),
        status=InquiryStatus.RECEIVED,
        inquiry_metadata={},
    )
    inquiry2 = InquiryModel(
        user_id="user2",
        content="問い合わせ2",
        source_system="manual",
        timestamp=datetime.now(timezone.utc),
        status=InquiryStatus.RECEIVED,
        inquiry_metadata={},
    )
    db.add_all([inquiry1, inquiry2])
    db.commit()
    db.close()

    # Act - sort_byとsort_orderパラメータが受け入れられることを確認
    response_desc = client.get("/api/inquiries?sort_by=created_at&sort_order=desc")

    # Assert
    assert response_desc.status_code == status.HTTP_200_OK
    data_desc = response_desc.json()
    assert len(data_desc["data"]) == 2

    # Act - updated_atでソート
    response_updated = client.get("/api/inquiries?sort_by=updated_at&sort_order=asc")

    # Assert
    assert response_updated.status_code == status.HTTP_200_OK
    data_updated = response_updated.json()
    assert len(data_updated["data"]) == 2


# GET /api/inquiries/{id} - 問い合わせ詳細API


def test_get_inquiry_success(sample_inquiry):
    """問い合わせ詳細取得の正常系テスト."""
    # Act
    response = client.get(f"/api/inquiries/{sample_inquiry.id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == sample_inquiry.id
    assert data["user_id"] == "test_user"
    assert data["content"] == "ログイン機能が欲しい"
    assert data["status"] == "received"


def test_get_inquiry_not_found():
    """問い合わせ詳細取得の404エラーテスト."""
    # Act
    response = client.get("/api/inquiries/99999")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "errors" in data["detail"]


# PUT /api/inquiries/{id} - 問い合わせ更新API


def test_update_inquiry_success(sample_inquiry):
    """問い合わせ更新の正常系テスト."""
    # Arrange
    update_data = {
        "content": "更新されたログイン機能の要望",
        "source_system": "email",
    }

    # Act
    response = client.put(f"/api/inquiries/{sample_inquiry.id}", json=update_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == sample_inquiry.id
    assert data["content"] == "更新されたログイン機能の要望"
    assert data["source_system"] == "email"


def test_update_inquiry_partial_update(sample_inquiry):
    """問い合わせの部分更新テスト."""
    # Arrange - contentのみ更新
    update_data = {
        "content": "contentのみ更新",
    }

    # Act
    response = client.put(f"/api/inquiries/{sample_inquiry.id}", json=update_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "contentのみ更新"
    assert data["source_system"] == "manual"  # 元のまま


def test_update_inquiry_validation_error(sample_inquiry):
    """問い合わせ更新のバリデーションエラーテスト."""
    # Arrange - 空白のみのcontent
    update_data = {
        "content": "   ",
    }

    # Act
    response = client.put(f"/api/inquiries/{sample_inquiry.id}", json=update_data)

    # Assert - Pydanticのバリデーションエラーなので422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_inquiry_not_found():
    """問い合わせ更新の404エラーテスト."""
    # Arrange
    update_data = {
        "content": "更新",
    }

    # Act
    response = client.put("/api/inquiries/99999", json=update_data)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


# POST /api/inquiries/{id}/approve - 問い合わせ承認API


def test_approve_inquiry_success(sample_inquiry):
    """問い合わせ承認の正常系テスト."""
    # Act
    response = client.post(f"/api/inquiries/{sample_inquiry.id}/approve")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == sample_inquiry.id
    assert data["status"] == "task_working"


def test_approve_inquiry_invalid_state_transition(sample_inquiry):
    """問い合わせ承認の無効なステータス遷移テスト."""
    # Arrange - 既に承認済みにする
    db = TestingSessionLocal()
    inquiry = (
        db.query(InquiryModel).filter(InquiryModel.id == sample_inquiry.id).first()
    )
    inquiry.status = InquiryStatus.TASK_WORKING
    db.commit()
    db.close()

    # Act - 再度承認を試みる
    response = client.post(f"/api/inquiries/{sample_inquiry.id}/approve")

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert "errors" in data["detail"]


def test_approve_inquiry_not_found():
    """問い合わせ承認の404エラーテスト."""
    # Act
    response = client.post("/api/inquiries/99999/approve")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


# POST /api/inquiries/{id}/reject - 問い合わせ却下API


def test_reject_inquiry_success_with_reason(sample_inquiry):
    """問い合わせ却下の正常系テスト（却下理由あり）."""
    # Arrange
    reject_data = {
        "reason": "要件が不明確です",
    }

    # Act
    response = client.post(
        f"/api/inquiries/{sample_inquiry.id}/reject", json=reject_data
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == sample_inquiry.id
    assert data["status"] == "rejected"

    # 却下理由がメタデータに保存されていることを確認
    db = TestingSessionLocal()
    inquiry = (
        db.query(InquiryModel).filter(InquiryModel.id == sample_inquiry.id).first()
    )
    assert inquiry.inquiry_metadata["rejection"]["reason"] == "要件が不明確です"
    db.close()


def test_reject_inquiry_success_without_reason(sample_inquiry):
    """問い合わせ却下の正常系テスト（却下理由なし）."""
    # Act - 却下理由なし
    response = client.post(f"/api/inquiries/{sample_inquiry.id}/reject", json={})

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "rejected"


def test_reject_inquiry_invalid_state_transition(sample_inquiry):
    """問い合わせ却下の無効なステータス遷移テスト."""
    # Arrange - 既に却下済みにする
    db = TestingSessionLocal()
    inquiry = (
        db.query(InquiryModel).filter(InquiryModel.id == sample_inquiry.id).first()
    )
    inquiry.status = InquiryStatus.REJECTED
    db.commit()
    db.close()

    # Act - 再度却下を試みる
    response = client.post(f"/api/inquiries/{sample_inquiry.id}/reject", json={})

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT


def test_reject_inquiry_not_found():
    """問い合わせ却下の404エラーテスト."""
    # Act
    response = client.post("/api/inquiries/99999/reject", json={})

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND

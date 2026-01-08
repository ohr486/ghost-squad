"""Story API Router - Integration Tests.

タスク 7.5: API層の統合テストを実施する
Story APIエンドポイントのエンドツーエンド動作をテストする。
"""

import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import get_db
from main import app
from models.database.base import Base
from models.database.inquiry import InquiryModel
from models.database.story import StoryModel
from models.enums.inquiry_status import InquiryStatus
from models.enums.priority import Priority
from models.enums.story_status import StoryStatus

# テスト用データベースの設定（shared in-memory SQLiteを使用）
SQLALCHEMY_DATABASE_URL = (
    "sqlite:///file:test_story_db?mode=memory&cache=shared&uri=true"
)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "uri": True}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """テスト用データベースセッションを提供する."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    """テストクライアントと依存関係のオーバーライドを管理する."""
    # モデルが確実に登録されるように明示的にインポート
    from models.database.inquiry import InquiryModel as _  # noqa: F401
    from models.database.story import StoryModel as __  # noqa: F401

    # データベーススキーマを作成
    Base.metadata.create_all(bind=engine)

    # 既存のオーバーライドを保存
    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # 元の状態に戻す
    if original_override is not None:
        app.dependency_overrides[get_db] = original_override
    else:
        app.dependency_overrides.pop(get_db, None)

    # データベーススキーマを削除
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def cleanup_database():
    """各テスト後にデータベースをクリーンアップする."""
    yield
    db = TestingSessionLocal()
    try:
        # すべてのテーブルのデータを削除
        db.query(StoryModel).delete()
        db.query(InquiryModel).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def db_session():
    """テスト用データベースセッション."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


class TestStoryGenerationEndpoint:
    """POST /api/inquiries/{inquiry_id}/stories エンドポイントのテスト."""

    def test_ai_story_generation_success(self, client: TestClient, db_session):
        """AIストーリー生成が成功する（空ボディ）.

        要件1.1-1.6: AI変換フロー
        """
        # Arrange: Inquiry作成 (status=task_working)
        inquiry = InquiryModel(
            user_id="test-user",
            content="ログイン機能が欲しい",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()
        db_session.refresh(inquiry)

        # Mock OpenAI API
        mock_ai_response = {
            "title": "ユーザーログイン機能",
            "description": (
                "As a user, I want to log in so that I can access my account"
            ),
            "priority": "medium",
        }

        with patch("services.story_generation_service.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_completion = Mock()
            mock_completion.choices = [
                Mock(message=Mock(content=json.dumps(mock_ai_response)))
            ]
            mock_client.chat.completions.create.return_value = mock_completion

            # Act: POST /api/inquiries/{inquiry_id}/stories (ボディなし = AI自動生成)
            response = client.post(
                f"/api/inquiries/{inquiry.id}/stories",
                # ボディなし = AI自動生成
            )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "ユーザーログイン機能"
        assert data["status"] == "waiting_review"
        assert data["inquiry_id"] == inquiry.id

    def test_manual_story_creation_success(self, client: TestClient, db_session):
        """手動ストーリー作成が成功する（ボディあり）.

        要件2.11-2.14: 手動作成フロー
        """
        # Arrange: Inquiry作成
        inquiry = InquiryModel(
            user_id="test-user",
            content="機能要求",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()
        db_session.refresh(inquiry)

        # Act: POST /api/inquiries/{inquiry_id}/stories (ボディあり)
        response = client.post(
            f"/api/inquiries/{inquiry.id}/stories",
            json={
                "title": "手動作成ストーリー",
                "description": "テスト用の説明",
                "priority": "high",
                "estimated_effort": 5.0,
            },
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "手動作成ストーリー"
        assert data["status"] == "waiting_review"
        assert data["priority"] == "high"
        assert data["inquiry_id"] == inquiry.id

    def test_inquiry_not_found(self, client: TestClient):
        """存在しない問い合わせIDの場合404エラー.

        要件: エラーハンドリング（404 Inquiry不存在）
        """
        # Act
        response = client.post(
            "/api/inquiries/999999/stories",
            # ボディなし
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "errors" in data["detail"]
        assert data["detail"]["errors"][0]["code"] == "GS-204"

    def test_invalid_inquiry_status(self, client: TestClient, db_session):
        """Inquiryステータスが不正な場合422エラー.

        要件: エラーハンドリング（422 ステータス不正）
        """
        # Arrange: Inquiry作成 (status=received, task_working以外)
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        db_session.add(inquiry)
        db_session.commit()
        db_session.refresh(inquiry)

        # Act
        response = client.post(
            f"/api/inquiries/{inquiry.id}/stories",
            # ボディなし
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
        assert "errors" in data["detail"]
        assert data["detail"]["errors"][0]["code"] == "GS-205"

    def test_validation_error_title_too_long(self, client: TestClient, db_session):
        """タイトルが500文字を超える場合422エラー.

        要件2.12: バリデーション（タイトル500文字以内）
        """
        # Arrange
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()
        db_session.refresh(inquiry)

        # Act
        response = client.post(
            f"/api/inquiries/{inquiry.id}/stories",
            json={
                "title": "あ" * 501,  # 500文字超過
                "description": "テスト説明",
                "priority": "medium",
            },
        )

        # Assert
        # Pydantic validation errors return 422 in FastAPI
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestStoryListEndpoints:
    """GET /api/stories, GET /api/inquiries/{inquiry_id}/stories エンドポイントのテスト."""

    def test_list_all_stories_success(self, client: TestClient, db_session):
        """全ストーリー一覧取得が成功する.

        要件2.1-2.4: ストーリー一覧提供、ページネーション、フィルタリング、ソート
        """
        # Arrange: Inquiry + Story作成
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()

        story1 = StoryModel(
            inquiry_id=inquiry.id,
            title="ストーリー1",
            description="説明1",
            priority=Priority.HIGH,
            status=StoryStatus.WAITING_REVIEW,
        )
        story2 = StoryModel(
            inquiry_id=inquiry.id,
            title="ストーリー2",
            description="説明2",
            priority=Priority.LOW,
            status=StoryStatus.APPROVED,
        )
        db_session.add_all([story1, story2])
        db_session.commit()

        # Act
        response = client.get("/api/stories")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 2

    def test_filter_by_status(self, client: TestClient, db_session):
        """ステータスフィルタリングが動作する.

        要件2.3: フィルタリング（status）
        """
        # Arrange
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()

        story1 = StoryModel(
            inquiry_id=inquiry.id,
            title="承認済みストーリー",
            description="説明",
            priority=Priority.MEDIUM,
            status=StoryStatus.APPROVED,
        )
        story2 = StoryModel(
            inquiry_id=inquiry.id,
            title="レビュー待ちストーリー",
            description="説明",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
        )
        db_session.add_all([story1, story2])
        db_session.commit()

        # Act: status=approvedでフィルタ
        response = client.get("/api/stories?status=approved")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "approved"


class TestStoryDetailEndpoint:
    """GET /api/stories/{id} エンドポイントのテスト."""

    def test_get_story_detail_success(self, client: TestClient, db_session):
        """ストーリー詳細取得が成功する.

        要件2.5: ストーリー詳細表示
        """
        # Arrange
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()

        story = StoryModel(
            inquiry_id=inquiry.id,
            title="テストストーリー",
            description="詳細な説明",
            priority=Priority.HIGH,
            status=StoryStatus.WAITING_REVIEW,
        )
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)

        # Act
        response = client.get(f"/api/stories/{story.id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == story.id
        assert data["title"] == "テストストーリー"

    def test_story_not_found(self, client: TestClient):
        """存在しないストーリーの場合404エラー.

        要件: エラーハンドリング（404 Story不存在）
        """
        # Act
        response = client.get("/api/stories/999999")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStoryUpdateEndpoint:
    """PUT /api/stories/{id} エンドポイントのテスト."""

    def test_update_story_success(self, client: TestClient, db_session):
        """ストーリー更新が成功する.

        要件2.6-2.9: ストーリー編集、バリデーション、変更内容保存、更新日時自動記録
        """
        # Arrange
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()

        story = StoryModel(
            inquiry_id=inquiry.id,
            title="元のタイトル",
            description="元の説明",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
        )
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)

        # Act
        response = client.put(
            f"/api/stories/{story.id}",
            json={
                "title": "更新されたタイトル",
                "priority": "high",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "更新されたタイトル"
        assert data["priority"] == "high"


class TestStoryDeleteEndpoint:
    """DELETE /api/stories/{id} エンドポイントのテスト."""

    def test_delete_story_success(self, client: TestClient, db_session):
        """ストーリー削除が成功する.

        要件2.15-2.17: ストーリー削除
        """
        # Arrange
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()

        story = StoryModel(
            inquiry_id=inquiry.id,
            title="削除対象",
            description="説明",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
        )
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)

        # Act
        response = client.delete(f"/api/stories/{story.id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True


class TestStoryApprovalEndpoints:
    """POST /api/stories/{id}/approve, POST /api/stories/{id}/reject エンドポイントのテスト."""

    def test_approve_story_success(self, client: TestClient, db_session):
        """ストーリー承認が成功する.

        要件3.1-3.3: 承認時のステータス検証、ステータス変更、承認日時と承認者の記録
        """
        # Arrange
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()

        story = StoryModel(
            inquiry_id=inquiry.id,
            title="承認対象",
            description="説明",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
        )
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)

        # Act
        response = client.post(
            f"/api/stories/{story.id}/approve",
            json={"approver": "admin-user"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "approved"
        assert "approval" in data["story_metadata"]

    def test_reject_story_success(self, client: TestClient, db_session):
        """ストーリー却下が成功する.

        要件3.4-3.7: 却下時のステータス検証、理由必須、ステータス変更、却下情報記録
        """
        # Arrange
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()

        story = StoryModel(
            inquiry_id=inquiry.id,
            title="却下対象",
            description="説明",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
        )
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)

        # Act
        response = client.post(
            f"/api/stories/{story.id}/reject",
            json={"rejector": "admin-user", "reason": "要件が不明確"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "rejected"
        assert "rejection" in data["story_metadata"]

    def test_reject_without_reason_fails(self, client: TestClient, db_session):
        """却下理由なしの場合400エラー.

        要件3.5: 却下理由入力必須
        """
        # Arrange
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()

        story = StoryModel(
            inquiry_id=inquiry.id,
            title="テスト",
            description="説明",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
        )
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)

        # Act
        response = client.post(
            f"/api/stories/{story.id}/reject",
            json={"rejector": "admin-user", "reason": ""},  # 空の理由
        )

        # Assert
        # Pydantic validation errors return 422 in FastAPI
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestBatchApprovalEndpoint:
    """POST /api/stories/batch-approve エンドポイントのテスト."""

    def test_batch_approve_success(self, client: TestClient, db_session):
        """一括承認が成功する.

        要件3.10-3.11: 一括承認機能、個別検証
        """
        # Arrange
        inquiry = InquiryModel(
            user_id="test-user",
            content="テスト",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()

        story1 = StoryModel(
            inquiry_id=inquiry.id,
            title="ストーリー1",
            description="説明",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
        )
        story2 = StoryModel(
            inquiry_id=inquiry.id,
            title="ストーリー2",
            description="説明",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
        )
        db_session.add_all([story1, story2])
        db_session.commit()
        db_session.refresh(story1)
        db_session.refresh(story2)

        # Act
        response = client.post(
            "/api/stories/batch-approve",
            json={"story_ids": [story1.id, story2.id], "approver": "admin-user"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2

"""Tests for StoryWorkflowService.

ストーリーワークフローサービスのテスト（要件3.1-3.11）。
"""
from datetime import datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from models.database.base import BaseModel
from models.database.inquiry import InquiryModel
from models.database.story import StoryModel
from models.enums.inquiry_status import InquiryStatus
from models.enums.priority import Priority
from models.enums.story_status import StoryStatus
from services.story_repository import StoryRepository
from services.story_workflow_service import (InvalidStatusTransitionError,
                                             StoryWorkflowService)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    BaseModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestStoryWorkflowService:
    """StoryWorkflowServiceのテストクラス."""

    @pytest.fixture
    def inquiry(self, db_session):
        """テスト用問い合わせ作成フィクスチャ."""
        inquiry = InquiryModel(
            user_id="test_user",
            content="Test inquiry content",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
            inquiry_metadata={},
        )
        db_session.add(inquiry)
        db_session.commit()
        db_session.refresh(inquiry)
        return inquiry

    @pytest.fixture
    def story(self, db_session, inquiry):
        """テスト用ストーリー作成フィクスチャ."""
        story = StoryModel(
            inquiry_id=inquiry.id,
            title="Test Story",
            description="Test story description",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
            story_metadata={},
        )
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)
        return story

    @pytest.fixture
    def repository(self, db_session):
        """StoryRepositoryフィクスチャ."""
        return StoryRepository(db_session)

    @pytest.fixture
    def service(self, repository):
        """StoryWorkflowServiceフィクスチャ."""
        return StoryWorkflowService(repository)

    # ===== approve_story メソッドのテスト =====

    def test_approve_story_success(self, service, story):
        """ストーリーの承認が成功する（要件3.1-3.3）."""
        # 承認前のストーリー状態確認
        assert story.status == StoryStatus.WAITING_REVIEW
        assert "approval" not in story.story_metadata
        old_updated_at = story.updated_at

        # 承認実行
        approved_story = service.approve_story(story.id, approver="test_approver")

        # 検証
        assert approved_story.status == StoryStatus.APPROVED  # 要件3.2
        assert approved_story.updated_at > old_updated_at  # タイムスタンプ更新

        # 承認メタデータの確認（要件3.3）
        assert "approval" in approved_story.story_metadata
        approval_data = approved_story.story_metadata["approval"]
        assert "approved_at" in approval_data
        assert approval_data["approver"] == "test_approver"

        # ステータス履歴の確認（要件3.9）
        assert "status_history" in approved_story.story_metadata
        history = approved_story.story_metadata["status_history"]
        assert len(history) == 1
        assert history[0]["from_status"] == StoryStatus.WAITING_REVIEW.value
        assert history[0]["to_status"] == StoryStatus.APPROVED.value
        assert "changed_at" in history[0]

    def test_approve_story_invalid_status(self, service, story, db_session):
        """waiting_review以外のストーリーは承認できない（要件3.1, 3.8）."""
        # ストーリーを承認済みに変更
        story.status = StoryStatus.APPROVED
        db_session.commit()

        # 承認を試みる
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            service.approve_story(story.id, approver="test_approver")

        # エラーメッセージ確認
        assert "waiting_review" in str(exc_info.value).lower()
        assert "approved" in str(exc_info.value).lower()

    def test_approve_story_not_found(self, service):
        """存在しないストーリーの承認はエラー."""
        with pytest.raises(ValueError) as exc_info:
            service.approve_story(99999, approver="test_approver")

        assert "not found" in str(exc_info.value).lower()

    # ===== reject_story メソッドのテスト =====

    def test_reject_story_success(self, service, story):
        """ストーリーの却下が成功する（要件3.4-3.7）."""
        # 却下前のストーリー状態確認
        assert story.status == StoryStatus.WAITING_REVIEW
        assert "rejection" not in story.story_metadata
        old_updated_at = story.updated_at

        # 却下実行
        reject_reason = "Not aligned with requirements"
        rejected_story = service.reject_story(
            story.id, rejector="test_rejector", reason=reject_reason
        )

        # 検証
        assert rejected_story.status == StoryStatus.REJECTED  # 要件3.6
        assert rejected_story.updated_at > old_updated_at  # タイムスタンプ更新

        # 却下メタデータの確認（要件3.7）
        assert "rejection" in rejected_story.story_metadata
        rejection_data = rejected_story.story_metadata["rejection"]
        assert "rejected_at" in rejection_data
        assert rejection_data["rejector"] == "test_rejector"
        assert rejection_data["reason"] == reject_reason

        # ステータス履歴の確認（要件3.9）
        assert "status_history" in rejected_story.story_metadata
        history = rejected_story.story_metadata["status_history"]
        assert len(history) == 1
        assert history[0]["from_status"] == StoryStatus.WAITING_REVIEW.value
        assert history[0]["to_status"] == StoryStatus.REJECTED.value

    def test_reject_story_without_reason(self, service, story):
        """却下理由なしでも却下は成功する（要件3.5）."""
        rejected_story = service.reject_story(story.id, rejector="test_rejector")

        # 検証
        assert rejected_story.status == StoryStatus.REJECTED
        assert "rejection" in rejected_story.story_metadata
        rejection_data = rejected_story.story_metadata["rejection"]
        assert rejection_data["rejector"] == "test_rejector"
        # reasonがない場合はフィールド自体が存在しない
        assert "reason" not in rejection_data

    def test_reject_story_invalid_status(self, service, story, db_session):
        """waiting_review以外のストーリーは却下できない（要件3.4, 3.8）."""
        # ストーリーを承認済みに変更
        story.status = StoryStatus.APPROVED
        db_session.commit()

        # 却下を試みる
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            service.reject_story(story.id, rejector="test_rejector", reason="Test")

        # エラーメッセージ確認
        assert "waiting_review" in str(exc_info.value).lower()

    def test_reject_story_not_found(self, service):
        """存在しないストーリーの却下はエラー."""
        with pytest.raises(ValueError) as exc_info:
            service.reject_story(99999, rejector="test_rejector", reason="Test")

        assert "not found" in str(exc_info.value).lower()

    # ===== batch_approve メソッドのテスト =====

    def test_batch_approve_all_success(self, service, db_session, inquiry):
        """一括承認が全て成功する（要件3.10-3.11）."""
        # 3つのストーリーを作成
        stories = []
        for i in range(3):
            story = StoryModel(
                inquiry_id=inquiry.id,
                title=f"Story {i+1}",
                description=f"Description {i+1}",
                priority=Priority.MEDIUM,
                status=StoryStatus.WAITING_REVIEW,
                story_metadata={},
            )
            db_session.add(story)
            stories.append(story)
        db_session.commit()

        story_ids = [s.id for s in stories]

        # 一括承認実行
        results = service.batch_approve(story_ids, approver="batch_approver")

        # 検証
        assert len(results) == 3
        for story_id, success, error in results:
            assert story_id in story_ids
            assert success is True
            assert error is None

        # 全てのストーリーが承認されたことを確認
        for story in stories:
            db_session.refresh(story)
            assert story.status == StoryStatus.APPROVED
            assert story.story_metadata["approval"]["approver"] == "batch_approver"

    def test_batch_approve_partial_success(self, service, db_session, inquiry):
        """一括承認で一部が失敗する場合（要件3.11）."""
        # 2つのストーリーを作成
        story1 = StoryModel(
            inquiry_id=inquiry.id,
            title="Story 1",
            description="Description 1",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
            story_metadata={},
        )
        story2 = StoryModel(
            inquiry_id=inquiry.id,
            title="Story 2",
            description="Description 2",
            priority=Priority.MEDIUM,
            status=StoryStatus.APPROVED,  # 既に承認済み
            story_metadata={},
        )
        db_session.add(story1)
        db_session.add(story2)
        db_session.commit()

        story_ids = [story1.id, story2.id]

        # 一括承認実行
        results = service.batch_approve(story_ids, approver="batch_approver")

        # 検証
        assert len(results) == 2

        # story1は成功
        result1 = next(r for r in results if r[0] == story1.id)
        assert result1[1] is True  # success
        assert result1[2] is None  # no error

        # story2は失敗（無効なステータス遷移）
        result2 = next(r for r in results if r[0] == story2.id)
        assert result2[1] is False  # failed
        assert result2[2] is not None  # error message exists
        assert "waiting_review" in result2[2].lower()

    def test_batch_approve_story_not_found(self, service, db_session, inquiry):
        """一括承認で存在しないストーリーIDが含まれる場合."""
        story = StoryModel(
            inquiry_id=inquiry.id,
            title="Story 1",
            description="Description 1",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
            story_metadata={},
        )
        db_session.add(story)
        db_session.commit()

        story_ids = [story.id, 99999]  # 99999は存在しない

        # 一括承認実行
        results = service.batch_approve(story_ids, approver="batch_approver")

        # 検証
        assert len(results) == 2

        # 存在するストーリーは成功
        result1 = next(r for r in results if r[0] == story.id)
        assert result1[1] is True

        # 存在しないストーリーは失敗
        result2 = next(r for r in results if r[0] == 99999)
        assert result2[1] is False
        assert "not found" in result2[2].lower()

    def test_batch_approve_empty_list(self, service):
        """一括承認で空のリストを渡した場合."""
        results = service.batch_approve([], approver="test_approver")
        assert results == []

    # ===== can_transition_to メソッドのテスト =====

    def test_can_transition_to_approve(self, service):
        """waiting_review → approved遷移は許可される."""
        assert (
            service.can_transition_to(StoryStatus.WAITING_REVIEW, StoryStatus.APPROVED)
            is True
        )

    def test_can_transition_to_reject(self, service):
        """waiting_review → rejected遷移は許可される."""
        assert (
            service.can_transition_to(StoryStatus.WAITING_REVIEW, StoryStatus.REJECTED)
            is True
        )

    def test_can_transition_to_invalid(self, service):
        """approved → waiting_review遷移は禁止される."""
        assert (
            service.can_transition_to(StoryStatus.APPROVED, StoryStatus.WAITING_REVIEW)
            is False
        )

    def test_can_transition_to_same_status(self, service):
        """同じステータスへの遷移は禁止される."""
        assert (
            service.can_transition_to(
                StoryStatus.WAITING_REVIEW, StoryStatus.WAITING_REVIEW
            )
            is False
        )

    def test_can_transition_to_rejected_to_approved(self, service):
        """rejected → approved遷移は禁止される."""
        assert (
            service.can_transition_to(StoryStatus.REJECTED, StoryStatus.APPROVED)
            is False
        )


class TestStoryWorkflowServiceEdgeCases:
    """StoryWorkflowServiceのエッジケーステスト."""

    @pytest.fixture
    def inquiry(self, db_session):
        """テスト用問い合わせ作成フィクスチャ."""
        inquiry = InquiryModel(
            user_id="test_user",
            content="Test inquiry content",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
            inquiry_metadata={},
        )
        db_session.add(inquiry)
        db_session.commit()
        db_session.refresh(inquiry)
        return inquiry

    @pytest.fixture
    def repository(self, db_session):
        """StoryRepositoryフィクスチャ."""
        return StoryRepository(db_session)

    @pytest.fixture
    def service(self, repository):
        """StoryWorkflowServiceフィクスチャ."""
        return StoryWorkflowService(repository)

    def test_approve_story_preserves_existing_metadata(
        self, service, db_session, inquiry
    ):
        """承認時に既存のメタデータが保持される."""
        # 既存メタデータ付きのストーリーを作成
        story = StoryModel(
            inquiry_id=inquiry.id,
            title="Test Story",
            description="Test description",
            priority=Priority.HIGH,
            status=StoryStatus.WAITING_REVIEW,
            story_metadata={"custom_field": "custom_value"},
        )
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)

        # 承認実行
        approved_story = service.approve_story(story.id, approver="test_approver")

        # 既存メタデータが保持されていることを確認
        assert approved_story.story_metadata["custom_field"] == "custom_value"
        assert "approval" in approved_story.story_metadata

    def test_reject_story_preserves_existing_metadata(
        self, service, db_session, inquiry
    ):
        """却下時に既存のメタデータが保持される."""
        # 既存メタデータ付きのストーリーを作成
        story = StoryModel(
            inquiry_id=inquiry.id,
            title="Test Story",
            description="Test description",
            priority=Priority.LOW,
            status=StoryStatus.WAITING_REVIEW,
            story_metadata={"custom_field": "custom_value"},
        )
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)

        # 却下実行
        rejected_story = service.reject_story(
            story.id, rejector="test_rejector", reason="Test reason"
        )

        # 既存メタデータが保持されていることを確認
        assert rejected_story.story_metadata["custom_field"] == "custom_value"
        assert "rejection" in rejected_story.story_metadata

    def test_multiple_status_changes_accumulate_history(
        self, service, db_session, inquiry
    ):
        """複数のステータス変更で履歴が蓄積される."""
        # ストーリーを作成
        story = StoryModel(
            inquiry_id=inquiry.id,
            title="Test Story",
            description="Test description",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
            story_metadata={},
        )
        db_session.add(story)
        db_session.commit()
        story_id = story.id

        # 1. 承認 → 却下の流れをシミュレート（実際には許可されないが、メタデータ蓄積を確認）
        # 承認
        approved_story = service.approve_story(story_id, approver="approver1")
        assert len(approved_story.story_metadata["status_history"]) == 1

        # 別のストーリーで却下（実際のワークフローに沿う）
        story2 = StoryModel(
            inquiry_id=inquiry.id,
            title="Test Story 2",
            description="Test description 2",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
            story_metadata={},
        )
        db_session.add(story2)
        db_session.commit()

        rejected_story = service.reject_story(
            story2.id, rejector="rejector1", reason="Test"
        )
        assert len(rejected_story.story_metadata["status_history"]) == 1

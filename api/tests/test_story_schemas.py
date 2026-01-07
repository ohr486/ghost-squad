"""Test Story Pydantic schemas.

タスク 3.1: Pydanticスキーマを定義する
- CreateStoryRequest（手動作成用、inquiry_idはパスパラメータ）スキーマを実装する
- UpdateStoryRequest（編集用、すべてオプショナル）スキーマを実装する
- StoryResponse（API応答用）スキーマを実装する
- StoryMetadata（承認・却下情報、ステータス履歴）スキーマを実装する
- バリデーションルール（タイトル500文字以内、必須フィールド）を設定する
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from models.enums.priority import Priority
from models.enums.story_status import StoryStatus
from models.schemas.story import (
    ApprovalMetadata,
    CreateStoryRequest,
    RejectionMetadata,
    StatusHistoryEntry,
    StoryMetadata,
    StoryResponse,
    UpdateStoryRequest,
)


class TestCreateStoryRequest:
    """CreateStoryRequestスキーマのテスト (要件2.7, 2.11, 2.12, 4.5, 4.6)."""

    def test_create_story_request_valid_minimal(self):
        """最小限の必須フィールドで作成できる."""
        request = CreateStoryRequest(
            title="ログイン機能を追加",
            description="ユーザーがメールアドレスとパスワードでログインできるようにする",
            priority=Priority.MEDIUM,
        )

        assert request.title == "ログイン機能を追加"
        assert request.description == "ユーザーがメールアドレスとパスワードでログインできるようにする"
        assert request.priority == Priority.MEDIUM
        assert request.estimated_effort is None
        assert request.deadline is None
        assert request.assignee is None

    def test_create_story_request_valid_all_fields(self):
        """すべてのフィールドを設定できる."""
        deadline = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        request = CreateStoryRequest(
            title="ログイン機能を追加",
            description="ユーザーがメールアドレスとパスワードでログインできるようにする",
            priority=Priority.HIGH,
            estimated_effort=5.0,
            deadline=deadline,
            assignee="user123",
        )

        assert request.title == "ログイン機能を追加"
        assert request.description == "ユーザーがメールアドレスとパスワードでログインできるようにする"
        assert request.priority == Priority.HIGH
        assert request.estimated_effort == 5.0
        assert request.deadline == deadline
        assert request.assignee == "user123"

    def test_create_story_request_title_required(self):
        """タイトルは必須フィールドである."""
        with pytest.raises(ValidationError) as exc_info:
            CreateStoryRequest(
                description="説明",
                priority=Priority.MEDIUM,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("title",) for error in errors)

    def test_create_story_request_title_max_length_500(self):
        """タイトルは最大500文字 (要件4.5)."""
        long_title = "あ" * 501  # 501文字

        with pytest.raises(ValidationError) as exc_info:
            CreateStoryRequest(
                title=long_title,
                description="説明",
                priority=Priority.MEDIUM,
            )

        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("title",) and "at most 500 characters" in error["msg"]
            for error in errors
        )

    def test_create_story_request_title_exactly_500_chars(self):
        """タイトルは正確に500文字の場合も有効."""
        title_500 = "あ" * 500
        request = CreateStoryRequest(
            title=title_500,
            description="説明",
            priority=Priority.MEDIUM,
        )

        assert len(request.title) == 500

    def test_create_story_request_title_not_empty(self):
        """タイトルは空白のみは許可されない."""
        with pytest.raises(ValidationError) as exc_info:
            CreateStoryRequest(
                title="   ",
                description="説明",
                priority=Priority.MEDIUM,
            )

        errors = exc_info.value.errors()
        assert any(
            "タイトルが空です" in str(error["ctx"]["error"])
            for error in errors
            if error.get("ctx")
        )

    def test_create_story_request_description_required(self):
        """説明は必須フィールドである (要件4.6)."""
        with pytest.raises(ValidationError) as exc_info:
            CreateStoryRequest(
                title="タイトル",
                priority=Priority.MEDIUM,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("description",) for error in errors)

    def test_create_story_request_description_not_empty(self):
        """説明は空白のみは許可されない (要件4.6)."""
        with pytest.raises(ValidationError) as exc_info:
            CreateStoryRequest(
                title="タイトル",
                description="   ",
                priority=Priority.MEDIUM,
            )

        errors = exc_info.value.errors()
        assert any(
            "説明が空です" in str(error["ctx"]["error"])
            for error in errors
            if error.get("ctx")
        )

    def test_create_story_request_priority_required(self):
        """優先度は必須フィールドである."""
        with pytest.raises(ValidationError) as exc_info:
            CreateStoryRequest(
                title="タイトル",
                description="説明",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("priority",) for error in errors)

    def test_create_story_request_priority_enum_validation(self):
        """優先度はEnum値のみ許可される."""
        with pytest.raises(ValidationError):
            CreateStoryRequest(
                title="タイトル",
                description="説明",
                priority="invalid_priority",  # type: ignore
            )

    def test_create_story_request_estimated_effort_optional(self):
        """推定工数はオプショナル."""
        request = CreateStoryRequest(
            title="タイトル",
            description="説明",
            priority=Priority.MEDIUM,
            estimated_effort=None,
        )

        assert request.estimated_effort is None

    def test_create_story_request_estimated_effort_positive(self):
        """推定工数は正の値."""
        request = CreateStoryRequest(
            title="タイトル",
            description="説明",
            priority=Priority.MEDIUM,
            estimated_effort=3.5,
        )

        assert request.estimated_effort == 3.5

    def test_create_story_request_assignee_max_length(self):
        """担当者は最大50文字."""
        long_assignee = "a" * 51

        with pytest.raises(ValidationError) as exc_info:
            CreateStoryRequest(
                title="タイトル",
                description="説明",
                priority=Priority.MEDIUM,
                assignee=long_assignee,
            )

        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("assignee",) and "at most 50 characters" in error["msg"]
            for error in errors
        )


class TestUpdateStoryRequest:
    """UpdateStoryRequestスキーマのテスト (要件2.7, 4.12)."""

    def test_update_story_request_all_optional(self):
        """すべてのフィールドがオプショナル（部分更新対応）."""
        request = UpdateStoryRequest()

        assert request.title is None
        assert request.description is None
        assert request.priority is None
        assert request.estimated_effort is None
        assert request.deadline is None
        assert request.assignee is None

    def test_update_story_request_partial_update(self):
        """一部のフィールドのみ更新できる."""
        request = UpdateStoryRequest(
            title="更新されたタイトル",
            priority=Priority.URGENT,
        )

        assert request.title == "更新されたタイトル"
        assert request.priority == Priority.URGENT
        assert request.description is None

    def test_update_story_request_title_max_length_500(self):
        """タイトルは最大500文字."""
        long_title = "あ" * 501

        with pytest.raises(ValidationError) as exc_info:
            UpdateStoryRequest(title=long_title)

        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("title",) and "at most 500 characters" in error["msg"]
            for error in errors
        )

    def test_update_story_request_title_not_empty(self):
        """タイトルが提供される場合、空白のみは許可されない."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateStoryRequest(title="   ")

        errors = exc_info.value.errors()
        assert any(
            "タイトルが空です" in str(error["ctx"]["error"])
            for error in errors
            if error.get("ctx")
        )

    def test_update_story_request_description_not_empty(self):
        """説明が提供される場合、空白のみは許可されない."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateStoryRequest(description="   ")

        errors = exc_info.value.errors()
        assert any(
            "説明が空です" in str(error["ctx"]["error"])
            for error in errors
            if error.get("ctx")
        )

    def test_update_story_request_assignee_max_length(self):
        """担当者は最大50文字."""
        long_assignee = "a" * 51

        with pytest.raises(ValidationError) as exc_info:
            UpdateStoryRequest(assignee=long_assignee)

        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("assignee",) and "at most 50 characters" in error["msg"]
            for error in errors
        )


class TestStoryMetadata:
    """StoryMetadataスキーマのテスト (要件3.3, 3.7, 3.9)."""

    def test_approval_metadata_valid(self):
        """承認メタデータを作成できる."""
        approved_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        metadata = ApprovalMetadata(
            approved_at=approved_at,
            approver="user123",
        )

        assert metadata.approved_at == approved_at
        assert metadata.approver == "user123"

    def test_rejection_metadata_valid(self):
        """却下メタデータを作成できる."""
        rejected_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        metadata = RejectionMetadata(
            rejected_at=rejected_at,
            rejector="user456",
            reason="要件が不明瞭",
        )

        assert metadata.rejected_at == rejected_at
        assert metadata.rejector == "user456"
        assert metadata.reason == "要件が不明瞭"

    def test_rejection_metadata_reason_required(self):
        """却下理由は必須フィールド (要件3.5)."""
        with pytest.raises(ValidationError) as exc_info:
            RejectionMetadata(
                rejected_at=datetime.now(timezone.utc),
                rejector="user456",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("reason",) for error in errors)

    def test_rejection_metadata_reason_not_empty(self):
        """却下理由は空白のみは許可されない."""
        with pytest.raises(ValidationError) as exc_info:
            RejectionMetadata(
                rejected_at=datetime.now(timezone.utc),
                rejector="user456",
                reason="   ",
            )

        errors = exc_info.value.errors()
        assert any(
            "却下理由が空です" in str(error["ctx"]["error"])
            for error in errors
            if error.get("ctx")
        )

    def test_status_history_entry_valid(self):
        """ステータス履歴エントリを作成できる."""
        changed_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        entry = StatusHistoryEntry(
            from_status=StoryStatus.WAITING_REVIEW,
            to_status=StoryStatus.APPROVED,
            changed_at=changed_at,
            changed_by="user123",
        )

        assert entry.from_status == StoryStatus.WAITING_REVIEW
        assert entry.to_status == StoryStatus.APPROVED
        assert entry.changed_at == changed_at
        assert entry.changed_by == "user123"

    def test_story_metadata_all_fields(self):
        """StoryMetadataにすべてのフィールドを設定できる."""
        approved_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        approval = ApprovalMetadata(approved_at=approved_at, approver="user123")

        history = [
            StatusHistoryEntry(
                from_status=StoryStatus.WAITING_REVIEW,
                to_status=StoryStatus.APPROVED,
                changed_at=approved_at,
                changed_by="user123",
            )
        ]

        metadata = StoryMetadata(
            approval=approval,
            status_history=history,
        )

        assert metadata.approval == approval
        assert metadata.rejection is None
        assert len(metadata.status_history) == 1

    def test_story_metadata_all_optional(self):
        """StoryMetadataのすべてのフィールドはオプショナル."""
        metadata = StoryMetadata()

        assert metadata.approval is None
        assert metadata.rejection is None
        assert metadata.status_history == []


class TestStoryResponse:
    """StoryResponseスキーマのテスト (要件2.5, 4.1-4.11)."""

    def test_story_response_minimal_fields(self):
        """最小限の必須フィールドでレスポンスを作成できる."""
        created_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        response = StoryResponse(
            id=1,
            inquiry_id=100,
            title="ログイン機能を追加",
            description="ユーザーがログインできるようにする",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert response.id == 1
        assert response.inquiry_id == 100
        assert response.title == "ログイン機能を追加"
        assert response.description == "ユーザーがログインできるようにする"
        assert response.priority == Priority.MEDIUM
        assert response.status == StoryStatus.WAITING_REVIEW
        assert response.created_at == created_at
        assert response.updated_at == updated_at
        assert response.estimated_effort is None
        assert response.deadline is None
        assert response.assignee is None
        assert response.story_metadata == {}

    def test_story_response_all_fields(self):
        """すべてのフィールドを設定できる."""
        created_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        deadline = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        response = StoryResponse(
            id=1,
            inquiry_id=100,
            title="ログイン機能を追加",
            description="ユーザーがログインできるようにする",
            priority=Priority.HIGH,
            status=StoryStatus.APPROVED,
            estimated_effort=5.0,
            deadline=deadline,
            assignee="user123",
            story_metadata={
                "approval": {
                    "approved_at": "2026-01-01T12:00:00Z",
                    "approver": "user123",
                }
            },
            created_at=created_at,
            updated_at=updated_at,
        )

        assert response.estimated_effort == 5.0
        assert response.deadline == deadline
        assert response.assignee == "user123"
        assert "approval" in response.story_metadata

    def test_story_response_datetime_serialization(self):
        """datetimeフィールドがISO 8601形式でシリアライズされる."""
        created_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        response = StoryResponse(
            id=1,
            inquiry_id=100,
            title="タイトル",
            description="説明",
            priority=Priority.MEDIUM,
            status=StoryStatus.WAITING_REVIEW,
            created_at=created_at,
            updated_at=updated_at,
        )

        json_data = response.model_dump(mode="json")
        assert json_data["created_at"] == "2026-01-01T00:00:00+00:00"
        assert json_data["updated_at"] == "2026-01-01T12:00:00+00:00"

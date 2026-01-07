"""Test StoryValidator.

タスク 3.2: StoryValidatorを実装する
- 作成リクエストの検証（validate_create_request）を実装する
- 更新リクエストの検証（validate_update_request）を実装する
- AI生成ストーリーの構造検証（validate_generated_story）を実装する
- 問い合わせID存在確認（validate_inquiry_exists）を実装する
- エラーコード体系（GS-2xx）に従った日本語エラーメッセージを実装する
"""

from datetime import datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from models.database.base import BaseModel
from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus
from models.enums.priority import Priority
from models.schemas.story import CreateStoryRequest, UpdateStoryRequest
from services.story_validator import (
    GeneratedStoryData,
    StoryValidator,
    ValidationError,
    ValidationResult,
)


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


class TestStoryValidatorCreateRequest:
    """validate_create_requestのテスト (要件2.7, 2.12)."""

    def test_validate_create_request_valid_minimal(self):
        """最小限の必須フィールドで検証が成功する."""
        validator = StoryValidator()
        request = CreateStoryRequest(
            title="ログイン機能を追加",
            description="ユーザーがログインできるようにする",
            priority=Priority.MEDIUM,
        )

        result = validator.validate_create_request(request)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_create_request_valid_all_fields(self):
        """すべてのフィールドが設定されている場合、検証が成功する."""
        validator = StoryValidator()
        request = CreateStoryRequest(
            title="ログイン機能を追加",
            description="ユーザーがログインできるようにする",
            priority=Priority.HIGH,
            estimated_effort=5.0,
            deadline=datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
            assignee="user123",
        )

        result = validator.validate_create_request(request)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_create_request_title_too_long(self):
        """タイトルが500文字を超える場合、エラーを返す (要件4.5)."""
        long_title = "あ" * 501  # 501文字

        with pytest.raises(ValueError) as exc_info:
            CreateStoryRequest(
                title=long_title,
                description="説明",
                priority=Priority.MEDIUM,
            )

        assert "at most 500 characters" in str(exc_info.value)

    def test_validate_create_request_title_empty(self):
        """タイトルが空白のみの場合、エラーを返す."""
        with pytest.raises(ValueError) as exc_info:
            CreateStoryRequest(
                title="   ",
                description="説明",
                priority=Priority.MEDIUM,
            )

        assert "タイトルが空です" in str(exc_info.value)

    def test_validate_create_request_description_empty(self):
        """説明が空白のみの場合、エラーを返す (要件4.6)."""
        with pytest.raises(ValueError) as exc_info:
            CreateStoryRequest(
                title="タイトル",
                description="   ",
                priority=Priority.MEDIUM,
            )

        assert "説明が空です" in str(exc_info.value)


class TestStoryValidatorUpdateRequest:
    """validate_update_requestのテスト (要件2.7)."""

    def test_validate_update_request_valid_partial(self):
        """部分更新が有効な場合、検証が成功する."""
        validator = StoryValidator()
        request = UpdateStoryRequest(
            title="更新されたタイトル",
        )

        result = validator.validate_update_request(request)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_update_request_valid_all_fields(self):
        """すべてのフィールドが更新される場合、検証が成功する."""
        validator = StoryValidator()
        request = UpdateStoryRequest(
            title="更新されたタイトル",
            description="更新された説明",
            priority=Priority.URGENT,
            estimated_effort=8.0,
            deadline=datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
            assignee="user456",
        )

        result = validator.validate_update_request(request)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_update_request_empty_fields(self):
        """すべてのフィールドがNoneの場合も有効."""
        validator = StoryValidator()
        request = UpdateStoryRequest()

        result = validator.validate_update_request(request)

        assert result.valid is True
        assert len(result.errors) == 0


class TestStoryValidatorGeneratedStory:
    """validate_generated_storyのテスト (要件1.8, 1.9)."""

    def test_validate_generated_story_valid_minimal(self):
        """必須フィールドのみのAI生成ストーリーを検証できる."""
        validator = StoryValidator()
        data = {
            "title": "ログイン機能を追加",
            "description": "ユーザーがログインできるようにする",
            "priority": "medium",
        }

        result = validator.validate_generated_story(data)

        assert isinstance(result, GeneratedStoryData)
        assert result.title == "ログイン機能を追加"
        assert result.description == "ユーザーがログインできるようにする"
        assert result.priority == Priority.MEDIUM
        assert result.estimated_effort is None

    def test_validate_generated_story_valid_with_optional_fields(self):
        """オプショナルフィールドを含むAI生成ストーリーを検証できる."""
        validator = StoryValidator()
        data = {
            "title": "ログイン機能を追加",
            "description": "ユーザーがログインできるようにする",
            "priority": "high",
            "estimated_effort": 5.0,
        }

        result = validator.validate_generated_story(data)

        assert result.title == "ログイン機能を追加"
        assert result.priority == Priority.HIGH
        assert result.estimated_effort == 5.0

    def test_validate_generated_story_missing_title(self):
        """タイトルが欠けている場合、ValidationErrorを発生させる."""
        validator = StoryValidator()
        data = {
            "description": "説明",
            "priority": "medium",
        }

        with pytest.raises(ValueError) as exc_info:
            validator.validate_generated_story(data)

        assert "title" in str(exc_info.value).lower()

    def test_validate_generated_story_missing_description(self):
        """説明が欠けている場合、ValidationErrorを発生させる."""
        validator = StoryValidator()
        data = {
            "title": "タイトル",
            "priority": "medium",
        }

        with pytest.raises(ValueError) as exc_info:
            validator.validate_generated_story(data)

        assert "description" in str(exc_info.value).lower()

    def test_validate_generated_story_missing_priority(self):
        """優先度が欠けている場合、ValidationErrorを発生させる."""
        validator = StoryValidator()
        data = {
            "title": "タイトル",
            "description": "説明",
        }

        with pytest.raises(ValueError) as exc_info:
            validator.validate_generated_story(data)

        assert "priority" in str(exc_info.value).lower()

    def test_validate_generated_story_title_too_long(self):
        """タイトルが500文字を超える場合、ValidationErrorを発生させる (要件1.9)."""
        validator = StoryValidator()
        long_title = "あ" * 501
        data = {
            "title": long_title,
            "description": "説明",
            "priority": "medium",
        }

        with pytest.raises(ValueError) as exc_info:
            validator.validate_generated_story(data)

        assert "500" in str(exc_info.value)

    def test_validate_generated_story_title_exactly_500_chars(self):
        """タイトルが正確に500文字の場合は有効."""
        validator = StoryValidator()
        title_500 = "あ" * 500
        data = {
            "title": title_500,
            "description": "説明",
            "priority": "medium",
        }

        result = validator.validate_generated_story(data)

        assert len(result.title) == 500

    def test_validate_generated_story_invalid_priority(self):
        """不正な優先度の場合、ValidationErrorを発生させる."""
        validator = StoryValidator()
        data = {
            "title": "タイトル",
            "description": "説明",
            "priority": "invalid_priority",
        }

        with pytest.raises(ValueError) as exc_info:
            validator.validate_generated_story(data)

        assert "priority" in str(exc_info.value).lower()

    def test_validate_generated_story_title_empty(self):
        """タイトルが空の場合、ValidationErrorを発生させる."""
        validator = StoryValidator()
        data = {
            "title": "",
            "description": "説明",
            "priority": "medium",
        }

        with pytest.raises(ValueError) as exc_info:
            validator.validate_generated_story(data)

        assert "タイトルが空です" in str(exc_info.value)

    def test_validate_generated_story_description_empty(self):
        """説明が空の場合、ValidationErrorを発生させる."""
        validator = StoryValidator()
        data = {
            "title": "タイトル",
            "description": "",
            "priority": "medium",
        }

        with pytest.raises(ValueError) as exc_info:
            validator.validate_generated_story(data)

        assert "説明が空です" in str(exc_info.value)


class TestStoryValidatorInquiryExists:
    """validate_inquiry_existsのテスト (要件2.13)."""

    def test_validate_inquiry_exists_valid(self, db_session: Session):
        """問い合わせが存在する場合、Trueを返す."""
        # 問い合わせを作成
        inquiry = InquiryModel(
            user_id="test_user",
            content="問い合わせ内容",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        db_session.add(inquiry)
        db_session.commit()

        validator = StoryValidator()
        result = validator.validate_inquiry_exists(db_session, inquiry.id)

        assert result is True

    def test_validate_inquiry_exists_not_found(self, db_session: Session):
        """問い合わせが存在しない場合、ValidationErrorを発生させる (エラーコード: GS-204)."""
        validator = StoryValidator()

        with pytest.raises(ValueError) as exc_info:
            validator.validate_inquiry_exists(db_session, 99999)

        error_message = str(exc_info.value)
        assert "GS-204" in error_message
        assert "問い合わせが見つかりません" in error_message


class TestValidationErrorAndResult:
    """ValidationErrorとValidationResultのテスト."""

    def test_validation_error_structure(self):
        """ValidationErrorが正しい構造を持つ."""
        error = ValidationError(
            field="title",
            message="タイトルが空です",
            code="GS-201",
        )

        assert error.field == "title"
        assert error.message == "タイトルが空です"
        assert error.code == "GS-201"

    def test_validation_result_valid(self):
        """ValidationResultが有効な結果を表現できる."""
        result = ValidationResult(valid=True, errors=[])

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validation_result_invalid(self):
        """ValidationResultが無効な結果を表現できる."""
        error = ValidationError(
            field="title",
            message="タイトルが空です",
            code="GS-201",
        )
        result = ValidationResult(valid=False, errors=[error])

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "GS-201"


class TestStoryValidatorErrorCodes:
    """エラーコード体系のテスト (要件3.2)."""

    def test_error_code_gs201_title_too_long(self):
        """GS-201: タイトル長さ制限違反."""
        # Pydanticバリデーションがエラーを投げる
        with pytest.raises(ValueError):
            CreateStoryRequest(
                title="あ" * 501,
                description="説明",
                priority=Priority.MEDIUM,
            )

    def test_error_code_gs202_missing_required_field(self):
        """GS-202: 必須フィールド欠如."""
        # Pydanticバリデーションがエラーを投げる
        with pytest.raises(ValueError):
            CreateStoryRequest(
                description="説明",
                priority=Priority.MEDIUM,
            )  # type: ignore

    def test_error_code_gs204_inquiry_not_found(self, db_session: Session):
        """GS-204: Inquiry不存在."""
        validator = StoryValidator()

        with pytest.raises(ValueError) as exc_info:
            validator.validate_inquiry_exists(db_session, 99999)

        assert "GS-204" in str(exc_info.value)

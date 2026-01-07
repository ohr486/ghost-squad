"""StoryGenerationService tests.

タスク 4.2*: AI生成サービスの動作を検証する
Test-Driven Development (TDD) approach:
1. RED: Write failing tests
2. GREEN: Implement minimal code to pass tests
3. REFACTOR: Clean up code
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from models.database.inquiry import InquiryModel
from models.database.story import StoryModel
from models.enums.inquiry_status import InquiryStatus
from models.enums.priority import Priority
from models.enums.story_status import StoryStatus
from services.story_generation_service import (
    AIGenerationError,
    InquiryNotFoundError,
    InvalidInquiryStatusError,
    StoryGenerationService,
)


class TestStoryGenerationService:
    """StoryGenerationService tests."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create mock database session."""
        session = MagicMock(spec=Session)
        return session

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> StoryGenerationService:
        """Create StoryGenerationService instance."""
        return StoryGenerationService(mock_session)

    @pytest.fixture
    def valid_inquiry(self) -> InquiryModel:
        """Create valid inquiry in task_working status."""
        inquiry = InquiryModel(
            id=1,
            user_id="test_user",
            content="ログイン機能を追加してください",
            source_system="web",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
            inquiry_metadata={},
        )
        return inquiry

    def test_generate_story_success(
        self,
        service: StoryGenerationService,
        mock_session: MagicMock,
        valid_inquiry: InquiryModel,
    ):
        """Test successful story generation from inquiry.

        要件 1.1-1.6: AI変換成功時のフロー
        - Inquiryステータス検証（task_working）
        - Inquiryステータス更新（processing → completed）
        - Story作成（waiting_review）
        - InquiryとStoryの関連付け
        """
        # Arrange: Mock inquiry retrieval
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            valid_inquiry
        )

        # Mock OpenAI API response
        ai_response = {
            "title": "ユーザーログイン機能の実装",
            "description": "ユーザーがメールアドレスとパスワードでログインできるようにする",
            "priority": "high",
            "estimated_effort": 5.0,
        }

        with patch.object(
            service, "_call_openai_api", return_value=ai_response
        ) as mock_ai_call:
            # Act: Generate story
            result = service.generate_story(inquiry_id=1)

            # Assert: Verify OpenAI API was called with inquiry content
            mock_ai_call.assert_called_once_with(valid_inquiry.content)

            # Assert: Verify story was created
            assert result is not None
            assert isinstance(result, StoryModel)
            assert result.inquiry_id == 1
            assert result.title == ai_response["title"]
            assert result.description == ai_response["description"]
            assert result.priority == Priority.HIGH
            assert result.status == StoryStatus.WAITING_REVIEW
            assert result.estimated_effort == 5.0

            # Assert: Verify inquiry status was updated to completed
            assert valid_inquiry.status == InquiryStatus.COMPLETED

            # Assert: Verify session commit was called
            assert mock_session.commit.call_count >= 2  # status update + story creation

    def test_generate_story_inquiry_not_found(
        self, service: StoryGenerationService, mock_session: MagicMock
    ):
        """Test generation fails when inquiry does not exist.

        要件: InquiryNotFoundError発生
        """
        # Arrange: Mock inquiry not found
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Act & Assert: Verify exception is raised
        with pytest.raises(InquiryNotFoundError) as exc_info:
            service.generate_story(inquiry_id=999)

        assert "Inquiry with id 999 not found" in str(exc_info.value)

    def test_generate_story_invalid_inquiry_status(
        self,
        service: StoryGenerationService,
        mock_session: MagicMock,
        valid_inquiry: InquiryModel,
    ):
        """Test generation fails when inquiry status is not task_working.

        要件1.1: Inquiryステータス検証
        """
        # Arrange: Set inquiry to invalid status
        valid_inquiry.status = InquiryStatus.RECEIVED
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            valid_inquiry
        )

        # Act & Assert: Verify exception is raised
        with pytest.raises(InvalidInquiryStatusError) as exc_info:
            service.generate_story(inquiry_id=1)

        assert "Inquiry status must be task_working" in str(exc_info.value)

    def test_generate_story_ai_generation_error_rolls_back_status(
        self,
        service: StoryGenerationService,
        mock_session: MagicMock,
        valid_inquiry: InquiryModel,
    ):
        """Test inquiry status is rolled back when AI generation fails.

        要件1.7: AI APIエラー時のリトライ処理とロールバック
        """
        # Arrange
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            valid_inquiry
        )

        # Mock OpenAI API to raise AIGenerationError
        with patch.object(
            service, "_call_openai_api", side_effect=AIGenerationError("API timeout")
        ):
            # Act & Assert
            with pytest.raises(AIGenerationError):
                service.generate_story(inquiry_id=1)

            # Assert: Verify inquiry status was rolled back to task_working
            assert valid_inquiry.status == InquiryStatus.TASK_WORKING
            # commit called twice: once for processing, once for rollback
            assert mock_session.commit.call_count == 2

    def test_generate_story_validation_error_rolls_back_status(
        self,
        service: StoryGenerationService,
        mock_session: MagicMock,
        valid_inquiry: InquiryModel,
    ):
        """Test inquiry status is rolled back when validation fails.

        要件1.8: ストーリー構造検証失敗時のロールバック
        """
        # Arrange
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            valid_inquiry
        )

        # Mock OpenAI API to return invalid data
        invalid_response = {"title": "Missing description and priority"}

        with patch.object(service, "_call_openai_api", return_value=invalid_response):
            # Act & Assert
            with pytest.raises(ValueError):
                service.generate_story(inquiry_id=1)

            # Assert: Verify inquiry status was rolled back to task_working
            assert valid_inquiry.status == InquiryStatus.TASK_WORKING


class TestCallOpenAIAPI:
    """Test _call_openai_api with retry logic."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create mock database session."""
        session = MagicMock(spec=Session)
        return session

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> StoryGenerationService:
        """Create StoryGenerationService instance."""
        return StoryGenerationService(mock_session)

    def test_call_openai_api_success(self, service: StoryGenerationService):
        """Test successful OpenAI API call.

        要件1.3: AI APIによるストーリー生成
        """
        with patch("services.story_generation_service.OpenAI") as mock_openai:
            # Mock OpenAI response
            mock_response = (
                '{"title": "Test Story", '
                '"description": "Test description", '
                '"priority": "high", "estimated_effort": 3.0}'
            )
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value.choices = [
                MagicMock(message=MagicMock(content=mock_response))
            ]

            # Act
            result = service._call_openai_api("Test inquiry content")

            # Assert
            assert result["title"] == "Test Story"
            assert result["description"] == "Test description"
            assert result["priority"] == "high"
            assert result["estimated_effort"] == 3.0

    def test_call_openai_api_retries_on_rate_limit(
        self, service: StoryGenerationService
    ):
        """Test retry logic on rate limit error.

        要件1.7: AI APIエラー時のリトライ処理
        """
        with patch("services.story_generation_service.OpenAI") as mock_openai:
            # Mock first 2 calls fail with rate limit, 3rd succeeds
            retry_response = (
                '{"title": "Retry Success", '
                '"description": "After retries", '
                '"priority": "medium"}'
            )
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_create = mock_client.chat.completions.create
            mock_create.side_effect = [
                Exception("Rate limit exceeded"),
                Exception("Rate limit exceeded"),
                MagicMock(
                    choices=[
                        MagicMock(message=MagicMock(content=retry_response))
                    ]
                ),
            ]

            # Act
            result = service._call_openai_api("Test content")

            # Assert: Should succeed after retries
            assert result["title"] == "Retry Success"
            assert mock_create.call_count == 3

    def test_call_openai_api_fails_after_max_retries(
        self, service: StoryGenerationService
    ):
        """Test failure after maximum retries.

        要件1.7: リトライ後も失敗した場合のエラー
        """
        with patch("services.story_generation_service.OpenAI") as mock_openai:
            # Mock all calls fail
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_create = mock_client.chat.completions.create
            mock_create.side_effect = Exception("Persistent error")

            # Act & Assert
            with pytest.raises(AIGenerationError) as exc_info:
                service._call_openai_api("Test content")

            # Assert: Should have tried 3 times
            assert mock_create.call_count == 3
            assert "リトライ後も失敗" in str(exc_info.value)

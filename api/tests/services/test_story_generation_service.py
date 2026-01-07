"""StoryGenerationService tests.

タスク 4.2*: AI生成サービスの動作を検証する
Test-Driven Development (TDD) approach:
1. RED: Write failing tests
2. GREEN: Implement minimal code to pass tests
3. REFACTOR: Clean up code
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
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
        # Mock OpenAI client initialization
        with patch(
            "services.story_generation_service.OpenAI"
        ) as mock_openai, patch.dict(
            "os.environ", {"OPENAI_API_KEY": "sk-test-key-1234567890abcdef"}
        ):
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            service = StoryGenerationService(mock_session)
            # Store mock client for test use
            service._test_mock_client = mock_client
            return service

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

            # Assert: Verify session was used for transaction
            # Note: With session.begin() context manager, commit is called once
            # by repository.create()
            assert mock_session.commit.call_count >= 1

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
            # Note: With session.begin() context manager, on error the transaction
            # is automatically rolled back, so no explicit commit is called

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
        # Mock OpenAI client initialization
        with patch(
            "services.story_generation_service.OpenAI"
        ) as mock_openai, patch.dict(
            "os.environ", {"OPENAI_API_KEY": "sk-test-key-1234567890abcdef"}
        ):
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            service = StoryGenerationService(mock_session)
            return service

    def test_call_openai_api_success(self, service: StoryGenerationService):
        """Test successful OpenAI API call.

        要件1.3: AI APIによるストーリー生成
        """
        # Mock OpenAI response using the service's client
        mock_response = (
            '{"title": "Test Story", '
            '"description": "Test description", '
            '"priority": "high", "estimated_effort": 3.0}'
        )
        service.openai_client.chat.completions.create.return_value.choices = [
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
        指数バックオフのタイミングを検証
        """
        with patch("services.story_generation_service.time.sleep") as mock_sleep:
            # Mock first 2 calls fail with rate limit, 3rd succeeds
            retry_response = (
                '{"title": "Retry Success", '
                '"description": "After retries", '
                '"priority": "medium", '
                '"estimated_effort": 2.5}'
            )
            mock_create = service.openai_client.chat.completions.create
            mock_create.side_effect = [
                Exception("Rate limit exceeded"),
                Exception("Rate limit exceeded"),
                MagicMock(
                    choices=[MagicMock(message=MagicMock(content=retry_response))]
                ),
            ]

            # Act
            result = service._call_openai_api("Test content")

            # Assert: Should succeed after retries
            assert result["title"] == "Retry Success"
            assert mock_create.call_count == 3

            # Assert: Verify exponential backoff timing (1s, 2s for first 2 retries)
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1)  # 2^0 = 1s for first retry
            mock_sleep.assert_any_call(2)  # 2^1 = 2s for second retry

    def test_call_openai_api_fails_after_max_retries(
        self, service: StoryGenerationService
    ):
        """Test failure after maximum retries.

        要件1.7: リトライ後も失敗した場合のエラー
        """
        # Mock all calls to fail
        mock_create = service.openai_client.chat.completions.create
        mock_create.side_effect = Exception("Persistent error")

        # Act & Assert
        with pytest.raises(AIGenerationError) as exc_info:
            service._call_openai_api("Test content")

        # Assert: Should have tried 3 times
        assert mock_create.call_count == 3
        assert "リトライ後も失敗" in str(exc_info.value)


class TestSanitizeInquiryContent:
    """Test _sanitize_inquiry_content method."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create mock database session."""
        session = MagicMock(spec=Session)
        return session

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> StoryGenerationService:
        """Create StoryGenerationService instance."""
        # Mock OpenAI client initialization
        with patch(
            "services.story_generation_service.OpenAI"
        ) as mock_openai, patch.dict(
            "os.environ", {"OPENAI_API_KEY": "sk-test-key-1234567890abcdef"}
        ):
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            service = StoryGenerationService(mock_session)
            return service

    def test_sanitize_inquiry_content_success(self, service: StoryGenerationService):
        """Test successful sanitization of inquiry content."""
        # Arrange
        content = "  ログイン機能を追加してください  "

        # Act
        result = service._sanitize_inquiry_content(content)

        # Assert
        assert result == "ログイン機能を追加してください"

    def test_sanitize_inquiry_content_removes_control_characters(
        self, service: StoryGenerationService
    ):
        """Test that control characters are removed (except newlines, tabs)."""
        # Arrange
        content = "テキスト\x00\x01\x02with\ncontrol\tchars"

        # Act
        result = service._sanitize_inquiry_content(content)

        # Assert
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
        assert "\n" in result  # Newlines should be preserved
        assert "\t" in result  # Tabs should be preserved

    def test_sanitize_inquiry_content_empty_raises_error(
        self, service: StoryGenerationService
    ):
        """Test that empty content raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service._sanitize_inquiry_content("")
        assert "cannot be empty" in str(exc_info.value)

    def test_sanitize_inquiry_content_whitespace_only_raises_error(
        self, service: StoryGenerationService
    ):
        """Test that whitespace-only content raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service._sanitize_inquiry_content("   \n\t  ")
        assert "cannot be empty" in str(exc_info.value)

    def test_sanitize_inquiry_content_too_long_raises_error(
        self, service: StoryGenerationService
    ):
        """Test that content exceeding max length raises ValueError."""
        # Arrange: Create content longer than 5000 characters
        content = "あ" * 5001

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service._sanitize_inquiry_content(content)
        assert "too long" in str(exc_info.value)
        assert "5001" in str(exc_info.value)
        assert "5000" in str(exc_info.value)

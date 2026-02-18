"""PromptService unit tests.

TDD implementation for prompt business logic layer.
Tests cover:
- Task 4.1: get_prompt, list_prompts, update_prompt, reset_to_default
- Task 4.2: test_prompt (AI test execution)
- Task 4.3: acquire_edit_lock, release_edit_lock
"""
from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.database.base import BaseModel
from models.database.prompt import PromptModel
from models.enums.prompt_category import PromptCategory
from services.prompt_cache import PromptCache, PromptCacheEntry
from services.prompt_service import (PromptData, PromptNotFoundError,
                                     PromptService, PromptTestError,
                                     PromptTestTimeoutError,
                                     PromptValidationError, TestPromptRequest,
                                     UpdatePromptRequest)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    BaseModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def cache() -> PromptCache:
    """Create PromptCache instance."""
    return PromptCache(ttl_seconds=60)


@pytest.fixture
def service(db_session: Session, cache: PromptCache) -> PromptService:
    """Create PromptService instance without AI provider registry."""
    return PromptService(session=db_session, cache=cache)


def _seed_prompt(db_session: Session, **overrides) -> PromptModel:
    """Helper to create a prompt directly in DB."""
    defaults = {
        "key": "test_prompt",
        "name": "テストプロンプト",
        "description": "テスト用プロンプト",
        "category": PromptCategory.GENERAL,
        "content": "テスト内容 {variable_1}",
        "default_content": "テスト内容 {variable_1}",
        "variables": ["variable_1"],
        "is_modified": False,
    }
    defaults.update(overrides)
    prompt = PromptModel(**defaults)
    db_session.add(prompt)
    db_session.commit()
    db_session.refresh(prompt)
    return prompt


# =============================================================================
# Task 4.1: get_prompt tests
# =============================================================================


class TestPromptServiceGetPrompt:
    """Tests for get_prompt operation (要件5.1, 5.2, 5.3, 5.4, 5.5)."""

    def test_get_prompt_from_db(
        self, service: PromptService, db_session: Session
    ) -> None:
        """DBからプロンプトを取得できる."""
        # Arrange
        _seed_prompt(db_session, key="story_gen")

        # Act
        result = service.get_prompt("story_gen")

        # Assert
        assert result.key == "story_gen"
        assert result.content == "テスト内容 {variable_1}"
        assert result.variables == ["variable_1"]

    def test_get_prompt_uses_cache(
        self, service: PromptService, db_session: Session, cache: PromptCache
    ) -> None:
        """キャッシュヒット時はキャッシュから取得する."""
        # Arrange
        cache.set(
            "cached_key",
            PromptCacheEntry(
                key="cached_key",
                content="キャッシュ内容",
                default_content="デフォルト内容",
                variables=["var1"],
            ),
        )
        # DB にはデータがない

        # Act
        result = service.get_prompt("cached_key")

        # Assert
        assert result.content == "キャッシュ内容"

    def test_get_prompt_populates_cache(
        self, service: PromptService, db_session: Session, cache: PromptCache
    ) -> None:
        """DB取得後にキャッシュに格納される."""
        # Arrange
        _seed_prompt(db_session, key="populate_cache")

        # Act
        service.get_prompt("populate_cache")

        # Assert
        cached = cache.get("populate_cache")
        assert cached is not None
        assert cached.content == "テスト内容 {variable_1}"

    def test_get_prompt_not_found_raises_error(self, service: PromptService) -> None:
        """存在しないキーはPromptNotFoundErrorを発生させる."""
        with pytest.raises(PromptNotFoundError):
            service.get_prompt("nonexistent_key")

    def test_get_prompt_fallback_to_cache_on_db_error(
        self, service: PromptService, cache: PromptCache
    ) -> None:
        """DB障害時にキャッシュからフォールバック取得する."""
        # Arrange
        cache.set(
            "fallback_key",
            PromptCacheEntry(
                key="fallback_key",
                content="フォールバック内容",
                default_content="デフォルト",
                variables=[],
            ),
        )

        # Mock repository to raise exception
        service._repository.find_by_key = MagicMock(side_effect=Exception("DB error"))

        # Act
        result = service.get_prompt("fallback_key")

        # Assert
        assert result.content == "フォールバック内容"

    def test_get_prompt_returns_prompt_data(
        self, service: PromptService, db_session: Session
    ) -> None:
        """PromptDataの全フィールドが正しく返される."""
        # Arrange
        _seed_prompt(
            db_session,
            key="full_data",
            name="完全データ",
            description="説明文",
            category=PromptCategory.STORY_GENERATION,
            content="カスタム内容",
            default_content="デフォルト内容",
            variables=["var1", "var2"],
            is_modified=True,
        )

        # Act
        result = service.get_prompt("full_data")

        # Assert
        assert result.key == "full_data"
        assert result.name == "完全データ"
        assert result.description == "説明文"
        assert result.category == "story_generation"
        assert result.content == "カスタム内容"
        assert result.default_content == "デフォルト内容"
        assert result.variables == ["var1", "var2"]
        assert result.is_modified is True


# =============================================================================
# Task 4.1: list_prompts tests
# =============================================================================


class TestPromptServiceListPrompts:
    """Tests for list_prompts operation (要件1.1, 1.3)."""

    def test_list_prompts_returns_all(
        self, service: PromptService, db_session: Session
    ) -> None:
        """全プロンプトを取得できる."""
        # Arrange
        _seed_prompt(db_session, key="p1")
        _seed_prompt(db_session, key="p2")
        _seed_prompt(db_session, key="p3")

        # Act
        results = service.list_prompts()

        # Assert
        assert len(results) == 3

    def test_list_prompts_with_category_filter(
        self, service: PromptService, db_session: Session
    ) -> None:
        """カテゴリフィルタリングが動作する."""
        # Arrange
        _seed_prompt(db_session, key="sg1", category=PromptCategory.STORY_GENERATION)
        _seed_prompt(db_session, key="ia1", category=PromptCategory.IMPORT_ANALYSIS)
        _seed_prompt(db_session, key="gen1", category=PromptCategory.GENERAL)

        # Act
        results = service.list_prompts(category=PromptCategory.STORY_GENERATION)

        # Assert
        assert len(results) == 1
        assert results[0].key == "sg1"

    def test_list_prompts_returns_empty(self, service: PromptService) -> None:
        """プロンプトが存在しない場合は空リストを返す."""
        # Act
        results = service.list_prompts()

        # Assert
        assert results == []

    def test_list_prompts_returns_prompt_data_objects(
        self, service: PromptService, db_session: Session
    ) -> None:
        """PromptDataオブジェクトのリストを返す."""
        # Arrange
        _seed_prompt(db_session, key="data_obj")

        # Act
        results = service.list_prompts()

        # Assert
        assert len(results) == 1
        assert isinstance(results[0], PromptData)
        assert results[0].key == "data_obj"


# =============================================================================
# Task 4.1: update_prompt tests
# =============================================================================


class TestPromptServiceUpdatePrompt:
    """Tests for update_prompt operation (要件2.2, 2.3, 2.4)."""

    def test_update_prompt_content(
        self, service: PromptService, db_session: Session
    ) -> None:
        """プロンプト内容を更新できる."""
        # Arrange
        _seed_prompt(db_session, key="update_test")

        # Act
        result = service.update_prompt(
            "update_test",
            UpdatePromptRequest(content="更新内容 {variable_1}"),
        )

        # Assert
        assert result.content == "更新内容 {variable_1}"

    def test_update_prompt_invalidates_cache(
        self, service: PromptService, db_session: Session, cache: PromptCache
    ) -> None:
        """更新後にキャッシュが無効化される."""
        # Arrange
        _seed_prompt(db_session, key="cache_invalidate")
        cache.set(
            "cache_invalidate",
            PromptCacheEntry(
                key="cache_invalidate",
                content="古い内容",
                default_content="デフォルト",
                variables=[],
            ),
        )

        # Act
        service.update_prompt(
            "cache_invalidate",
            UpdatePromptRequest(content="新しい内容"),
        )

        # Assert
        cached = cache.get("cache_invalidate")
        assert cached is None

    def test_update_prompt_validates_content_not_empty(
        self, service: PromptService, db_session: Session
    ) -> None:
        """空のコンテンツでの更新は拒否される."""
        # Arrange
        _seed_prompt(db_session, key="empty_content")

        # Act & Assert
        with pytest.raises(PromptValidationError) as exc_info:
            service.update_prompt(
                "empty_content",
                UpdatePromptRequest(content=""),
            )
        assert "GS-401" in str(exc_info.value)

    def test_update_prompt_validates_placeholders(
        self, service: PromptService, db_session: Session
    ) -> None:
        """無効なプレースホルダーの更新は拒否される."""
        # Arrange
        _seed_prompt(
            db_session,
            key="bad_placeholder",
            variables=["variable_1"],
        )

        # Act & Assert
        with pytest.raises(PromptValidationError) as exc_info:
            service.update_prompt(
                "bad_placeholder",
                UpdatePromptRequest(content="内容 {invalid var}"),
            )
        assert "GS-402" in str(exc_info.value)

    def test_update_nonexistent_prompt_raises_error(
        self, service: PromptService
    ) -> None:
        """存在しないプロンプトの更新はエラーを発生させる."""
        with pytest.raises(PromptNotFoundError):
            service.update_prompt(
                "nonexistent",
                UpdatePromptRequest(content="内容"),
            )

    def test_update_prompt_with_description(
        self, service: PromptService, db_session: Session
    ) -> None:
        """descriptionも同時に更新できる."""
        # Arrange
        _seed_prompt(db_session, key="desc_update")

        # Act
        result = service.update_prompt(
            "desc_update",
            UpdatePromptRequest(content="新しい内容", description="新しい説明"),
        )

        # Assert
        assert result.description == "新しい説明"


# =============================================================================
# Task 4.1: reset_to_default tests
# =============================================================================


class TestPromptServiceResetToDefault:
    """Tests for reset_to_default operation (要件4.4)."""

    def test_reset_to_default_success(
        self, service: PromptService, db_session: Session
    ) -> None:
        """デフォルトにリセットできる."""
        # Arrange
        _seed_prompt(
            db_session,
            key="reset_test",
            content="カスタム内容",
            default_content="デフォルト内容",
            is_modified=True,
        )

        # Act
        result = service.reset_to_default("reset_test")

        # Assert
        assert result.content == "デフォルト内容"
        assert result.is_modified is False

    def test_reset_invalidates_cache(
        self, service: PromptService, db_session: Session, cache: PromptCache
    ) -> None:
        """リセット後にキャッシュが無効化される."""
        # Arrange
        _seed_prompt(
            db_session,
            key="reset_cache",
            content="カスタム",
            default_content="デフォルト",
        )
        cache.set(
            "reset_cache",
            PromptCacheEntry(
                key="reset_cache",
                content="カスタム",
                default_content="デフォルト",
                variables=[],
            ),
        )

        # Act
        service.reset_to_default("reset_cache")

        # Assert
        cached = cache.get("reset_cache")
        assert cached is None

    def test_reset_nonexistent_raises_error(self, service: PromptService) -> None:
        """存在しないプロンプトのリセットはエラーを発生させる."""
        with pytest.raises(PromptNotFoundError):
            service.reset_to_default("nonexistent")


# =============================================================================
# Task 4.2: test_prompt tests
# =============================================================================


class TestPromptServiceTestPrompt:
    """Tests for test_prompt operation (要件3.1, 3.2, 3.4)."""

    def test_test_prompt_with_mock_provider(self, service: PromptService) -> None:
        """AIプロバイダーモックでテスト実行できる."""
        # Arrange
        mock_registry = MagicMock()
        mock_provider = MagicMock()
        mock_provider.provider_type.value = "openai"
        mock_provider._config.model = "gpt-4"
        mock_provider.analyze.return_value = MagicMock(
            content="AI出力結果",
            provider_type="openai",
            model="gpt-4",
        )
        mock_registry.get_provider.return_value = mock_provider
        service._ai_provider_registry = mock_registry

        request = TestPromptRequest(
            content="テスト {var1}",
            variables={"var1": "値1"},
        )

        # Act
        result = service.test_prompt(request)

        # Assert
        assert result.output == "AI出力結果"
        assert result.provider == "openai"
        assert result.model == "gpt-4"

    def test_test_prompt_replaces_placeholders(self, service: PromptService) -> None:
        """プレースホルダーが正しく置換される."""
        # Arrange
        mock_registry = MagicMock()
        mock_provider = MagicMock()
        mock_provider.provider_type.value = "openai"
        mock_provider._config.model = "gpt-4"
        mock_provider.analyze.return_value = MagicMock(
            content="結果",
            provider_type="openai",
            model="gpt-4",
        )
        mock_registry.get_provider.return_value = mock_provider
        service._ai_provider_registry = mock_registry

        request = TestPromptRequest(
            content="Hello {name}, your task is {task}",
            variables={"name": "太郎", "task": "テスト"},
        )

        # Act
        service.test_prompt(request)

        # Assert - verify the substituted content was sent
        call_args = mock_provider.analyze.call_args
        sent_content = call_args[0][0].content
        assert "太郎" in sent_content
        assert "テスト" in sent_content

    def test_test_prompt_with_specific_provider(self, service: PromptService) -> None:
        """プロバイダーを指定してテスト実行できる."""
        # Arrange
        mock_registry = MagicMock()
        mock_provider = MagicMock()
        mock_provider.provider_type.value = "anthropic"
        mock_provider._config.model = "claude-3"
        mock_provider.analyze.return_value = MagicMock(
            content="Anthropic出力",
            provider_type="anthropic",
            model="claude-3",
        )
        mock_registry.get_provider.return_value = mock_provider
        service._ai_provider_registry = mock_registry

        request = TestPromptRequest(
            content="テスト内容",
            variables={},
            provider="anthropic",
        )

        # Act
        result = service.test_prompt(request)

        # Assert
        assert result.provider == "anthropic"

    def test_test_prompt_timeout_raises_error(self, service: PromptService) -> None:
        """タイムアウト時にGS-406エラーが発生する."""
        # Arrange
        mock_registry = MagicMock()
        mock_provider = MagicMock()
        mock_provider.analyze.side_effect = TimeoutError("Timeout")
        mock_registry.get_provider.return_value = mock_provider
        service._ai_provider_registry = mock_registry

        request = TestPromptRequest(
            content="テスト内容",
            variables={},
        )

        # Act & Assert
        with pytest.raises(PromptTestTimeoutError) as exc_info:
            service.test_prompt(request)
        assert "GS-406" in str(exc_info.value)

    def test_test_prompt_api_error_raises_error(self, service: PromptService) -> None:
        """AI API呼び出し失敗時にGS-407エラーが発生する."""
        # Arrange
        mock_registry = MagicMock()
        mock_provider = MagicMock()
        mock_provider.analyze.side_effect = RuntimeError("API Error")
        mock_registry.get_provider.return_value = mock_provider
        service._ai_provider_registry = mock_registry

        request = TestPromptRequest(
            content="テスト内容",
            variables={},
        )

        # Act & Assert
        with pytest.raises(PromptTestError) as exc_info:
            service.test_prompt(request)
        assert "GS-407" in str(exc_info.value)

    def test_test_prompt_no_provider_registry_raises_error(
        self, service: PromptService
    ) -> None:
        """AIプロバイダーレジストリ未設定時にエラーが発生する."""
        # service has no AI provider registry by default
        request = TestPromptRequest(
            content="テスト内容",
            variables={},
        )

        # Act & Assert
        with pytest.raises(PromptTestError):
            service.test_prompt(request)

    def test_test_prompt_no_provider_available_raises_error(
        self, service: PromptService
    ) -> None:
        """利用可能なプロバイダーがない場合にエラーが発生する."""
        # Arrange
        mock_registry = MagicMock()
        mock_registry.get_provider.return_value = None
        service._ai_provider_registry = mock_registry

        request = TestPromptRequest(
            content="テスト内容",
            variables={},
        )

        # Act & Assert
        with pytest.raises(PromptTestError):
            service.test_prompt(request)

    def test_test_prompt_returns_elapsed_ms(self, service: PromptService) -> None:
        """実行時間がミリ秒で返される."""
        # Arrange
        mock_registry = MagicMock()
        mock_provider = MagicMock()
        mock_provider.provider_type.value = "openai"
        mock_provider._config.model = "gpt-4"
        mock_provider.analyze.return_value = MagicMock(
            content="結果",
            provider_type="openai",
            model="gpt-4",
        )
        mock_registry.get_provider.return_value = mock_provider
        service._ai_provider_registry = mock_registry

        request = TestPromptRequest(
            content="テスト",
            variables={},
        )

        # Act
        result = service.test_prompt(request)

        # Assert
        assert isinstance(result.elapsed_ms, int)
        assert result.elapsed_ms >= 0


# =============================================================================
# Task 4.3: edit lock tests
# =============================================================================


class TestPromptServiceEditLock:
    """Tests for edit lock management (要件2.5)."""

    def test_acquire_edit_lock_success(
        self, service: PromptService, db_session: Session
    ) -> None:
        """編集ロックを取得できる."""
        # Arrange
        _seed_prompt(db_session, key="lock_test")

        # Act
        result = service.acquire_edit_lock("lock_test", "admin_user")

        # Assert
        assert result.acquired is True
        assert result.locked_by == "admin_user"

    def test_acquire_edit_lock_conflict(
        self, service: PromptService, db_session: Session
    ) -> None:
        """他のユーザーが編集中の場合はGS-405エラーが発生する."""
        # Arrange
        now = datetime.now(timezone.utc)
        _seed_prompt(
            db_session,
            key="conflict_test",
            editing_by="other_user",
            editing_since=now,
        )

        # Act
        result = service.acquire_edit_lock("conflict_test", "admin_user")

        # Assert
        assert result.acquired is False
        assert result.locked_by == "other_user"
        assert result.error_code == "GS-405"

    def test_acquire_edit_lock_same_user_reacquires(
        self, service: PromptService, db_session: Session
    ) -> None:
        """同じユーザーが再取得する場合は成功する."""
        # Arrange
        now = datetime.now(timezone.utc)
        _seed_prompt(
            db_session,
            key="same_user_test",
            editing_by="admin_user",
            editing_since=now,
        )

        # Act
        result = service.acquire_edit_lock("same_user_test", "admin_user")

        # Assert
        assert result.acquired is True

    def test_acquire_edit_lock_expired_lock(
        self, service: PromptService, db_session: Session
    ) -> None:
        """30分以上前のロックは無効として取得できる."""
        # Arrange
        old_time = datetime.now(timezone.utc) - timedelta(minutes=31)
        _seed_prompt(
            db_session,
            key="expired_lock_test",
            editing_by="old_user",
            editing_since=old_time,
        )

        # Act
        result = service.acquire_edit_lock("expired_lock_test", "new_user")

        # Assert
        assert result.acquired is True
        assert result.locked_by == "new_user"

    def test_acquire_edit_lock_nonexistent_raises_error(
        self, service: PromptService
    ) -> None:
        """存在しないプロンプトのロックはエラーを発生させる."""
        with pytest.raises(PromptNotFoundError):
            service.acquire_edit_lock("nonexistent", "user")

    def test_release_edit_lock_success(
        self, service: PromptService, db_session: Session
    ) -> None:
        """編集ロックを解放できる."""
        # Arrange
        now = datetime.now(timezone.utc)
        _seed_prompt(
            db_session,
            key="release_test",
            editing_by="admin_user",
            editing_since=now,
        )

        # Act
        service.release_edit_lock("release_test", "admin_user")

        # Assert - verify lock is released
        prompt = (
            db_session.query(PromptModel)
            .filter(PromptModel.key == "release_test")
            .first()
        )
        assert prompt is not None
        assert prompt.editing_by is None
        assert prompt.editing_since is None

    def test_release_edit_lock_nonexistent_raises_error(
        self, service: PromptService
    ) -> None:
        """存在しないプロンプトのロック解放はエラーを発生させる."""
        with pytest.raises(PromptNotFoundError):
            service.release_edit_lock("nonexistent", "user")

    def test_release_edit_lock_by_different_user_still_releases(
        self, service: PromptService, db_session: Session
    ) -> None:
        """異なるユーザーでもロック解放は動作する（管理者用途）."""
        # Arrange
        now = datetime.now(timezone.utc)
        _seed_prompt(
            db_session,
            key="diff_user_release",
            editing_by="user_a",
            editing_since=now,
        )

        # Act - admin releases user_a's lock
        service.release_edit_lock("diff_user_release", "admin")

        # Assert
        prompt = (
            db_session.query(PromptModel)
            .filter(PromptModel.key == "diff_user_release")
            .first()
        )
        assert prompt is not None
        assert prompt.editing_by is None

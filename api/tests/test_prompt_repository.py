"""PromptRepository unit tests.

TDD implementation for prompt data access layer.
Tests cover CRUD operations, category filtering, default protection,
edit lock, and reset functionality.
"""
from datetime import datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.database.base import BaseModel
from models.database.prompt import PromptModel
from models.enums.prompt_category import PromptCategory
from services.prompt_repository import (CreatePromptData, PromptRepository,
                                        UpdatePromptData)


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
def repository(db_session: Session) -> PromptRepository:
    """Create PromptRepository instance."""
    return PromptRepository(db_session)


def _create_sample_prompt(db_session: Session, **overrides) -> PromptModel:
    """Helper to create a sample prompt directly in DB."""
    defaults = {
        "key": "test_prompt",
        "name": "テストプロンプト",
        "description": "テスト用プロンプト",
        "category": PromptCategory.GENERAL,
        "content": "テスト内容",
        "default_content": "テスト内容",
        "variables": [],
        "is_modified": False,
    }
    defaults.update(overrides)
    prompt = PromptModel(**defaults)
    db_session.add(prompt)
    db_session.commit()
    db_session.refresh(prompt)
    return prompt


# =============================================================================
# Create operation tests
# =============================================================================


class TestPromptRepositoryCreate:
    """Tests for create operation (シード用)."""

    def test_create_prompt_success(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """プロンプトの作成が正しく動作する."""
        # Arrange
        data = CreatePromptData(
            key="story_generation_system",
            name="ストーリー生成システムプロンプト",
            description="ストーリー生成に使用するシステムプロンプト",
            category=PromptCategory.STORY_GENERATION,
            content="あなたはアジャイル開発の専門家です。",
            default_content="あなたはアジャイル開発の専門家です。",
            variables=["inquiry_content", "template_content"],
        )

        # Act
        prompt = repository.create(data)

        # Assert
        assert prompt.id is not None
        assert prompt.key == "story_generation_system"
        assert prompt.name == "ストーリー生成システムプロンプト"
        assert prompt.description == "ストーリー生成に使用するシステムプロンプト"
        assert prompt.category == PromptCategory.STORY_GENERATION
        assert prompt.content == "あなたはアジャイル開発の専門家です。"
        assert prompt.default_content == "あなたはアジャイル開発の専門家です。"
        assert prompt.variables == ["inquiry_content", "template_content"]
        assert prompt.is_modified is False
        assert prompt.created_at is not None
        assert prompt.updated_at is not None

    def test_create_prompt_without_description(
        self, repository: PromptRepository
    ) -> None:
        """descriptionなしでプロンプトを作成できる."""
        # Arrange
        data = CreatePromptData(
            key="no_desc_prompt",
            name="説明なしプロンプト",
            category=PromptCategory.GENERAL,
            content="テスト内容",
            default_content="テスト内容",
            variables=[],
        )

        # Act
        prompt = repository.create(data)

        # Assert
        assert prompt.description is None

    def test_create_prompt_with_empty_variables(
        self, repository: PromptRepository
    ) -> None:
        """空の変数リストでプロンプトを作成できる."""
        # Arrange
        data = CreatePromptData(
            key="empty_vars_prompt",
            name="変数なしプロンプト",
            category=PromptCategory.GENERAL,
            content="固定テキスト",
            default_content="固定テキスト",
            variables=[],
        )

        # Act
        prompt = repository.create(data)

        # Assert
        assert prompt.variables == []

    def test_create_prompt_persistence(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """作成されたプロンプトがDBに永続化される."""
        # Arrange
        data = CreatePromptData(
            key="persist_test",
            name="永続化テスト",
            category=PromptCategory.IMPORT_ANALYSIS,
            content="内容",
            default_content="内容",
            variables=[],
        )

        # Act
        repository.create(data)

        # Assert
        assert db_session.query(PromptModel).count() == 1


# =============================================================================
# Find by key tests
# =============================================================================


class TestPromptRepositoryFindByKey:
    """Tests for find_by_key operation (要件1.2)."""

    def test_find_by_key_success(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """キーでプロンプトを取得できる."""
        # Arrange
        _create_sample_prompt(db_session, key="find_me")

        # Act
        found = repository.find_by_key("find_me")

        # Assert
        assert found is not None
        assert found.key == "find_me"

    def test_find_by_key_not_found(self, repository: PromptRepository) -> None:
        """存在しないキーの場合Noneを返す."""
        # Act
        result = repository.find_by_key("nonexistent_key")

        # Assert
        assert result is None

    def test_find_by_key_returns_all_fields(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """find_by_keyが全フィールドを返す."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="full_fields",
            name="全フィールドテスト",
            description="説明文",
            category=PromptCategory.STORY_GENERATION,
            content="カスタム内容",
            default_content="デフォルト内容",
            variables=["var1", "var2"],
            is_modified=True,
        )

        # Act
        found = repository.find_by_key("full_fields")

        # Assert
        assert found is not None
        assert found.name == "全フィールドテスト"
        assert found.description == "説明文"
        assert found.category == PromptCategory.STORY_GENERATION
        assert found.content == "カスタム内容"
        assert found.default_content == "デフォルト内容"
        assert found.variables == ["var1", "var2"]
        assert found.is_modified is True


# =============================================================================
# Find all tests
# =============================================================================


class TestPromptRepositoryFindAll:
    """Tests for find_all operation (要件1.1, 1.3)."""

    def test_find_all_returns_all_prompts(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """全プロンプトを取得できる."""
        # Arrange
        _create_sample_prompt(db_session, key="prompt_1")
        _create_sample_prompt(db_session, key="prompt_2")
        _create_sample_prompt(db_session, key="prompt_3")

        # Act
        results = repository.find_all()

        # Assert
        assert len(results) == 3

    def test_find_all_returns_empty_when_no_prompts(
        self, repository: PromptRepository
    ) -> None:
        """プロンプトが存在しない場合は空リストを返す."""
        # Act
        results = repository.find_all()

        # Assert
        assert results == []

    def test_find_all_with_category_filter(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """カテゴリフィルタリングが正しく動作する."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="sg_prompt",
            category=PromptCategory.STORY_GENERATION,
        )
        _create_sample_prompt(
            db_session,
            key="ia_prompt",
            category=PromptCategory.IMPORT_ANALYSIS,
        )
        _create_sample_prompt(
            db_session,
            key="gen_prompt",
            category=PromptCategory.GENERAL,
        )

        # Act
        story_prompts = repository.find_all(category=PromptCategory.STORY_GENERATION)

        # Assert
        assert len(story_prompts) == 1
        assert story_prompts[0].key == "sg_prompt"

    def test_find_all_with_import_analysis_filter(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """import_analysisカテゴリでフィルタリングできる."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="sg_prompt_2",
            category=PromptCategory.STORY_GENERATION,
        )
        _create_sample_prompt(
            db_session,
            key="ia_prompt_2",
            category=PromptCategory.IMPORT_ANALYSIS,
        )

        # Act
        ia_prompts = repository.find_all(category=PromptCategory.IMPORT_ANALYSIS)

        # Assert
        assert len(ia_prompts) == 1
        assert ia_prompts[0].key == "ia_prompt_2"

    def test_find_all_without_filter_returns_all(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """フィルタなしで全プロンプトを返す."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="all_1",
            category=PromptCategory.STORY_GENERATION,
        )
        _create_sample_prompt(
            db_session,
            key="all_2",
            category=PromptCategory.IMPORT_ANALYSIS,
        )
        _create_sample_prompt(
            db_session,
            key="all_3",
            category=PromptCategory.GENERAL,
        )

        # Act
        results = repository.find_all(category=None)

        # Assert
        assert len(results) == 3


# =============================================================================
# Update tests
# =============================================================================


class TestPromptRepositoryUpdate:
    """Tests for update operation (要件2.2)."""

    def test_update_content_success(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """プロンプト内容を更新できる."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="update_test",
            content="元の内容",
            default_content="元の内容",
        )
        update_data = UpdatePromptData(content="更新された内容")

        # Act
        updated = repository.update("update_test", update_data)

        # Assert
        assert updated is not None
        assert updated.content == "更新された内容"

    def test_update_auto_calculates_is_modified_true(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """更新時にis_modifiedがTrueに自動計算される（contentがdefault_contentと異なる場合）."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="modified_test",
            content="デフォルト内容",
            default_content="デフォルト内容",
            is_modified=False,
        )
        update_data = UpdatePromptData(content="カスタム内容")

        # Act
        updated = repository.update("modified_test", update_data)

        # Assert
        assert updated is not None
        assert updated.is_modified is True

    def test_update_auto_calculates_is_modified_false(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """更新時にis_modifiedがFalseに自動計算される（contentがdefault_contentと同じ場合）."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="unmodified_test",
            content="カスタム内容",
            default_content="デフォルト内容",
            is_modified=True,
        )
        update_data = UpdatePromptData(content="デフォルト内容")

        # Act
        updated = repository.update("unmodified_test", update_data)

        # Assert
        assert updated is not None
        assert updated.is_modified is False

    def test_update_does_not_modify_default_content(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """更新時にdefault_contentは変更されない."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="protect_default_test",
            content="元の内容",
            default_content="デフォルト内容",
        )
        update_data = UpdatePromptData(content="新しい内容")

        # Act
        updated = repository.update("protect_default_test", update_data)

        # Assert
        assert updated is not None
        assert updated.default_content == "デフォルト内容"

    def test_update_description(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """説明を更新できる."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="desc_update_test",
            description="元の説明",
        )
        update_data = UpdatePromptData(description="新しい説明")

        # Act
        updated = repository.update("desc_update_test", update_data)

        # Assert
        assert updated is not None
        assert updated.description == "新しい説明"

    def test_update_updates_timestamp(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """更新時にupdated_atが更新される."""
        # Arrange
        prompt = _create_sample_prompt(db_session, key="timestamp_test")
        original_updated_at = prompt.updated_at
        update_data = UpdatePromptData(content="新しい内容")

        # Act
        updated = repository.update("timestamp_test", update_data)

        # Assert
        assert updated is not None
        assert updated.updated_at >= original_updated_at

    def test_update_nonexistent_key_returns_none(
        self, repository: PromptRepository
    ) -> None:
        """存在しないキーの更新はNoneを返す."""
        # Arrange
        update_data = UpdatePromptData(content="新しい内容")

        # Act
        result = repository.update("nonexistent_key", update_data)

        # Assert
        assert result is None

    def test_update_content_only_leaves_description_unchanged(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """contentのみ更新時にdescriptionは変更されない."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="partial_update_test",
            description="元の説明",
            content="元の内容",
            default_content="元の内容",
        )
        update_data = UpdatePromptData(content="新しい内容")

        # Act
        updated = repository.update("partial_update_test", update_data)

        # Assert
        assert updated is not None
        assert updated.description == "元の説明"
        assert updated.content == "新しい内容"


# =============================================================================
# Reset to default tests
# =============================================================================


class TestPromptRepositoryResetToDefault:
    """Tests for reset_to_default operation (要件4.4)."""

    def test_reset_to_default_success(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """デフォルトにリセットできる."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="reset_test",
            content="カスタム内容",
            default_content="デフォルト内容",
            is_modified=True,
        )

        # Act
        reset = repository.reset_to_default("reset_test")

        # Assert
        assert reset is not None
        assert reset.content == "デフォルト内容"
        assert reset.is_modified is False

    def test_reset_to_default_preserves_default_content(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """リセット時にdefault_contentは保持される."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="preserve_default_test",
            content="変更された内容",
            default_content="オリジナルデフォルト",
            is_modified=True,
        )

        # Act
        reset = repository.reset_to_default("preserve_default_test")

        # Assert
        assert reset is not None
        assert reset.default_content == "オリジナルデフォルト"

    def test_reset_to_default_updates_timestamp(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """リセット時にupdated_atが更新される."""
        # Arrange
        prompt = _create_sample_prompt(
            db_session,
            key="reset_ts_test",
            content="カスタム内容",
            default_content="デフォルト内容",
        )
        original_updated_at = prompt.updated_at

        # Act
        reset = repository.reset_to_default("reset_ts_test")

        # Assert
        assert reset is not None
        assert reset.updated_at >= original_updated_at

    def test_reset_nonexistent_key_returns_none(
        self, repository: PromptRepository
    ) -> None:
        """存在しないキーのリセットはNoneを返す."""
        # Act
        result = repository.reset_to_default("nonexistent_key")

        # Assert
        assert result is None

    def test_reset_already_default_prompt(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """既にデフォルトのプロンプトをリセットしても正常動作する."""
        # Arrange
        _create_sample_prompt(
            db_session,
            key="already_default_test",
            content="デフォルト内容",
            default_content="デフォルト内容",
            is_modified=False,
        )

        # Act
        reset = repository.reset_to_default("already_default_test")

        # Assert
        assert reset is not None
        assert reset.content == "デフォルト内容"
        assert reset.is_modified is False


# =============================================================================
# Edit lock tests
# =============================================================================


class TestPromptRepositoryUpdateEditLock:
    """Tests for update_edit_lock operation (要件2.5)."""

    def test_acquire_edit_lock(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """編集ロックを取得できる."""
        # Arrange
        _create_sample_prompt(db_session, key="lock_test")
        now = datetime.now(timezone.utc)

        # Act
        locked = repository.update_edit_lock("lock_test", "admin_user", now)

        # Assert
        assert locked is not None
        assert locked.editing_by == "admin_user"
        assert locked.editing_since is not None

    def test_release_edit_lock(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """編集ロックを解放できる."""
        # Arrange
        now = datetime.now(timezone.utc)
        _create_sample_prompt(
            db_session,
            key="release_lock_test",
            editing_by="admin_user",
            editing_since=now,
        )

        # Act
        released = repository.update_edit_lock("release_lock_test", None, None)

        # Assert
        assert released is not None
        assert released.editing_by is None
        assert released.editing_since is None

    def test_update_edit_lock_nonexistent_key(
        self, repository: PromptRepository
    ) -> None:
        """存在しないキーのロック操作はNoneを返す."""
        # Act
        result = repository.update_edit_lock(
            "nonexistent_key", "user", datetime.now(timezone.utc)
        )

        # Assert
        assert result is None

    def test_edit_lock_overwrite(
        self, repository: PromptRepository, db_session: Session
    ) -> None:
        """既存のロックを上書きできる."""
        # Arrange
        now = datetime.now(timezone.utc)
        _create_sample_prompt(
            db_session,
            key="overwrite_lock_test",
            editing_by="user_1",
            editing_since=now,
        )
        new_time = datetime.now(timezone.utc)

        # Act
        updated = repository.update_edit_lock("overwrite_lock_test", "user_2", new_time)

        # Assert
        assert updated is not None
        assert updated.editing_by == "user_2"

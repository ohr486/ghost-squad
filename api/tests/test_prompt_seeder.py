"""PromptSeeder unit tests.

TDD implementation for default prompt seeding.
Tests cover initial seeding, idempotency, existing data protection,
and default prompt definitions.

Requirements: 4.1, 4.2, 4.3
"""
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.database.base import BaseModel
from models.enums.prompt_category import PromptCategory
from services.prompt_repository import PromptRepository


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


# =============================================================================
# Default prompt definitions tests
# =============================================================================


class TestDefaultPromptDefinitions:
    """Tests for default prompt definitions (要件4.1, 4.2)."""

    def test_default_prompts_is_list(self) -> None:
        """DEFAULT_PROMPTSがリストとして定義されている."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        assert isinstance(DEFAULT_PROMPTS, list)

    def test_default_prompts_not_empty(self) -> None:
        """DEFAULT_PROMPTSが空でない."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        assert len(DEFAULT_PROMPTS) > 0

    def test_default_prompts_have_required_fields(self) -> None:
        """各デフォルトプロンプトに必要なフィールドが存在する."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        required_fields = [
            "key",
            "name",
            "description",
            "category",
            "content",
            "variables",
        ]
        for prompt_def in DEFAULT_PROMPTS:
            for field in required_fields:
                key = prompt_def.get("key", "unknown")
                assert field in prompt_def, (
                    f"Missing field '{field}' in " f"prompt definition '{key}'"
                )

    def test_default_prompts_have_unique_keys(self) -> None:
        """各デフォルトプロンプトのキーが一意である."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        keys = [p["key"] for p in DEFAULT_PROMPTS]
        assert len(keys) == len(set(keys)), "Duplicate keys found in DEFAULT_PROMPTS"

    def test_story_generation_system_prompt_exists(self) -> None:
        """ストーリー生成システムプロンプトが定義されている."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        keys = [p["key"] for p in DEFAULT_PROMPTS]
        assert "story_generation_system" in keys

    def test_story_generation_user_prompt_exists(self) -> None:
        """ストーリー生成ユーザープロンプトが定義されている."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        keys = [p["key"] for p in DEFAULT_PROMPTS]
        assert "story_generation_user" in keys

    def test_import_analysis_system_prompt_exists(self) -> None:
        """インポート解析システムプロンプトが定義されている."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        keys = [p["key"] for p in DEFAULT_PROMPTS]
        assert "import_analysis_system" in keys

    def test_story_generation_system_prompt_category(self) -> None:
        """ストーリー生成システムプロンプトのカテゴリがstory_generationである."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        prompt = next(
            p for p in DEFAULT_PROMPTS if p["key"] == "story_generation_system"
        )
        assert prompt["category"] == PromptCategory.STORY_GENERATION

    def test_story_generation_user_prompt_category(self) -> None:
        """ストーリー生成ユーザープロンプトのカテゴリがstory_generationである."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        prompt = next(p for p in DEFAULT_PROMPTS if p["key"] == "story_generation_user")
        assert prompt["category"] == PromptCategory.STORY_GENERATION

    def test_import_analysis_system_prompt_category(self) -> None:
        """インポート解析システムプロンプトのカテゴリがimport_analysisである."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        prompt = next(
            p for p in DEFAULT_PROMPTS if p["key"] == "import_analysis_system"
        )
        assert prompt["category"] == PromptCategory.IMPORT_ANALYSIS

    def test_story_generation_user_prompt_has_inquiry_content_variable(self) -> None:
        """ストーリー生成ユーザープロンプトにinquiry_content変数が定義されている."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        prompt = next(p for p in DEFAULT_PROMPTS if p["key"] == "story_generation_user")
        assert "inquiry_content" in prompt["variables"]

    def test_story_generation_system_prompt_content_not_empty(
        self,
    ) -> None:
        """ストーリー生成システムプロンプトの内容が空でない."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        prompt = next(
            p for p in DEFAULT_PROMPTS if p["key"] == "story_generation_system"
        )
        assert prompt["content"].strip() != ""

    def test_import_analysis_system_prompt_content_not_empty(
        self,
    ) -> None:
        """インポート解析システムプロンプトの内容が空でない."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        prompt = next(
            p for p in DEFAULT_PROMPTS if p["key"] == "import_analysis_system"
        )
        assert prompt["content"].strip() != ""

    def test_story_generation_user_prompt_contains_placeholder(self) -> None:
        """ストーリー生成ユーザープロンプトに{inquiry_content}プレースホルダーが含まれる."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        prompt = next(p for p in DEFAULT_PROMPTS if p["key"] == "story_generation_user")
        assert "{inquiry_content}" in prompt["content"]

    def test_all_categories_are_valid(self) -> None:
        """全デフォルトプロンプトのカテゴリが有効なPromptCategoryである."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        for prompt_def in DEFAULT_PROMPTS:
            assert isinstance(
                prompt_def["category"], PromptCategory
            ), f"Invalid category for prompt '{prompt_def['key']}'"

    def test_all_variables_are_string_lists(self) -> None:
        """全デフォルトプロンプトのvariablesがstring型リストである."""
        from services.prompt_defaults import DEFAULT_PROMPTS

        for prompt_def in DEFAULT_PROMPTS:
            assert isinstance(
                prompt_def["variables"], list
            ), f"Variables should be a list for prompt '{prompt_def['key']}'"
            for var in prompt_def["variables"]:
                assert isinstance(
                    var, str
                ), f"Variable should be a string for prompt '{prompt_def['key']}'"


# =============================================================================
# PromptSeeder initial seed tests
# =============================================================================


class TestPromptSeederInitialSeed:
    """Tests for initial seed operation (要件4.1)."""

    def test_seed_creates_all_default_prompts(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """初回シードで全デフォルトプロンプトが作成される."""
        from services.prompt_defaults import DEFAULT_PROMPTS
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)

        # Act
        seeder.seed()

        # Assert
        all_prompts = repository.find_all()
        assert len(all_prompts) == len(DEFAULT_PROMPTS)

    def test_seed_creates_story_generation_system_prompt(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """初回シードでストーリー生成システムプロンプトが作成される."""
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        # Assert
        prompt = repository.find_by_key("story_generation_system")
        assert prompt is not None
        assert prompt.category == PromptCategory.STORY_GENERATION

    def test_seed_creates_story_generation_user_prompt(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """初回シードでストーリー生成ユーザープロンプトが作成される."""
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        # Assert
        prompt = repository.find_by_key("story_generation_user")
        assert prompt is not None
        assert prompt.category == PromptCategory.STORY_GENERATION

    def test_seed_creates_import_analysis_system_prompt(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """初回シードでインポート解析システムプロンプトが作成される."""
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        # Assert
        prompt = repository.find_by_key("import_analysis_system")
        assert prompt is not None
        assert prompt.category == PromptCategory.IMPORT_ANALYSIS

    def test_seed_sets_content_equal_to_default_content(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """シード時にcontentとdefault_contentが同じ値に設定される."""
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        # Assert
        all_prompts = repository.find_all()
        for prompt in all_prompts:
            assert (
                prompt.content == prompt.default_content
            ), f"content and default_content should be equal for '{prompt.key}'"

    def test_seed_sets_is_modified_false(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """シード時にis_modifiedがFalseに設定される."""
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        # Assert
        all_prompts = repository.find_all()
        for prompt in all_prompts:
            assert (
                prompt.is_modified is False
            ), f"is_modified should be False for '{prompt.key}'"

    def test_seed_returns_count_of_created_prompts(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """シード処理が作成されたプロンプト数を返す."""
        from services.prompt_defaults import DEFAULT_PROMPTS
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)

        # Act
        result = seeder.seed()

        # Assert
        assert result.created == len(DEFAULT_PROMPTS)
        assert result.skipped == 0

    def test_seed_sets_correct_variables(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """シード時に正しいvariablesが設定される."""
        from services.prompt_defaults import DEFAULT_PROMPTS
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        # Assert
        for prompt_def in DEFAULT_PROMPTS:
            prompt = repository.find_by_key(prompt_def["key"])
            assert prompt is not None
            assert (
                prompt.variables == prompt_def["variables"]
            ), f"Variables mismatch for '{prompt_def['key']}'"


# =============================================================================
# PromptSeeder idempotency tests
# =============================================================================


class TestPromptSeederIdempotency:
    """Tests for seed idempotency (要件4.1 - 冪等性)."""

    def test_seed_twice_does_not_duplicate(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """2回シードしてもプロンプトが重複しない."""
        from services.prompt_defaults import DEFAULT_PROMPTS
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)

        # Act: seed twice
        seeder.seed()
        seeder.seed()

        # Assert
        all_prompts = repository.find_all()
        assert len(all_prompts) == len(DEFAULT_PROMPTS)

    def test_second_seed_returns_zero_created(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """2回目のシードでcreatedが0を返す."""
        from services.prompt_defaults import DEFAULT_PROMPTS
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)

        # Act
        seeder.seed()
        result = seeder.seed()

        # Assert
        assert result.created == 0
        assert result.skipped == len(DEFAULT_PROMPTS)

    def test_seed_does_not_overwrite_existing_content(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """シードが既存プロンプトの内容を上書きしない（要件4.2 - デフォルト保護）."""
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        # Modify one prompt's content
        prompt = repository.find_by_key("story_generation_system")
        assert prompt is not None
        original_default = prompt.default_content
        prompt.content = "カスタマイズされた内容"
        prompt.is_modified = True
        db_session.commit()

        # Act: seed again
        seeder.seed()

        # Assert: customized content is preserved
        prompt = repository.find_by_key("story_generation_system")
        assert prompt is not None
        assert prompt.content == "カスタマイズされた内容"
        assert prompt.default_content == original_default

    def test_seed_preserves_edit_lock(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """シードが既存プロンプトの編集ロックを上書きしない."""
        from datetime import datetime, timezone

        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        # Set edit lock
        now = datetime.now(timezone.utc)
        repository.update_edit_lock("story_generation_system", "admin_user", now)

        # Act: seed again
        seeder.seed()

        # Assert: edit lock is preserved
        prompt = repository.find_by_key("story_generation_system")
        assert prompt is not None
        assert prompt.editing_by == "admin_user"


# =============================================================================
# PromptSeeder default protection tests
# =============================================================================


class TestPromptSeederDefaultProtection:
    """Tests for default value protection (要件4.2)."""

    def test_default_content_is_system_defined(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """デフォルト値がシステム定義として設定される."""
        from services.prompt_defaults import DEFAULT_PROMPTS
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        # Assert: default_content matches definition
        for prompt_def in DEFAULT_PROMPTS:
            prompt = repository.find_by_key(prompt_def["key"])
            assert prompt is not None
            assert (
                prompt.default_content == prompt_def["content"]
            ), f"default_content mismatch for '{prompt_def['key']}'"

    def test_default_content_matches_hardcoded_story_generation_system(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """ストーリー生成システムプロンプトのデフォルトが現行ハードコード値と一致する."""
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        prompt = repository.find_by_key("story_generation_system")
        assert prompt is not None
        # The system message from StoryGenerationService
        assert "アジャイル開発の専門家" in prompt.default_content

    def test_default_content_matches_hardcoded_import_analysis_system(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """インポート解析システムプロンプトのデフォルトが現行ハードコード値と一致する."""
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        prompt = repository.find_by_key("import_analysis_system")
        assert prompt is not None
        # The ANALYSIS_SYSTEM_PROMPT from OpenAI/Anthropic providers
        assert "問い合わせ解析の専門家" in prompt.default_content

    def test_default_content_matches_hardcoded_story_generation_user(
        self, db_session: Session, repository: PromptRepository
    ) -> None:
        """ストーリー生成ユーザープロンプトのデフォルトが現行ハードコード値と一致する."""
        from services.prompt_seeder import PromptSeeder

        seeder = PromptSeeder(repository)
        seeder.seed()

        prompt = repository.find_by_key("story_generation_user")
        assert prompt is not None
        # The user prompt template from StoryGenerationService
        assert "ユーザーストーリーを生成" in prompt.default_content
        assert "{inquiry_content}" in prompt.default_content


# =============================================================================
# PromptSeeder SeedResult tests
# =============================================================================


class TestSeedResult:
    """Tests for SeedResult dataclass."""

    def test_seed_result_attributes(self) -> None:
        """SeedResultが正しい属性を持つ."""
        from services.prompt_seeder import SeedResult

        result = SeedResult(created=3, skipped=0)
        assert result.created == 3
        assert result.skipped == 0

    def test_seed_result_total(self) -> None:
        """SeedResult.totalがcreated + skippedを返す."""
        from services.prompt_seeder import SeedResult

        result = SeedResult(created=2, skipped=1)
        assert result.total == 3

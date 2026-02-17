"""プロンプトモデルのテスト."""
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from models.database.base import Base
from models.database.prompt import PromptModel
from models.enums.prompt_category import PromptCategory


@pytest.fixture
def db_engine():
    """テスト用データベースエンジン."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """テスト用インメモリデータベースセッション."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


class TestPromptModel:
    """PromptModelのテストクラス."""

    def test_create_prompt_with_all_fields(self, db_session):
        """すべてのフィールドを持つプロンプトを作成できる."""
        # Arrange
        now = datetime.now(UTC)
        prompt = PromptModel(
            key="story_generation_system",
            name="ストーリー生成システムプロンプト",
            description="ストーリー生成に使用するシステムプロンプト",
            category=PromptCategory.STORY_GENERATION,
            content="あなたはアジャイル開発の専門家です。",
            default_content="あなたはアジャイル開発の専門家です。",
            variables=["inquiry_content", "template_content"],
            is_modified=False,
            editing_by="admin_user",
            editing_since=now,
        )

        # Act
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)

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
        assert prompt.editing_by == "admin_user"
        assert prompt.editing_since is not None
        assert prompt.created_at is not None
        assert prompt.updated_at is not None

    def test_prompt_key_is_unique(self, db_session):
        """keyフィールドはユニークである."""
        # Arrange
        prompt1 = PromptModel(
            key="unique_key",
            name="プロンプト1",
            category=PromptCategory.GENERAL,
            content="内容1",
            default_content="内容1",
        )
        prompt2 = PromptModel(
            key="unique_key",
            name="プロンプト2",
            category=PromptCategory.GENERAL,
            content="内容2",
            default_content="内容2",
        )

        # Act & Assert
        db_session.add(prompt1)
        db_session.commit()
        db_session.add(prompt2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_prompt_requires_key(self, db_session):
        """keyフィールドは必須である."""
        # Arrange & Act & Assert
        prompt = PromptModel(
            key=None,
            name="テストプロンプト",
            category=PromptCategory.GENERAL,
            content="テスト内容",
            default_content="テスト内容",
        )
        db_session.add(prompt)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_prompt_requires_name(self, db_session):
        """nameフィールドは必須である."""
        # Arrange & Act & Assert
        prompt = PromptModel(
            key="test_key",
            name=None,
            category=PromptCategory.GENERAL,
            content="テスト内容",
            default_content="テスト内容",
        )
        db_session.add(prompt)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_prompt_requires_content(self, db_session):
        """contentフィールドは必須である."""
        # Arrange & Act & Assert
        prompt = PromptModel(
            key="test_key",
            name="テストプロンプト",
            category=PromptCategory.GENERAL,
            content=None,
            default_content="テスト内容",
        )
        db_session.add(prompt)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_prompt_requires_default_content(self, db_session):
        """default_contentフィールドは必須である."""
        # Arrange & Act & Assert
        prompt = PromptModel(
            key="test_key",
            name="テストプロンプト",
            category=PromptCategory.GENERAL,
            content="テスト内容",
            default_content=None,
        )
        db_session.add(prompt)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_prompt_requires_category(self, db_session):
        """categoryフィールドは必須である."""
        # Arrange & Act & Assert
        prompt = PromptModel(
            key="test_key",
            name="テストプロンプト",
            category=None,
            content="テスト内容",
            default_content="テスト内容",
        )
        db_session.add(prompt)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_prompt_variables_defaults_to_empty_list(self, db_session):
        """variablesのデフォルトが空リストである."""
        # Arrange & Act
        prompt = PromptModel(
            key="test_default_vars",
            name="テストプロンプト",
            category=PromptCategory.GENERAL,
            content="テスト内容",
            default_content="テスト内容",
        )
        db_session.add(prompt)
        db_session.commit()

        # Assert
        assert prompt.variables == []

    def test_prompt_is_modified_defaults_to_false(self, db_session):
        """is_modifiedのデフォルトがFalseである."""
        # Arrange & Act
        prompt = PromptModel(
            key="test_default_modified",
            name="テストプロンプト",
            category=PromptCategory.GENERAL,
            content="テスト内容",
            default_content="テスト内容",
        )
        db_session.add(prompt)
        db_session.commit()

        # Assert
        assert prompt.is_modified is False

    def test_prompt_editing_fields_default_to_none(self, db_session):
        """editing_by/editing_sinceのデフォルトがNoneである."""
        # Arrange & Act
        prompt = PromptModel(
            key="test_default_editing",
            name="テストプロンプト",
            category=PromptCategory.GENERAL,
            content="テスト内容",
            default_content="テスト内容",
        )
        db_session.add(prompt)
        db_session.commit()

        # Assert
        assert prompt.editing_by is None
        assert prompt.editing_since is None

    def test_prompt_description_can_be_null(self, db_session):
        """descriptionフィールドはNULLでも可能."""
        # Arrange & Act
        prompt = PromptModel(
            key="test_nullable_desc",
            name="テストプロンプト",
            category=PromptCategory.GENERAL,
            content="テスト内容",
            default_content="テスト内容",
            description=None,
        )
        db_session.add(prompt)
        db_session.commit()

        # Assert
        assert prompt.description is None

    def test_prompt_category_story_generation(self, db_session):
        """story_generationカテゴリのプロンプトを作成できる."""
        # Arrange & Act
        prompt = PromptModel(
            key="story_gen_test",
            name="ストーリー生成",
            category=PromptCategory.STORY_GENERATION,
            content="内容",
            default_content="内容",
        )
        db_session.add(prompt)
        db_session.commit()

        # Assert
        assert prompt.category == PromptCategory.STORY_GENERATION

    def test_prompt_category_import_analysis(self, db_session):
        """import_analysisカテゴリのプロンプトを作成できる."""
        # Arrange & Act
        prompt = PromptModel(
            key="import_analysis_test",
            name="インポート解析",
            category=PromptCategory.IMPORT_ANALYSIS,
            content="内容",
            default_content="内容",
        )
        db_session.add(prompt)
        db_session.commit()

        # Assert
        assert prompt.category == PromptCategory.IMPORT_ANALYSIS

    def test_prompt_category_general(self, db_session):
        """generalカテゴリのプロンプトを作成できる."""
        # Arrange & Act
        prompt = PromptModel(
            key="general_test",
            name="汎用",
            category=PromptCategory.GENERAL,
            content="内容",
            default_content="内容",
        )
        db_session.add(prompt)
        db_session.commit()

        # Assert
        assert prompt.category == PromptCategory.GENERAL

    def test_prompt_repr(self, db_session):
        """PromptModelの文字列表現が適切である."""
        # Arrange & Act
        prompt = PromptModel(
            key="repr_test",
            name="テスト",
            category=PromptCategory.GENERAL,
            content="内容",
            default_content="内容",
        )
        db_session.add(prompt)
        db_session.commit()

        # Assert
        repr_str = repr(prompt)
        assert "PromptModel" in repr_str
        assert "repr_test" in repr_str
        assert "general" in repr_str


class TestPromptModelCRUDOperations:
    """PromptModelのCRUD操作テストクラス."""

    def test_prompt_create_operation(self, db_session):
        """プロンプトの作成操作が正しく動作する."""
        # Arrange
        prompt = PromptModel(
            key="crud_create",
            name="作成テスト",
            category=PromptCategory.GENERAL,
            content="テスト内容",
            default_content="テスト内容",
        )

        # Act
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)

        # Assert
        assert prompt.id is not None
        assert prompt.key == "crud_create"
        assert prompt.created_at is not None

    def test_prompt_read_operation(self, db_session):
        """プロンプトの取得操作が正しく動作する."""
        # Arrange
        prompt = PromptModel(
            key="crud_read",
            name="読み取りテスト",
            category=PromptCategory.STORY_GENERATION,
            content="テスト内容",
            default_content="テスト内容",
        )
        db_session.add(prompt)
        db_session.commit()
        prompt_id = prompt.id

        # Act
        db_session.expunge_all()
        retrieved = db_session.query(PromptModel).filter_by(id=prompt_id).first()

        # Assert
        assert retrieved is not None
        assert retrieved.key == "crud_read"
        assert retrieved.category == PromptCategory.STORY_GENERATION

    def test_prompt_read_by_key(self, db_session):
        """キーによるプロンプトの取得が正しく動作する."""
        # Arrange
        prompt = PromptModel(
            key="crud_read_by_key",
            name="キー検索テスト",
            category=PromptCategory.IMPORT_ANALYSIS,
            content="テスト内容",
            default_content="テスト内容",
        )
        db_session.add(prompt)
        db_session.commit()

        # Act
        db_session.expunge_all()
        retrieved = (
            db_session.query(PromptModel).filter_by(key="crud_read_by_key").first()
        )

        # Assert
        assert retrieved is not None
        assert retrieved.name == "キー検索テスト"

    def test_prompt_update_operation(self, db_session):
        """プロンプトの更新操作が正しく動作する."""
        # Arrange
        prompt = PromptModel(
            key="crud_update",
            name="更新前",
            category=PromptCategory.GENERAL,
            content="元の内容",
            default_content="元の内容",
        )
        db_session.add(prompt)
        db_session.commit()

        # Act
        prompt.content = "更新された内容"
        prompt.is_modified = True
        db_session.commit()
        db_session.refresh(prompt)

        # Assert
        assert prompt.content == "更新された内容"
        assert prompt.is_modified is True

    def test_prompt_delete_operation(self, db_session):
        """プロンプトの削除操作が正しく動作する."""
        # Arrange
        prompt = PromptModel(
            key="crud_delete",
            name="削除テスト",
            category=PromptCategory.GENERAL,
            content="テスト内容",
            default_content="テスト内容",
        )
        db_session.add(prompt)
        db_session.commit()
        prompt_id = prompt.id

        # Act
        db_session.delete(prompt)
        db_session.commit()

        # Assert
        deleted = db_session.query(PromptModel).filter_by(id=prompt_id).first()
        assert deleted is None

    def test_prompt_filter_by_category(self, db_session):
        """カテゴリによるフィルタリングが正しく動作する."""
        # Arrange
        prompts = [
            PromptModel(
                key="filter_sg",
                name="SG",
                category=PromptCategory.STORY_GENERATION,
                content="内容",
                default_content="内容",
            ),
            PromptModel(
                key="filter_ia",
                name="IA",
                category=PromptCategory.IMPORT_ANALYSIS,
                content="内容",
                default_content="内容",
            ),
            PromptModel(
                key="filter_gen",
                name="GEN",
                category=PromptCategory.GENERAL,
                content="内容",
                default_content="内容",
            ),
        ]
        db_session.add_all(prompts)
        db_session.commit()

        # Act
        story_prompts = (
            db_session.query(PromptModel)
            .filter_by(category=PromptCategory.STORY_GENERATION)
            .all()
        )

        # Assert
        assert len(story_prompts) == 1
        assert story_prompts[0].key == "filter_sg"

    def test_prompt_variables_json_storage(self, db_session):
        """variables（JSON）フィールドの保存・取得が正しく動作する."""
        # Arrange
        variables = ["inquiry_content", "template_content", "user_name"]
        prompt = PromptModel(
            key="json_test",
            name="JSONテスト",
            category=PromptCategory.STORY_GENERATION,
            content="内容 {inquiry_content} {template_content} {user_name}",
            default_content="内容",
            variables=variables,
        )

        # Act
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)

        # Assert
        assert prompt.variables == variables
        assert len(prompt.variables) == 3

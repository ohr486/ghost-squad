"""プロンプト管理E2E統合テスト.

Task 10.1: バックエンド統合テスト
- API→Service E2Eフローテスト（シード→一覧→更新→リセット）
- テスト実行フロー統合テスト（AIプロバイダーモック）
- 既存サービス統合テスト（StoryGenerationServiceがPromptServiceを使用）
- デフォルトシーダー起動時テスト

Requirements: 1.1, 2.2, 3.1, 4.1, 5.1, 5.2
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import get_db
from main import app
from models.database.base import Base
from models.database.prompt import PromptModel
from models.enums.prompt_category import PromptCategory
from services.prompt_defaults import DEFAULT_PROMPTS
from services.prompt_repository import PromptRepository
from services.prompt_seeder import PromptSeeder

# テスト用データベースの設定（shared in-memory SQLiteを使用）
SQLALCHEMY_DATABASE_URL = "sqlite:///file:test_e2e_prompt_db?mode=memory&cache=shared&uri=true"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False, "uri": True},
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
    from models.database.prompt import PromptModel as _  # noqa: F401

    Base.metadata.create_all(bind=engine)

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    if original_override is not None:
        app.dependency_overrides[get_db] = original_override
    else:
        app.dependency_overrides.pop(get_db, None)

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def cleanup_database():
    """各テスト後にデータベースをクリーンアップする."""
    yield
    db = TestingSessionLocal()
    try:
        db.query(PromptModel).delete()
        db.commit()
    finally:
        db.close()


def seed_defaults():
    """テスト用にデフォルトプロンプトをシードする."""
    db = TestingSessionLocal()
    try:
        repository = PromptRepository(db)
        seeder = PromptSeeder(repository)
        result = seeder.seed()
        return result
    finally:
        db.close()


# =========================================================================
# E2E フロー 1: シード → 一覧取得 → 更新 → リセット
# =========================================================================


class TestPromptE2EFlow:
    """API→Serviceの一貫したE2Eフローテスト."""

    def test_seed_then_list_all(self, client):
        """シード後に全プロンプトを一覧取得できる."""
        # Arrange: デフォルトプロンプトをシード
        seed_defaults()

        # Act: 一覧取得
        response = client.get("/api/prompts")

        # Assert: デフォルトプロンプトが全て取得できる
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == len(DEFAULT_PROMPTS)
        keys = [p["key"] for p in data["data"]]
        for prompt_def in DEFAULT_PROMPTS:
            assert prompt_def["key"] in keys

    def test_seed_then_get_detail(self, client):
        """シード後に個別プロンプトの詳細を取得できる."""
        seed_defaults()

        # Act: 詳細取得
        response = client.get("/api/prompts/story_generation_system")

        # Assert: 正しいデフォルト内容が返される
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["key"] == "story_generation_system"
        assert data["name"] == "ストーリー生成システムプロンプト"
        assert data["category"] == "story_generation"
        assert data["is_modified"] is False
        assert data["content"] == data["default_content"]

    def test_seed_then_update_then_verify(self, client):
        """シード → 更新 → 更新内容の確認フロー."""
        seed_defaults()

        # Act: プロンプトを更新
        update_response = client.put(
            "/api/prompts/story_generation_system",
            json={"content": "カスタムシステムプロンプト"},
        )
        assert update_response.status_code == status.HTTP_200_OK

        # Assert: 更新結果の確認
        updated = update_response.json()
        assert updated["content"] == "カスタムシステムプロンプト"
        assert updated["is_modified"] is True

        # Act: 再取得で永続化を確認
        get_response = client.get("/api/prompts/story_generation_system")
        assert get_response.status_code == status.HTTP_200_OK
        persisted = get_response.json()
        assert persisted["content"] == "カスタムシステムプロンプト"
        assert persisted["is_modified"] is True
        assert persisted["default_content"] != persisted["content"]

    def test_seed_update_then_reset(self, client):
        """シード → 更新 → リセット → デフォルトに戻るフロー."""
        seed_defaults()

        # Arrange: プロンプトを更新
        client.put(
            "/api/prompts/story_generation_system",
            json={"content": "一時的なカスタム内容"},
        )

        # Act: リセット
        reset_response = client.post("/api/prompts/story_generation_system/reset")
        assert reset_response.status_code == status.HTTP_200_OK

        # Assert: デフォルトに戻っている
        reset_data = reset_response.json()
        assert reset_data["content"] == reset_data["default_content"]
        assert reset_data["is_modified"] is False

        # Act: 再取得で永続化を確認
        get_response = client.get("/api/prompts/story_generation_system")
        persisted = get_response.json()
        assert persisted["content"] == persisted["default_content"]
        assert persisted["is_modified"] is False

    def test_seed_then_filter_by_category(self, client):
        """シード後にカテゴリフィルタリングが動作する."""
        seed_defaults()

        # Act: story_generationカテゴリでフィルター
        response = client.get("/api/prompts?category=story_generation")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Assert: story_generationカテゴリのプロンプトのみ取得
        assert data["total"] >= 1
        for item in data["data"]:
            assert item["category"] == "story_generation"

        # Act: import_analysisカテゴリでフィルター
        response2 = client.get("/api/prompts?category=import_analysis")
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["total"] >= 1
        for item in data2["data"]:
            assert item["category"] == "import_analysis"

    def test_full_edit_flow_with_lock(self, client):
        """ロック取得 → 編集 → 保存 → ロック解放の完全フロー."""
        seed_defaults()

        # Act 1: ロック取得
        lock_response = client.post(
            "/api/prompts/story_generation_system/lock",
            json={"user_id": "test_editor"},
        )
        assert lock_response.status_code == status.HTTP_200_OK
        lock_data = lock_response.json()
        assert lock_data["acquired"] is True

        # Act 2: 他ユーザーがロック取得を試みる → 競合
        conflict_response = client.post(
            "/api/prompts/story_generation_system/lock",
            json={"user_id": "other_user"},
        )
        assert conflict_response.status_code == status.HTTP_409_CONFLICT

        # Act 3: 編集者がプロンプトを更新
        update_response = client.put(
            "/api/prompts/story_generation_system",
            json={"content": "ロック中に更新した内容"},
        )
        assert update_response.status_code == status.HTTP_200_OK

        # Act 4: ロック解放
        release_response = client.delete(
            "/api/prompts/story_generation_system/lock",
        )
        assert release_response.status_code == status.HTTP_204_NO_CONTENT

        # Assert: 更新が永続化されている
        get_response = client.get("/api/prompts/story_generation_system")
        final_data = get_response.json()
        assert final_data["content"] == "ロック中に更新した内容"
        assert final_data["is_modified"] is True


# =========================================================================
# E2E フロー 2: テスト実行フロー（AIプロバイダーモック使用）
# =========================================================================


class TestPromptTestExecutionE2E:
    """テスト実行フローの統合テスト."""

    def test_test_execution_with_seeded_prompt(self, client):
        """シード済みプロンプトの内容でテスト実行できる."""
        seed_defaults()

        # Arrange: シード済みプロンプトの内容を取得
        get_response = client.get("/api/prompts/story_generation_system")
        prompt_content = get_response.json()["content"]

        # Act: テスト実行（AIプロバイダーモック）
        mock_result = MagicMock()
        mock_result.output = "テスト出力結果"
        mock_result.provider = "openai"
        mock_result.model = "gpt-4"
        mock_result.elapsed_ms = 1200

        with patch("routers.prompt.PromptService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.test_prompt.return_value = mock_result
            mock_svc_cls.return_value = mock_svc

            response = client.post(
                "/api/prompts/test",
                json={
                    "content": prompt_content,
                    "variables": {},
                },
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["output"] == "テスト出力結果"
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"

    def test_test_execution_with_variables(self, client):
        """変数付きプロンプトのテスト実行フロー."""
        seed_defaults()

        # Arrange: 変数付きプロンプトの内容を取得
        get_response = client.get("/api/prompts/story_generation_user")
        prompt_data = get_response.json()
        assert "inquiry_content" in prompt_data["variables"]

        # Act: 変数付きテスト実行
        mock_result = MagicMock()
        mock_result.output = "生成されたストーリー"
        mock_result.provider = "anthropic"
        mock_result.model = "claude-3"
        mock_result.elapsed_ms = 2500

        with patch("routers.prompt.PromptService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.test_prompt.return_value = mock_result
            mock_svc_cls.return_value = mock_svc

            response = client.post(
                "/api/prompts/test",
                json={
                    "content": prompt_data["content"],
                    "variables": {"inquiry_content": "ログイン画面の改善"},
                    "provider": "anthropic",
                },
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["output"] == "生成されたストーリー"
        assert data["provider"] == "anthropic"

    def test_test_execution_with_updated_prompt(self, client):
        """更新後のプロンプトでテスト実行できる."""
        seed_defaults()

        # Arrange: プロンプトを更新
        client.put(
            "/api/prompts/story_generation_system",
            json={"content": "カスタマイズ済みプロンプト"},
        )

        # Act: 更新後の内容でテスト実行
        mock_result = MagicMock()
        mock_result.output = "カスタム出力"
        mock_result.provider = "openai"
        mock_result.model = "gpt-4"
        mock_result.elapsed_ms = 800

        with patch("routers.prompt.PromptService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.test_prompt.return_value = mock_result
            mock_svc_cls.return_value = mock_svc

            response = client.post(
                "/api/prompts/test",
                json={
                    "content": "カスタマイズ済みプロンプト",
                    "variables": {},
                },
            )

        assert response.status_code == status.HTTP_200_OK

    def test_test_execution_timeout_handling(self, client):
        """テスト実行タイムアウト時の処理."""
        from services.prompt_service import PromptTestTimeoutError

        with patch("routers.prompt.PromptService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.test_prompt.side_effect = PromptTestTimeoutError(
                "GS-406: タイムアウト"
            )
            mock_svc_cls.return_value = mock_svc

            response = client.post(
                "/api/prompts/test",
                json={
                    "content": "タイムアウトテスト",
                    "variables": {},
                },
            )

        assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT


# =========================================================================
# E2E フロー 3: 既存サービス統合テスト
# =========================================================================


class TestExistingServiceIntegration:
    """既存サービスがプロンプト管理サービスと連携するテスト."""

    def test_story_generation_uses_seeded_prompts(self):
        """StoryGenerationServiceがシード済みプロンプトを使用する."""
        from services.prompt_service import PromptData

        # Arrange: シード済みプロンプトを模倣するPromptServiceモック
        mock_prompt_service = MagicMock()

        system_data = PromptData(
            id=1,
            key="story_generation_system",
            name="ストーリー生成システムプロンプト",
            description=None,
            category="story_generation",
            content="カスタムシステムプロンプト（DB由来）",
            default_content="デフォルトシステムプロンプト",
            variables=[],
            is_modified=True,
        )
        user_data = PromptData(
            id=2,
            key="story_generation_user",
            name="ストーリー生成ユーザープロンプト",
            description=None,
            category="story_generation",
            content="カスタムユーザープロンプト: {inquiry_content}",
            default_content="デフォルトユーザープロンプト",
            variables=["inquiry_content"],
            is_modified=True,
        )

        def get_prompt_side_effect(key):
            if key == "story_generation_system":
                return system_data
            elif key == "story_generation_user":
                return user_data
            raise Exception(f"Unknown key: {key}")

        mock_prompt_service.get_prompt.side_effect = get_prompt_side_effect

        # Act: StoryGenerationServiceにPromptServiceを注入
        from services.story_generation_service import StoryGenerationService

        mock_session = MagicMock()
        with patch(
            "services.story_generation_service.OpenAI"
        ) as mock_openai, patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test-key-1234567890ab"},
        ):
            mock_openai.return_value = MagicMock()
            service = StoryGenerationService(
                mock_session, prompt_service=mock_prompt_service
            )

        # Assert: プロンプトを取得してカスタム内容が使用される
        system_prompt, user_prompt = service._get_prompts("テスト問い合わせ")
        assert system_prompt == "カスタムシステムプロンプト（DB由来）"
        assert "テスト問い合わせ" in user_prompt
        mock_prompt_service.get_prompt.assert_any_call("story_generation_system")
        mock_prompt_service.get_prompt.assert_any_call("story_generation_user")

    def test_story_generation_fallback_without_prompt_service(self):
        """PromptServiceがない場合、既存のハードコードにフォールバックする."""
        from services.story_generation_service import StoryGenerationService

        mock_session = MagicMock()
        with patch(
            "services.story_generation_service.OpenAI"
        ) as mock_openai, patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test-key-1234567890ab"},
        ):
            mock_openai.return_value = MagicMock()
            service = StoryGenerationService(mock_session)

        # Assert: フォールバックプロンプトが使用される
        system_prompt, user_prompt = service._get_prompts("フォールバックテスト")
        assert len(system_prompt) > 0
        assert "アジャイル開発の専門家" in system_prompt
        assert "フォールバックテスト" in user_prompt


# =========================================================================
# E2E フロー 4: デフォルトシーダー起動テスト
# =========================================================================


class TestDefaultSeederStartup:
    """デフォルトシーダーの起動時動作テスト."""

    def test_seeder_creates_all_defaults(self):
        """シーダーが全デフォルトプロンプトを作成する."""
        result = seed_defaults()

        assert result.created == len(DEFAULT_PROMPTS)
        assert result.skipped == 0
        assert result.total == len(DEFAULT_PROMPTS)

    def test_seeder_is_idempotent(self):
        """シーダーは冪等（2回実行しても既存を上書きしない）."""
        # 1回目: 全て新規作成
        result1 = seed_defaults()
        assert result1.created == len(DEFAULT_PROMPTS)
        assert result1.skipped == 0

        # 2回目: 全てスキップ（既存のため）
        db = TestingSessionLocal()
        try:
            repository = PromptRepository(db)
            seeder = PromptSeeder(repository)
            result2 = seeder.seed()
        finally:
            db.close()

        assert result2.created == 0
        assert result2.skipped == len(DEFAULT_PROMPTS)

    def test_seeder_preserves_modified_prompts(self):
        """シーダーはカスタマイズ済みプロンプトを上書きしない."""
        # 1回目: シード
        seed_defaults()

        # プロンプトをカスタマイズ
        db = TestingSessionLocal()
        try:
            prompt = (
                db.query(PromptModel)
                .filter(PromptModel.key == "story_generation_system")
                .first()
            )
            prompt.content = "カスタマイズ済み"
            prompt.is_modified = True
            db.commit()
        finally:
            db.close()

        # 2回目: 再シード
        db = TestingSessionLocal()
        try:
            repository = PromptRepository(db)
            seeder = PromptSeeder(repository)
            seeder.seed()
        finally:
            db.close()

        # Assert: カスタマイズ内容が保持されている
        db = TestingSessionLocal()
        try:
            prompt = (
                db.query(PromptModel)
                .filter(PromptModel.key == "story_generation_system")
                .first()
            )
            assert prompt.content == "カスタマイズ済み"
            assert prompt.is_modified is True
        finally:
            db.close()

    def test_seeder_creates_correct_categories(self):
        """シーダーが正しいカテゴリでプロンプトを作成する."""
        seed_defaults()

        db = TestingSessionLocal()
        try:
            # story_generationカテゴリ
            story_prompts = (
                db.query(PromptModel)
                .filter(PromptModel.category == PromptCategory.STORY_GENERATION)
                .all()
            )
            assert len(story_prompts) >= 2  # system + user

            # import_analysisカテゴリ
            import_prompts = (
                db.query(PromptModel)
                .filter(PromptModel.category == PromptCategory.IMPORT_ANALYSIS)
                .all()
            )
            assert len(import_prompts) >= 1
        finally:
            db.close()

    def test_seeder_sets_content_equal_to_default(self):
        """シーダーがcontent=default_contentで作成する."""
        seed_defaults()

        db = TestingSessionLocal()
        try:
            prompts = db.query(PromptModel).all()
            for prompt in prompts:
                assert prompt.content == prompt.default_content
                assert prompt.is_modified is False
        finally:
            db.close()

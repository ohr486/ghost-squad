"""プロンプト管理APIテスト.

Task 6.1: プロンプト一覧・詳細・更新エンドポイント
Task 6.2: テスト実行・リセット・編集ロックエンドポイント

Requirements: 1.1, 1.2, 1.3, 2.2, 2.5, 3.1, 3.2, 3.4, 4.4, 4.5
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

# テスト用データベースの設定（shared in-memory SQLiteを使用）
SQLALCHEMY_DATABASE_URL = (
    "sqlite:///file:test_prompt_db" "?mode=memory&cache=shared&uri=true"
)
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


@pytest.fixture
def sample_prompt():
    """テスト用プロンプトを作成する."""
    db = TestingSessionLocal()
    try:
        prompt = PromptModel(
            key="test_prompt",
            name="テストプロンプト",
            description="テスト用の説明",
            category=PromptCategory.STORY_GENERATION,
            content="テスト内容",
            default_content="テスト内容",
            variables=[],
            is_modified=False,
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        return prompt
    finally:
        db.close()


@pytest.fixture
def sample_prompt_with_vars():
    """変数付きテスト用プロンプトを作成する."""
    db = TestingSessionLocal()
    try:
        prompt = PromptModel(
            key="test_prompt_vars",
            name="変数付きプロンプト",
            description="変数テスト用",
            category=PromptCategory.IMPORT_ANALYSIS,
            content="内容: {name}",
            default_content="内容: {name}",
            variables=["name"],
            is_modified=False,
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        return prompt
    finally:
        db.close()


@pytest.fixture
def multiple_prompts():
    """複数のテスト用プロンプトを作成する."""
    db = TestingSessionLocal()
    try:
        prompts = [
            PromptModel(
                key="story_sys",
                name="ストーリーシステム",
                description=None,
                category=PromptCategory.STORY_GENERATION,
                content="システムプロンプト",
                default_content="システムプロンプト",
                variables=[],
                is_modified=False,
            ),
            PromptModel(
                key="story_user",
                name="ストーリーユーザー",
                description="ユーザープロンプト",
                category=PromptCategory.STORY_GENERATION,
                content="ユーザープロンプト {inquiry}",
                default_content="ユーザープロンプト {inquiry}",
                variables=["inquiry"],
                is_modified=False,
            ),
            PromptModel(
                key="import_sys",
                name="インポートシステム",
                description="解析用",
                category=PromptCategory.IMPORT_ANALYSIS,
                content="解析プロンプト",
                default_content="解析プロンプト",
                variables=[],
                is_modified=False,
            ),
        ]
        for p in prompts:
            db.add(p)
        db.commit()
        for p in prompts:
            db.refresh(p)
        return prompts
    finally:
        db.close()


@pytest.fixture
def modified_prompt():
    """デフォルトから変更されたプロンプトを作成する."""
    db = TestingSessionLocal()
    try:
        prompt = PromptModel(
            key="modified_prompt",
            name="変更済みプロンプト",
            description="変更テスト",
            category=PromptCategory.STORY_GENERATION,
            content="変更後の内容",
            default_content="デフォルト内容",
            variables=[],
            is_modified=True,
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        return prompt
    finally:
        db.close()


# =========================================================================
# Task 6.1: GET /api/prompts - プロンプト一覧
# =========================================================================


class TestListPrompts:
    """プロンプト一覧取得エンドポイントのテスト."""

    def test_list_prompts_empty(self, client):
        """プロンプトが存在しない場合、空リストを返す."""
        response = client.get("/api/prompts")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    def test_list_prompts_returns_all(self, client, multiple_prompts):
        """全プロンプトを返す."""
        response = client.get("/api/prompts")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert len(data["data"]) == 3

    def test_list_prompts_filter_by_category(self, client, multiple_prompts):
        """カテゴリフィルターで絞り込める."""
        response = client.get("/api/prompts?category=story_generation")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        for item in data["data"]:
            assert item["category"] == "story_generation"

    def test_list_prompts_filter_import_analysis(self, client, multiple_prompts):
        """import_analysisカテゴリでフィルターできる."""
        response = client.get("/api/prompts?category=import_analysis")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["key"] == "import_sys"

    def test_list_prompts_invalid_category(self, client):
        """無効なカテゴリでは400エラーを返す."""
        response = client.get("/api/prompts?category=invalid_category")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_prompts_response_fields(self, client, sample_prompt):
        """レスポンスに必要なフィールドが含まれる."""
        response = client.get("/api/prompts")
        data = response.json()
        item = data["data"][0]
        assert "id" in item
        assert "key" in item
        assert "name" in item
        assert "category" in item
        assert "content" in item
        assert "default_content" in item
        assert "variables" in item
        assert "is_modified" in item
        assert "created_at" in item
        assert "updated_at" in item


# =========================================================================
# Task 6.1: GET /api/prompts/{key} - プロンプト詳細
# =========================================================================


class TestGetPrompt:
    """プロンプト詳細取得エンドポイントのテスト."""

    def test_get_prompt_success(self, client, sample_prompt):
        """キーでプロンプトを取得できる."""
        response = client.get("/api/prompts/test_prompt")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["key"] == "test_prompt"
        assert data["name"] == "テストプロンプト"
        assert data["description"] == "テスト用の説明"
        assert data["category"] == "story_generation"
        assert data["content"] == "テスト内容"
        assert data["default_content"] == "テスト内容"
        assert data["variables"] == []
        assert data["is_modified"] is False

    def test_get_prompt_not_found(self, client):
        """存在しないキーでは404を返す."""
        response = client.get("/api/prompts/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    def test_get_prompt_shows_modified_flag(self, client, modified_prompt):
        """変更されたプロンプトのis_modifiedがTrueになる."""
        response = client.get("/api/prompts/modified_prompt")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_modified"] is True
        assert data["content"] != data["default_content"]

    def test_get_prompt_with_variables(self, client, sample_prompt_with_vars):
        """変数付きプロンプトの変数リストが正しく返る."""
        response = client.get("/api/prompts/test_prompt_vars")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["variables"] == ["name"]


# =========================================================================
# Task 6.1: PUT /api/prompts/{key} - プロンプト更新
# =========================================================================


class TestUpdatePrompt:
    """プロンプト更新エンドポイントのテスト."""

    def test_update_prompt_success(self, client, sample_prompt):
        """プロンプトを正常に更新できる."""
        response = client.put(
            "/api/prompts/test_prompt",
            json={"content": "更新後の内容"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "更新後の内容"
        assert data["is_modified"] is True

    def test_update_prompt_with_description(self, client, sample_prompt):
        """説明付きで更新できる."""
        response = client.put(
            "/api/prompts/test_prompt",
            json={
                "content": "更新後の内容",
                "description": "新しい説明",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "新しい説明"

    def test_update_prompt_not_found(self, client):
        """存在しないプロンプトの更新は404を返す."""
        response = client.put(
            "/api/prompts/nonexistent",
            json={"content": "内容"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_prompt_empty_content(self, client, sample_prompt):
        """空の本文では422エラーを返す（Pydanticバリデーション）."""
        response = client.put(
            "/api/prompts/test_prompt",
            json={"content": ""},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_prompt_preserves_default(self, client, sample_prompt):
        """更新してもデフォルト値は保持される."""
        client.put(
            "/api/prompts/test_prompt",
            json={"content": "新しい内容"},
        )
        response = client.get("/api/prompts/test_prompt")
        data = response.json()
        assert data["default_content"] == "テスト内容"
        assert data["content"] == "新しい内容"


# =========================================================================
# Task 6.2: POST /api/prompts/{key}/reset - デフォルトリセット
# =========================================================================


class TestResetPrompt:
    """プロンプトリセットエンドポイントのテスト."""

    def test_reset_prompt_success(self, client, modified_prompt):
        """変更されたプロンプトをデフォルトにリセットできる."""
        response = client.post("/api/prompts/modified_prompt/reset")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == data["default_content"]
        assert data["is_modified"] is False

    def test_reset_prompt_not_found(self, client):
        """存在しないプロンプトのリセットは404を返す."""
        response = client.post("/api/prompts/nonexistent/reset")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =========================================================================
# Task 6.2: POST /api/prompts/{key}/lock - 編集ロック取得
# =========================================================================


class TestAcquireLock:
    """編集ロック取得エンドポイントのテスト."""

    def test_acquire_lock_success(self, client, sample_prompt):
        """編集ロックを取得できる."""
        response = client.post(
            "/api/prompts/test_prompt/lock",
            json={"user_id": "admin_user"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["acquired"] is True
        assert data["locked_by"] == "admin_user"
        assert data["locked_since"] is not None

    def test_acquire_lock_conflict(self, client, sample_prompt):
        """他のユーザーが編集中は409を返す."""
        # まずロックを取得
        client.post(
            "/api/prompts/test_prompt/lock",
            json={"user_id": "user_a"},
        )
        # 別のユーザーがロックを取得しようとする
        response = client.post(
            "/api/prompts/test_prompt/lock",
            json={"user_id": "user_b"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_acquire_lock_not_found(self, client):
        """存在しないプロンプトへのロック取得は404を返す."""
        response = client.post(
            "/api/prompts/nonexistent/lock",
            json={"user_id": "admin_user"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_acquire_lock_same_user(self, client, sample_prompt):
        """同一ユーザーはロックを再取得できる."""
        client.post(
            "/api/prompts/test_prompt/lock",
            json={"user_id": "admin_user"},
        )
        response = client.post(
            "/api/prompts/test_prompt/lock",
            json={"user_id": "admin_user"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["acquired"] is True


# =========================================================================
# Task 6.2: DELETE /api/prompts/{key}/lock - 編集ロック解放
# =========================================================================


class TestReleaseLock:
    """編集ロック解放エンドポイントのテスト."""

    def test_release_lock_success(self, client, sample_prompt):
        """編集ロックを解放できる."""
        client.post(
            "/api/prompts/test_prompt/lock",
            json={"user_id": "admin_user"},
        )
        response = client.delete("/api/prompts/test_prompt/lock")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_release_lock_not_found(self, client):
        """存在しないプロンプトのロック解放は404を返す."""
        response = client.delete("/api/prompts/nonexistent/lock")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =========================================================================
# Task 6.2: POST /api/prompts/test - テスト実行
# =========================================================================


class TestTestPrompt:
    """テスト実行エンドポイントのテスト."""

    def test_test_prompt_success(self, client):
        """テスト実行が正常に動作する."""
        mock_result = MagicMock()
        mock_result.output = "AI出力結果"
        mock_result.provider = "openai"
        mock_result.model = "gpt-4"
        mock_result.elapsed_ms = 1500

        with patch("routers.prompt.PromptService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.test_prompt.return_value = mock_result
            mock_svc_cls.return_value = mock_svc

            response = client.post(
                "/api/prompts/test",
                json={
                    "content": "テストプロンプト",
                    "variables": {},
                },
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["output"] == "AI出力結果"
            assert data["provider"] == "openai"
            assert data["model"] == "gpt-4"
            assert data["elapsed_ms"] == 1500

    def test_test_prompt_empty_content(self, client):
        """空のコンテンツでは422エラーを返す."""
        response = client.post(
            "/api/prompts/test",
            json={"content": "", "variables": {}},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_test_prompt_timeout(self, client):
        """タイムアウト時は504を返す."""
        from services.prompt_service import PromptTestTimeoutError

        with patch("routers.prompt.PromptService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.test_prompt.side_effect = PromptTestTimeoutError("GS-406: タイムアウト")
            mock_svc_cls.return_value = mock_svc

            response = client.post(
                "/api/prompts/test",
                json={
                    "content": "テスト",
                    "variables": {},
                },
            )
            assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT

    def test_test_prompt_ai_error(self, client):
        """AI APIエラー時は500を返す."""
        from services.prompt_service import PromptTestError

        with patch("routers.prompt.PromptService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.test_prompt.side_effect = PromptTestError("GS-407: AI APIエラー")
            mock_svc_cls.return_value = mock_svc

            response = client.post(
                "/api/prompts/test",
                json={
                    "content": "テスト",
                    "variables": {},
                },
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_test_prompt_with_variables(self, client):
        """変数付きテスト実行が動作する."""
        mock_result = MagicMock()
        mock_result.output = "結果"
        mock_result.provider = "anthropic"
        mock_result.model = "claude-3"
        mock_result.elapsed_ms = 2000

        with patch("routers.prompt.PromptService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.test_prompt.return_value = mock_result
            mock_svc_cls.return_value = mock_svc

            response = client.post(
                "/api/prompts/test",
                json={
                    "content": "テスト {name}",
                    "variables": {"name": "テスト値"},
                    "provider": "anthropic",
                },
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["provider"] == "anthropic"

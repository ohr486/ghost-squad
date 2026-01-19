"""AIプロバイダー管理API - Integration Tests.

タスク 10.2: AIプロバイダー管理APIの実装
- GET /api/ai-providers - プロバイダー一覧取得
- POST /api/ai-providers/{type}/set-default - デフォルト設定

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """テストクライアントを提供する."""
    with TestClient(app) as test_client:
        yield test_client


class TestAIProviderListEndpoint:
    """GET /api/ai-providers エンドポイントのテスト."""

    def test_list_ai_providers_empty(self, client: TestClient):
        """AIプロバイダー未登録時は空リストを返す.

        要件3.1: カテゴリ判定
        """
        # Mock AIProviderRegistryService
        with patch("routers.importer.get_ai_provider_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.list_providers.return_value = []
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.get("/api/ai-providers")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["data"] == []
            assert "timestamp" in data

    def test_list_ai_providers_with_providers(self, client: TestClient):
        """登録済みAIプロバイダーが一覧表示される.

        要件3.1-3.6: AI解析機能
        """
        from services.importer.ai_provider_base import AIProviderType
        from services.importer.ai_provider_registry import AIProviderStatus

        # Mock AIProviderRegistryService
        with patch("routers.importer.get_ai_provider_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.list_providers.return_value = [
                AIProviderStatus(
                    provider_type=AIProviderType.OPENAI,
                    enabled=True,
                    initialized=True,
                    is_default=True,
                    model="gpt-4",
                    error_message=None,
                ),
                AIProviderStatus(
                    provider_type=AIProviderType.ANTHROPIC,
                    enabled=True,
                    initialized=True,
                    is_default=False,
                    model="claude-3-sonnet-20240229",
                    error_message=None,
                ),
            ]
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.get("/api/ai-providers")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["data"]) == 2
            assert data["data"][0]["provider_type"] == "openai"
            assert data["data"][0]["enabled"] is True
            assert data["data"][0]["initialized"] is True
            assert data["data"][0]["is_default"] is True
            assert data["data"][0]["model"] == "gpt-4"
            assert data["data"][1]["provider_type"] == "anthropic"
            assert data["data"][1]["is_default"] is False

    def test_list_ai_providers_with_error(self, client: TestClient):
        """初期化エラーのあるプロバイダーも表示される.

        要件3.6: 日本語解析
        """
        from services.importer.ai_provider_base import AIProviderType
        from services.importer.ai_provider_registry import AIProviderStatus

        # Mock AIProviderRegistryService
        with patch("routers.importer.get_ai_provider_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.list_providers.return_value = [
                AIProviderStatus(
                    provider_type=AIProviderType.OPENAI,
                    enabled=False,
                    initialized=False,
                    is_default=False,
                    model="gpt-4",
                    error_message="API Keyが無効です",
                ),
            ]
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.get("/api/ai-providers")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["data"]) == 1
            assert data["data"][0]["initialized"] is False
            assert data["data"][0]["error_message"] == "API Keyが無効です"


class TestAIProviderSetDefaultEndpoint:
    """POST /api/ai-providers/{type}/set-default エンドポイントのテスト."""

    def test_set_default_provider_success(self, client: TestClient):
        """デフォルトプロバイダー設定が成功する.

        要件3.1: カテゴリ判定
        """
        from services.importer.ai_provider_base import AIProviderType
        from services.importer.ai_provider_registry import AIProviderStatus
        from services.importer.result import Result

        # Mock AIProviderRegistryService
        with patch("routers.importer.get_ai_provider_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.set_default.return_value = Result.ok(
                AIProviderStatus(
                    provider_type=AIProviderType.ANTHROPIC,
                    enabled=True,
                    initialized=True,
                    is_default=True,
                    model="claude-3-sonnet-20240229",
                    error_message=None,
                )
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/ai-providers/anthropic/set-default")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["provider_type"] == "anthropic"
            assert data["is_default"] is True
            assert data["enabled"] is True
            assert data["initialized"] is True

    def test_set_default_provider_not_found(self, client: TestClient):
        """存在しないプロバイダーのデフォルト設定は404エラー.

        要件3.1: カテゴリ判定
        """
        from services.importer.ai_provider_registry import AIProviderError
        from services.importer.result import Result

        # Mock AIProviderRegistryService
        with patch("routers.importer.get_ai_provider_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.set_default.return_value = Result.err(
                AIProviderError("GS-308", "AIプロバイダー 'unknown' が見つかりません")
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/ai-providers/unknown/set-default")

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "errors" in data["detail"]
            assert data["detail"]["errors"][0]["code"] == "GS-308"

    def test_set_default_provider_invalid_type(self, client: TestClient):
        """無効なプロバイダータイプは404エラー.

        要件3.1: カテゴリ判定
        """
        from services.importer.ai_provider_registry import AIProviderError
        from services.importer.result import Result

        # Mock AIProviderRegistryService
        with patch("routers.importer.get_ai_provider_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.set_default.return_value = Result.err(
                AIProviderError("GS-308", "AIプロバイダー 'invalid' が見つかりません")
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/ai-providers/invalid/set-default")

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAIProviderResponseSchema:
    """AIプロバイダーレスポンススキーマのテスト."""

    def test_response_contains_required_fields(self, client: TestClient):
        """レスポンスに必須フィールドが含まれる."""
        from services.importer.ai_provider_base import AIProviderType
        from services.importer.ai_provider_registry import AIProviderStatus
        from services.importer.result import Result

        # Mock AIProviderRegistryService
        with patch("routers.importer.get_ai_provider_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.set_default.return_value = Result.ok(
                AIProviderStatus(
                    provider_type=AIProviderType.OPENAI,
                    enabled=True,
                    initialized=True,
                    is_default=True,
                    model="gpt-4",
                    error_message=None,
                )
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/ai-providers/openai/set-default")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "provider_type" in data
            assert "enabled" in data
            assert "initialized" in data
            assert "is_default" in data
            assert "model" in data
            # error_message はオプショナル

    def test_error_response_format(self, client: TestClient):
        """エラーレスポンスが統一フォーマットに従う."""
        from services.importer.ai_provider_registry import AIProviderError
        from services.importer.result import Result

        # Mock AIProviderRegistryService
        with patch("routers.importer.get_ai_provider_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.set_default.return_value = Result.err(
                AIProviderError("GS-308", "AIプロバイダー 'unknown' が見つかりません")
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/ai-providers/unknown/set-default")

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "detail" in data
            assert "errors" in data["detail"]
            assert "timestamp" in data["detail"]
            error = data["detail"]["errors"][0]
            assert "code" in error
            assert "message" in error


class TestAIProviderListResponseSchema:
    """AIプロバイダー一覧レスポンススキーマのテスト."""

    def test_list_response_format(self, client: TestClient):
        """一覧レスポンスが統一フォーマットに従う."""
        from services.importer.ai_provider_base import AIProviderType
        from services.importer.ai_provider_registry import AIProviderStatus

        # Mock AIProviderRegistryService
        with patch("routers.importer.get_ai_provider_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.list_providers.return_value = [
                AIProviderStatus(
                    provider_type=AIProviderType.OPENAI,
                    enabled=True,
                    initialized=True,
                    is_default=True,
                    model="gpt-4",
                    error_message=None,
                ),
            ]
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.get("/api/ai-providers")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "data" in data
            assert "timestamp" in data
            assert isinstance(data["data"], list)

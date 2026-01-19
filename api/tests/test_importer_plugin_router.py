"""プラグイン管理API - Integration Tests.

タスク 10.1: プラグイン管理APIの実装
- GET /api/plugins - プラグイン一覧取得
- POST /api/plugins/{type}/enable - プラグイン有効化
- POST /api/plugins/{type}/disable - プラグイン無効化

Requirements: 1.1, 1.2
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


class TestPluginListEndpoint:
    """GET /api/plugins エンドポイントのテスト."""

    def test_list_plugins_empty(self, client: TestClient):
        """プラグイン未登録時は空リストを返す.

        要件1.1: プラグイン登録・解除
        """
        # Mock PluginRegistryService
        with patch(
            "routers.importer.get_plugin_registry"
        ) as mock_get_registry:
            mock_registry = Mock()
            mock_registry.list_plugins.return_value = []
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.get("/api/plugins")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["data"] == []
            assert "timestamp" in data

    def test_list_plugins_with_plugins(self, client: TestClient):
        """登録済みプラグインが一覧表示される.

        要件1.1, 1.2: プラグイン登録・有効/無効管理
        """
        from services.importer.plugin_registry import PluginStatus

        # Mock PluginRegistryService
        with patch(
            "routers.importer.get_plugin_registry"
        ) as mock_get_registry:
            mock_registry = Mock()
            mock_registry.list_plugins.return_value = [
                PluginStatus(
                    plugin_type="email",
                    enabled=True,
                    initialized=True,
                    error_message=None,
                ),
                PluginStatus(
                    plugin_type="sentry",
                    enabled=False,
                    initialized=True,
                    error_message=None,
                ),
            ]
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.get("/api/plugins")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["data"]) == 2
            assert data["data"][0]["plugin_type"] == "email"
            assert data["data"][0]["enabled"] is True
            assert data["data"][0]["initialized"] is True
            assert data["data"][1]["plugin_type"] == "sentry"
            assert data["data"][1]["enabled"] is False

    def test_list_plugins_with_error(self, client: TestClient):
        """初期化エラーのあるプラグインも表示される.

        要件1.5: 初期化失敗時のエラーログ記録と自動無効化
        """
        from services.importer.plugin_registry import PluginStatus

        # Mock PluginRegistryService
        with patch(
            "routers.importer.get_plugin_registry"
        ) as mock_get_registry:
            mock_registry = Mock()
            mock_registry.list_plugins.return_value = [
                PluginStatus(
                    plugin_type="email",
                    enabled=False,
                    initialized=False,
                    error_message="IMAP接続に失敗しました",
                ),
            ]
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.get("/api/plugins")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["data"]) == 1
            assert data["data"][0]["initialized"] is False
            assert data["data"][0]["error_message"] == "IMAP接続に失敗しました"


class TestPluginEnableEndpoint:
    """POST /api/plugins/{type}/enable エンドポイントのテスト."""

    def test_enable_plugin_success(self, client: TestClient):
        """プラグイン有効化が成功する.

        要件1.2: 有効/無効切り替え
        """
        from services.importer.plugin_registry import PluginStatus
        from services.importer.result import Result

        # Mock PluginRegistryService
        with patch(
            "routers.importer.get_plugin_registry"
        ) as mock_get_registry:
            mock_registry = Mock()
            mock_registry.enable.return_value = Result.ok(
                PluginStatus(
                    plugin_type="email",
                    enabled=True,
                    initialized=True,
                    error_message=None,
                )
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/plugins/email/enable")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["plugin_type"] == "email"
            assert data["enabled"] is True
            assert data["initialized"] is True

    def test_enable_plugin_not_found(self, client: TestClient):
        """存在しないプラグインの有効化は404エラー.

        要件1.1: プラグイン登録・解除
        """
        from services.importer.plugin_registry import PluginError
        from services.importer.result import Result

        # Mock PluginRegistryService
        with patch(
            "routers.importer.get_plugin_registry"
        ) as mock_get_registry:
            mock_registry = Mock()
            mock_registry.enable.return_value = Result.err(
                PluginError("GS-301", "プラグイン 'unknown' が見つかりません")
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/plugins/unknown/enable")

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "errors" in data["detail"]
            assert data["detail"]["errors"][0]["code"] == "GS-301"


class TestPluginDisableEndpoint:
    """POST /api/plugins/{type}/disable エンドポイントのテスト."""

    def test_disable_plugin_success(self, client: TestClient):
        """プラグイン無効化が成功する.

        要件1.2: 有効/無効切り替え
        """
        from services.importer.plugin_registry import PluginStatus
        from services.importer.result import Result

        # Mock PluginRegistryService
        with patch(
            "routers.importer.get_plugin_registry"
        ) as mock_get_registry:
            mock_registry = Mock()
            mock_registry.disable.return_value = Result.ok(
                PluginStatus(
                    plugin_type="email",
                    enabled=False,
                    initialized=True,
                    error_message=None,
                )
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/plugins/email/disable")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["plugin_type"] == "email"
            assert data["enabled"] is False
            assert data["initialized"] is True

    def test_disable_plugin_not_found(self, client: TestClient):
        """存在しないプラグインの無効化は404エラー.

        要件1.1: プラグイン登録・解除
        """
        from services.importer.plugin_registry import PluginError
        from services.importer.result import Result

        # Mock PluginRegistryService
        with patch(
            "routers.importer.get_plugin_registry"
        ) as mock_get_registry:
            mock_registry = Mock()
            mock_registry.disable.return_value = Result.err(
                PluginError("GS-301", "プラグイン 'unknown' が見つかりません")
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/plugins/unknown/disable")

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "errors" in data["detail"]
            assert data["detail"]["errors"][0]["code"] == "GS-301"

    def test_disable_already_disabled_plugin(self, client: TestClient):
        """既に無効化されているプラグインの無効化も成功する（冪等性）.

        要件1.2: 有効/無効切り替え
        """
        from services.importer.plugin_registry import PluginStatus
        from services.importer.result import Result

        # Mock PluginRegistryService
        with patch(
            "routers.importer.get_plugin_registry"
        ) as mock_get_registry:
            mock_registry = Mock()
            mock_registry.disable.return_value = Result.ok(
                PluginStatus(
                    plugin_type="email",
                    enabled=False,
                    initialized=True,
                    error_message=None,
                )
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/plugins/email/disable")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["enabled"] is False


class TestPluginResponseSchema:
    """プラグインレスポンススキーマのテスト."""

    def test_response_contains_required_fields(self, client: TestClient):
        """レスポンスに必須フィールドが含まれる."""
        from services.importer.plugin_registry import PluginStatus
        from services.importer.result import Result

        # Mock PluginRegistryService
        with patch(
            "routers.importer.get_plugin_registry"
        ) as mock_get_registry:
            mock_registry = Mock()
            mock_registry.enable.return_value = Result.ok(
                PluginStatus(
                    plugin_type="email",
                    enabled=True,
                    initialized=True,
                    error_message=None,
                )
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/plugins/email/enable")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "plugin_type" in data
            assert "enabled" in data
            assert "initialized" in data
            # error_message はオプショナル（None の場合は含まれない可能性あり）

    def test_error_response_format(self, client: TestClient):
        """エラーレスポンスが統一フォーマットに従う."""
        from services.importer.plugin_registry import PluginError
        from services.importer.result import Result

        # Mock PluginRegistryService
        with patch(
            "routers.importer.get_plugin_registry"
        ) as mock_get_registry:
            mock_registry = Mock()
            mock_registry.enable.return_value = Result.err(
                PluginError("GS-301", "プラグイン 'unknown' が見つかりません")
            )
            mock_get_registry.return_value = mock_registry

            # Act
            response = client.post("/api/plugins/unknown/enable")

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "detail" in data
            assert "errors" in data["detail"]
            assert "timestamp" in data["detail"]
            error = data["detail"]["errors"][0]
            assert "code" in error
            assert "message" in error

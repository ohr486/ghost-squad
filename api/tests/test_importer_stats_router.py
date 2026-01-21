"""エラー統計API - Integration Tests.

タスク 10.4: エラー統計APIの実装
- GET /api/importers/stats - エラー統計取得

Requirements: 5.4
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from routers.importer import set_importer_service


@pytest.fixture
def client():
    """テストクライアントを提供する."""
    with TestClient(app) as test_client:
        yield test_client
    # テスト後にサービスをリセット
    set_importer_service(None)


@pytest.fixture
def mock_importer_service():
    """モックImporterServiceを提供する."""
    mock_service = Mock()
    set_importer_service(mock_service)
    yield mock_service
    set_importer_service(None)


# =============================================================================
# GET /api/importers/stats エンドポイントのテスト
# =============================================================================


class TestGetErrorStatsEndpoint:
    """GET /api/importers/stats エンドポイントのテスト."""

    def test_get_error_stats_success(self, client: TestClient, mock_importer_service):
        """エラー統計取得が成功する.

        要件5.4: エラー統計
        """
        from services.importer.import_error_log_repository import ErrorStats

        mock_importer_service.get_error_stats.return_value = [
            ErrorStats(
                error_code="GS-304",
                count=15,
                last_occurred=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            ),
            ErrorStats(
                error_code="GS-303",
                count=5,
                last_occurred=datetime(2024, 1, 14, 14, 20, 0, tzinfo=timezone.utc),
            ),
        ]

        # Act
        response = client.get("/api/importers/stats")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 2
        assert data["data"][0]["error_code"] == "GS-304"
        assert data["data"][0]["count"] == 15
        assert "last_occurred" in data["data"][0]
        assert data["data"][1]["error_code"] == "GS-303"
        assert data["data"][1]["count"] == 5
        assert "timestamp" in data

    def test_get_error_stats_empty(self, client: TestClient, mock_importer_service):
        """エラーがない場合は空のリストを返す.

        要件5.4: エラー統計
        """
        mock_importer_service.get_error_stats.return_value = []

        # Act
        response = client.get("/api/importers/stats")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"] == []
        assert "timestamp" in data

    def test_get_error_stats_with_plugin_filter(
        self, client: TestClient, mock_importer_service
    ):
        """プラグイン種別でフィルタリングできる.

        要件5.4: エラー統計
        """
        from services.importer.import_error_log_repository import ErrorStats

        mock_importer_service.get_error_stats.return_value = [
            ErrorStats(
                error_code="GS-304",
                count=10,
                last_occurred=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            ),
        ]

        # Act
        response = client.get("/api/importers/stats?plugin_type=email")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["error_code"] == "GS-304"
        # plugin_type引数で呼び出されたことを確認
        mock_importer_service.get_error_stats.assert_called_once_with(
            plugin_type="email"
        )

    def test_get_error_stats_without_plugin_filter(
        self, client: TestClient, mock_importer_service
    ):
        """プラグイン種別フィルタなしの場合は全てのエラーを返す.

        要件5.4: エラー統計
        """
        from services.importer.import_error_log_repository import ErrorStats

        mock_importer_service.get_error_stats.return_value = [
            ErrorStats(
                error_code="GS-304",
                count=20,
                last_occurred=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            ),
        ]

        # Act
        response = client.get("/api/importers/stats")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        # plugin_type=Noneで呼び出されたことを確認
        mock_importer_service.get_error_stats.assert_called_once_with(plugin_type=None)

    def test_get_error_stats_server_error(
        self, client: TestClient, mock_importer_service
    ):
        """サーバーエラーが発生した場合は500エラーを返す.

        要件5.4: エラー統計
        """
        mock_importer_service.get_error_stats.side_effect = Exception("データベース接続エラー")

        # Act
        response = client.get("/api/importers/stats")

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data
        assert "errors" in data["detail"]
        assert data["detail"]["errors"][0]["code"] == "GS-310"

    def test_get_error_stats_multiple_error_codes(
        self, client: TestClient, mock_importer_service
    ):
        """複数のエラーコードの統計を返す.

        要件5.4: エラー統計
        """
        from services.importer.import_error_log_repository import ErrorStats

        mock_importer_service.get_error_stats.return_value = [
            ErrorStats(
                error_code="GS-304",
                count=25,
                last_occurred=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            ),
            ErrorStats(
                error_code="GS-303",
                count=10,
                last_occurred=datetime(2024, 1, 14, 10, 0, 0, tzinfo=timezone.utc),
            ),
            ErrorStats(
                error_code="GS-305",
                count=5,
                last_occurred=datetime(2024, 1, 13, 8, 0, 0, tzinfo=timezone.utc),
            ),
            ErrorStats(
                error_code="GS-306",
                count=2,
                last_occurred=datetime(2024, 1, 12, 6, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        # Act
        response = client.get("/api/importers/stats")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 4
        # 件数の降順になっていることを確認（サービス側でソートされている前提）
        assert data["data"][0]["count"] == 25
        assert data["data"][1]["count"] == 10
        assert data["data"][2]["count"] == 5
        assert data["data"][3]["count"] == 2


# =============================================================================
# レスポンススキーマのテスト
# =============================================================================


class TestErrorStatsResponseSchema:
    """エラー統計レスポンススキーマのテスト."""

    def test_response_contains_required_fields(
        self, client: TestClient, mock_importer_service
    ):
        """レスポンスに必須フィールドが含まれる."""
        from services.importer.import_error_log_repository import ErrorStats

        mock_importer_service.get_error_stats.return_value = [
            ErrorStats(
                error_code="GS-304",
                count=1,
                last_occurred=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        # Act
        response = client.get("/api/importers/stats")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # トップレベル
        assert "data" in data
        assert "timestamp" in data
        # 各エラー統計アイテム
        assert "error_code" in data["data"][0]
        assert "count" in data["data"][0]
        assert "last_occurred" in data["data"][0]

    def test_timestamp_is_iso8601_format(
        self, client: TestClient, mock_importer_service
    ):
        """タイムスタンプがISO 8601形式である."""
        from services.importer.import_error_log_repository import ErrorStats

        mock_importer_service.get_error_stats.return_value = [
            ErrorStats(
                error_code="GS-304",
                count=1,
                last_occurred=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            ),
        ]

        # Act
        response = client.get("/api/importers/stats")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # ISO 8601形式でパース可能であることを確認
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["data"][0]["last_occurred"].replace("Z", "+00:00"))

    def test_error_response_format(self, client: TestClient, mock_importer_service):
        """エラーレスポンスが統一フォーマットに従う."""
        mock_importer_service.get_error_stats.side_effect = Exception("テストエラー")

        # Act
        response = client.get("/api/importers/stats")

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data
        assert "errors" in data["detail"]
        assert "timestamp" in data["detail"]
        error = data["detail"]["errors"][0]
        assert "code" in error
        assert "message" in error

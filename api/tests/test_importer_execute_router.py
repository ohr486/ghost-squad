"""インポート実行API - Integration Tests.

タスク 10.3: インポート実行APIの実装
- POST /api/importers/execute - インポート実行
- POST /api/importers/retry - リトライ実行

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5, 5.2
"""

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
# POST /api/importers/execute エンドポイントのテスト
# =============================================================================


class TestExecuteImportEndpoint:
    """POST /api/importers/execute エンドポイントのテスト."""

    def test_execute_import_success(self, client: TestClient, mock_importer_service):
        """インポート実行が成功する.

        要件2.1-2.6, 4.1-4.5
        """
        from services.importer.importer_service import ImportResult
        from services.importer.result import Result

        mock_importer_service.execute_import.return_value = Result.ok(
            ImportResult(
                total_fetched=5,
                total_imported=4,
                total_skipped=1,
                total_failed=0,
                imported_inquiry_ids=[101, 102, 103, 104],
                errors=[],
            )
        )

        # Act
        response = client.post(
            "/api/importers/execute",
            json={
                "plugin_type": "email",
                "ai_provider_type": "openai",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_fetched"] == 5
        assert data["total_imported"] == 4
        assert data["total_skipped"] == 1
        assert data["total_failed"] == 0
        assert data["imported_inquiry_ids"] == [101, 102, 103, 104]
        assert data["errors"] == []
        assert "timestamp" in data

    def test_execute_import_without_ai_provider(
        self, client: TestClient, mock_importer_service
    ):
        """AIプロバイダー未指定時はデフォルトを使用.

        要件3.1: カテゴリ判定
        """
        from services.importer.importer_service import ImportResult
        from services.importer.result import Result

        mock_importer_service.execute_import.return_value = Result.ok(
            ImportResult(
                total_fetched=3,
                total_imported=3,
                total_skipped=0,
                total_failed=0,
                imported_inquiry_ids=[201, 202, 203],
                errors=[],
            )
        )

        # Act
        response = client.post(
            "/api/importers/execute",
            json={
                "plugin_type": "email",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_imported"] == 3
        # ai_provider_type=None で呼び出されたことを確認
        mock_importer_service.execute_import.assert_called_once_with(
            plugin_type="email",
            ai_provider_type=None,
        )

    def test_execute_import_with_partial_failures(
        self, client: TestClient, mock_importer_service
    ):
        """一部のインポートが失敗しても結果を返す.

        要件4.4: 生成失敗処理
        """
        from services.importer.importer_service import (ImportError,
                                                        ImportResult)
        from services.importer.result import Result

        mock_importer_service.execute_import.return_value = Result.ok(
            ImportResult(
                total_fetched=5,
                total_imported=3,
                total_skipped=0,
                total_failed=2,
                imported_inquiry_ids=[301, 302, 303],
                errors=[
                    ImportError(
                        source_id="<error1@example.com>",
                        error_code="GS-304",
                        error_message="AI解析に失敗しました",
                    ),
                    ImportError(
                        source_id="<error2@example.com>",
                        error_code="GS-305",
                        error_message="問い合わせ作成に失敗しました",
                    ),
                ],
            )
        )

        # Act
        response = client.post(
            "/api/importers/execute",
            json={
                "plugin_type": "email",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_fetched"] == 5
        assert data["total_imported"] == 3
        assert data["total_failed"] == 2
        assert len(data["errors"]) == 2
        assert data["errors"][0]["error_code"] == "GS-304"
        assert data["errors"][1]["error_code"] == "GS-305"

    def test_execute_import_plugin_not_found(
        self, client: TestClient, mock_importer_service
    ):
        """存在しないプラグインの場合は404エラー.

        要件1.1: プラグイン登録
        """
        from services.importer.importer_service import ImporterServiceError
        from services.importer.result import Result

        mock_importer_service.execute_import.return_value = Result.err(
            ImporterServiceError(
                code="GS-301",
                message="プラグイン 'unknown' が見つかりません",
            )
        )

        # Act
        response = client.post(
            "/api/importers/execute",
            json={
                "plugin_type": "unknown",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "errors" in data["detail"]
        assert data["detail"]["errors"][0]["code"] == "GS-301"

    def test_execute_import_connection_error(
        self, client: TestClient, mock_importer_service
    ):
        """データソース接続失敗時は500エラー.

        要件2.5: リトライ処理
        """
        from services.importer.importer_service import ImporterServiceError
        from services.importer.result import Result

        mock_importer_service.execute_import.return_value = Result.err(
            ImporterServiceError(
                code="GS-303",
                message="データソース接続に失敗しました: Connection refused",
            )
        )

        # Act
        response = client.post(
            "/api/importers/execute",
            json={
                "plugin_type": "email",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "errors" in data["detail"]
        assert data["detail"]["errors"][0]["code"] == "GS-303"

    def test_execute_import_invalid_request_missing_plugin_type(
        self, client: TestClient
    ):
        """plugin_type未指定は422エラー.

        バリデーションエラー
        """
        # Act
        response = client.post(
            "/api/importers/execute",
            json={},
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_execute_import_invalid_request_empty_plugin_type(self, client: TestClient):
        """plugin_typeが空文字は422エラー.

        バリデーションエラー
        """
        # Act
        response = client.post(
            "/api/importers/execute",
            json={"plugin_type": ""},
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_execute_import_invalid_ai_provider(self, client: TestClient):
        """無効なAIプロバイダー種別は404エラー.

        要件3.1: カテゴリ判定
        """
        # Act
        response = client.post(
            "/api/importers/execute",
            json={
                "plugin_type": "email",
                "ai_provider_type": "invalid",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "errors" in data["detail"]
        assert data["detail"]["errors"][0]["code"] == "GS-308"


# =============================================================================
# POST /api/importers/retry エンドポイントのテスト
# =============================================================================


class TestRetryImportEndpoint:
    """POST /api/importers/retry エンドポイントのテスト."""

    def test_retry_import_success(self, client: TestClient, mock_importer_service):
        """リトライ実行が成功する.

        要件5.2: 手動リトライ
        """
        from services.importer.importer_service import ImportResult
        from services.importer.result import Result

        mock_importer_service.retry_failed.return_value = Result.ok(
            ImportResult(
                total_fetched=2,
                total_imported=2,
                total_skipped=0,
                total_failed=0,
                imported_inquiry_ids=[401, 402],
                errors=[],
            )
        )

        # Act
        response = client.post(
            "/api/importers/retry",
            json={
                "plugin_type": "email",
                "source_ids": ["<msg1@example.com>", "<msg2@example.com>"],
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_fetched"] == 2
        assert data["total_imported"] == 2
        assert data["imported_inquiry_ids"] == [401, 402]
        assert "timestamp" in data

    def test_retry_import_with_ai_provider(
        self, client: TestClient, mock_importer_service
    ):
        """リトライ時にAIプロバイダーを指定できる.

        要件5.2: 手動リトライ
        """
        from services.importer.ai_provider_base import AIProviderType
        from services.importer.importer_service import ImportResult
        from services.importer.result import Result

        mock_importer_service.retry_failed.return_value = Result.ok(
            ImportResult(
                total_fetched=1,
                total_imported=1,
                total_skipped=0,
                total_failed=0,
                imported_inquiry_ids=[501],
                errors=[],
            )
        )

        # Act
        response = client.post(
            "/api/importers/retry",
            json={
                "plugin_type": "email",
                "source_ids": ["<msg@example.com>"],
                "ai_provider_type": "anthropic",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        # anthropic プロバイダーで呼び出されたことを確認
        call_args = mock_importer_service.retry_failed.call_args
        assert call_args.kwargs.get("ai_provider_type") == AIProviderType.ANTHROPIC

    def test_retry_import_partial_success(
        self, client: TestClient, mock_importer_service
    ):
        """リトライで一部が成功する場合.

        要件5.2: 手動リトライ
        """
        from services.importer.importer_service import (ImportError,
                                                        ImportResult)
        from services.importer.result import Result

        mock_importer_service.retry_failed.return_value = Result.ok(
            ImportResult(
                total_fetched=3,
                total_imported=1,
                total_skipped=1,
                total_failed=1,
                imported_inquiry_ids=[601],
                errors=[
                    ImportError(
                        source_id="<failed@example.com>",
                        error_code="GS-304",
                        error_message="AI解析に失敗しました",
                    )
                ],
            )
        )

        # Act
        response = client.post(
            "/api/importers/retry",
            json={
                "plugin_type": "email",
                "source_ids": [
                    "<ok@example.com>",
                    "<skip@example.com>",
                    "<failed@example.com>",
                ],
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_imported"] == 1
        assert data["total_skipped"] == 1
        assert data["total_failed"] == 1
        assert len(data["errors"]) == 1

    def test_retry_import_plugin_not_found(
        self, client: TestClient, mock_importer_service
    ):
        """存在しないプラグインのリトライは404エラー.

        要件1.1: プラグイン登録
        """
        from services.importer.importer_service import ImporterServiceError
        from services.importer.result import Result

        mock_importer_service.retry_failed.return_value = Result.err(
            ImporterServiceError(
                code="GS-301",
                message="プラグイン 'unknown' が見つかりません",
            )
        )

        # Act
        response = client.post(
            "/api/importers/retry",
            json={
                "plugin_type": "unknown",
                "source_ids": ["<msg@example.com>"],
            },
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "errors" in data["detail"]
        assert data["detail"]["errors"][0]["code"] == "GS-301"

    def test_retry_import_connection_error(
        self, client: TestClient, mock_importer_service
    ):
        """データソース接続失敗時は500エラー.

        要件2.5: リトライ処理
        """
        from services.importer.importer_service import ImporterServiceError
        from services.importer.result import Result

        mock_importer_service.retry_failed.return_value = Result.err(
            ImporterServiceError(
                code="GS-303",
                message="データソース接続に失敗しました",
            )
        )

        # Act
        response = client.post(
            "/api/importers/retry",
            json={
                "plugin_type": "email",
                "source_ids": ["<msg@example.com>"],
            },
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "errors" in data["detail"]
        assert data["detail"]["errors"][0]["code"] == "GS-303"

    def test_retry_import_invalid_request_missing_source_ids(self, client: TestClient):
        """source_ids未指定は422エラー.

        バリデーションエラー
        """
        # Act
        response = client.post(
            "/api/importers/retry",
            json={
                "plugin_type": "email",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_retry_import_invalid_request_empty_source_ids(self, client: TestClient):
        """source_idsが空リストは422エラー.

        バリデーションエラー
        """
        # Act
        response = client.post(
            "/api/importers/retry",
            json={
                "plugin_type": "email",
                "source_ids": [],
            },
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# レスポンススキーマのテスト
# =============================================================================


class TestImportResponseSchema:
    """インポートレスポンススキーマのテスト."""

    def test_response_contains_required_fields(
        self, client: TestClient, mock_importer_service
    ):
        """レスポンスに必須フィールドが含まれる."""
        from services.importer.importer_service import ImportResult
        from services.importer.result import Result

        mock_importer_service.execute_import.return_value = Result.ok(
            ImportResult(
                total_fetched=0,
                total_imported=0,
                total_skipped=0,
                total_failed=0,
                imported_inquiry_ids=[],
                errors=[],
            )
        )

        # Act
        response = client.post(
            "/api/importers/execute",
            json={"plugin_type": "email"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_fetched" in data
        assert "total_imported" in data
        assert "total_skipped" in data
        assert "total_failed" in data
        assert "imported_inquiry_ids" in data
        assert "errors" in data
        assert "timestamp" in data

    def test_error_response_format(self, client: TestClient, mock_importer_service):
        """エラーレスポンスが統一フォーマットに従う."""
        from services.importer.importer_service import ImporterServiceError
        from services.importer.result import Result

        mock_importer_service.execute_import.return_value = Result.err(
            ImporterServiceError(
                code="GS-301",
                message="プラグイン 'unknown' が見つかりません",
            )
        )

        # Act
        response = client.post(
            "/api/importers/execute",
            json={"plugin_type": "unknown"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "errors" in data["detail"]
        assert "timestamp" in data["detail"]
        error = data["detail"]["errors"][0]
        assert "code" in error
        assert "message" in error

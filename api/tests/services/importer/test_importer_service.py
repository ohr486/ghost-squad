"""ImporterServiceのユニットテスト.

Task 9.1, 9.2, 9.3, 9.4のテスト
- ImporterMetadata, ImportResult, ImportErrorのデータクラス
- ImporterServiceのインポート実行機能
- ImporterServiceのエラーハンドリング機能
- ImporterServiceのリトライ機能
"""
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, List
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from models.enums.priority import Priority
from services.importer.ai_provider_base import AIProviderType
from services.importer.ai_provider_registry import AIProviderRegistryService
from services.importer.analysis_service import (AnalysisResult,
                                                ImporterAnalysisService)
from services.importer.importer_service import (CONSECUTIVE_ERROR_THRESHOLD,
                                                ImporterMetadata, ImportError,
                                                ImporterService,
                                                ImporterServiceError,
                                                ImportResult)
from services.importer.plugin_base import DataSourcePlugin, RawImportData
from services.importer.plugin_registry import PluginRegistryService
from tests.conftest import MockDataSourcePlugin


class TestImporterMetadata:
    """ImporterMetadataのテスト (Task 9.1)."""

    def test_create_importer_metadata(self) -> None:
        """ImporterMetadataの作成をテスト."""
        now = datetime.now(UTC)
        metadata = ImporterMetadata(
            source_type="email",
            source_id="<message-id-123>",
            imported_at=now,
            confidence_score=0.85,
            needs_review=False,
            original_subject="Test Subject",
            original_sender="test@example.com",
            ai_provider="openai",
            ai_model="gpt-4",
        )

        assert metadata.source_type == "email"
        assert metadata.source_id == "<message-id-123>"
        assert metadata.imported_at == now
        assert metadata.confidence_score == 0.85
        assert metadata.needs_review is False
        assert metadata.original_subject == "Test Subject"
        assert metadata.original_sender == "test@example.com"
        assert metadata.ai_provider == "openai"
        assert metadata.ai_model == "gpt-4"

    def test_importer_metadata_to_dict(self) -> None:
        """ImporterMetadataをdictに変換できることをテスト."""
        now = datetime.now(UTC)
        metadata = ImporterMetadata(
            source_type="email",
            source_id="<message-id-456>",
            imported_at=now,
            confidence_score=0.7,
            needs_review=True,
            original_subject="件名",
            original_sender="sender@example.com",
            ai_provider="anthropic",
            ai_model="claude-3-sonnet-20240229",
        )

        data = asdict(metadata)
        assert data["source_type"] == "email"
        assert data["source_id"] == "<message-id-456>"
        assert data["confidence_score"] == 0.7
        assert data["needs_review"] is True
        assert data["ai_provider"] == "anthropic"


class TestImportError:
    """ImportErrorのテスト (Task 9.1)."""

    def test_create_import_error(self) -> None:
        """ImportErrorの作成をテスト."""
        error = ImportError(
            source_id="<message-id-789>",
            error_code="GS-304",
            error_message="AI解析に失敗しました",
        )

        assert error.source_id == "<message-id-789>"
        assert error.error_code == "GS-304"
        assert error.error_message == "AI解析に失敗しました"

    def test_import_error_to_dict(self) -> None:
        """ImportErrorをdictに変換できることをテスト."""
        error = ImportError(
            source_id="<msg-1>",
            error_code="GS-305",
            error_message="重複検出",
        )

        data = asdict(error)
        assert data["source_id"] == "<msg-1>"
        assert data["error_code"] == "GS-305"


class TestImportResult:
    """ImportResultのテスト (Task 9.1)."""

    def test_create_import_result_success(self) -> None:
        """成功ケースのImportResultの作成をテスト."""
        result = ImportResult(
            total_fetched=10,
            total_imported=8,
            total_skipped=1,
            total_failed=1,
            imported_inquiry_ids=[1, 2, 3, 4, 5, 6, 7, 8],
            errors=[
                ImportError(
                    source_id="<msg-fail>",
                    error_code="GS-304",
                    error_message="AI解析失敗",
                )
            ],
        )

        assert result.total_fetched == 10
        assert result.total_imported == 8
        assert result.total_skipped == 1
        assert result.total_failed == 1
        assert len(result.imported_inquiry_ids) == 8
        assert len(result.errors) == 1

    def test_create_import_result_empty(self) -> None:
        """空のImportResultの作成をテスト."""
        result = ImportResult(
            total_fetched=0,
            total_imported=0,
            total_skipped=0,
            total_failed=0,
            imported_inquiry_ids=[],
            errors=[],
        )

        assert result.total_fetched == 0
        assert result.imported_inquiry_ids == []
        assert result.errors == []

    def test_import_result_to_dict(self) -> None:
        """ImportResultをdictに変換できることをテスト."""
        result = ImportResult(
            total_fetched=5,
            total_imported=3,
            total_skipped=2,
            total_failed=0,
            imported_inquiry_ids=[10, 20, 30],
            errors=[],
        )

        data = asdict(result)
        assert data["total_fetched"] == 5
        assert data["total_imported"] == 3
        assert data["imported_inquiry_ids"] == [10, 20, 30]


class TestImporterServiceError:
    """ImporterServiceErrorのテスト (Task 9.1)."""

    def test_create_importer_service_error(self) -> None:
        """ImporterServiceErrorの作成をテスト."""
        error = ImporterServiceError(
            code="GS-301",
            message="プラグインが見つかりません",
        )

        assert error.code == "GS-301"
        assert error.message == "プラグインが見つかりません"
        assert str(error) == "[GS-301] プラグインが見つかりません"


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_session() -> MagicMock:
    """モックセッションを作成."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_plugin_registry() -> PluginRegistryService:
    """モックプラグインレジストリを作成."""
    return PluginRegistryService()


@pytest.fixture
def mock_ai_provider_registry() -> AIProviderRegistryService:
    """モックAIプロバイダーレジストリを作成."""
    return AIProviderRegistryService()


@pytest.fixture
def mock_analysis_service(
    mock_ai_provider_registry: AIProviderRegistryService,
) -> ImporterAnalysisService:
    """モック解析サービスを作成."""
    return ImporterAnalysisService(mock_ai_provider_registry)


@pytest.fixture
def sample_raw_data() -> RawImportData:
    """サンプルの生データを作成."""
    return RawImportData(
        source_id="<message-id-test-123>",
        source_type="email",
        content="これはテスト問い合わせの本文です。",
        subject="テスト件名",
        sender="test@example.com",
        received_at=datetime.now(UTC),
        raw_metadata={"header": "value"},
    )


@pytest.fixture
def sample_analysis_result() -> AnalysisResult:
    """サンプルの解析結果を作成."""
    return AnalysisResult(
        title="テスト問い合わせ",
        content="構造化されたテスト問い合わせの本文です。",
        priority=Priority.MEDIUM,
        confidence_score=0.85,
        needs_review=False,
        provider_type="openai",
        model="gpt-4",
        analysis_metadata={"key": "value"},
        category=None,
    )


# ==============================================================================
# Task 9.2: ImporterService インポート実行機能のテスト
# ==============================================================================


class TestImporterServiceExecuteImport:
    """ImporterServiceのインポート実行機能のテスト (Task 9.2)."""

    def test_execute_import_plugin_not_found(
        self,
        mock_session: MagicMock,
        mock_plugin_registry: PluginRegistryService,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """存在しないプラグインでインポートを実行するとエラーを返す."""
        service = ImporterService(
            session=mock_session,
            plugin_registry=mock_plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = service.execute_import("nonexistent_plugin")

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-301"
        assert "nonexistent_plugin" in error.message

    def test_execute_import_connection_failure(
        self,
        mock_session: MagicMock,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """接続失敗時にエラーを返す."""
        # 接続失敗するプラグインを登録
        plugin_registry = PluginRegistryService()
        plugin_registry.register(
            MockDataSourcePlugin,
            {"fail_connect": True},
        )

        service = ImporterService(
            session=mock_session,
            plugin_registry=plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = service.execute_import("mock_plugin")

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-303"

    def test_execute_import_fetch_failure(
        self,
        mock_session: MagicMock,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """データ取得失敗時にエラーを返す."""
        # データ取得失敗するプラグインを登録
        plugin_registry = PluginRegistryService()
        plugin_registry.register(
            MockDataSourcePlugin,
            {"fail_fetch": True},
        )

        service = ImporterService(
            session=mock_session,
            plugin_registry=plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = service.execute_import("mock_plugin")

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-306"

    def test_execute_import_empty_data(
        self,
        mock_session: MagicMock,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """空のデータでインポートを実行すると空の結果を返す."""
        plugin_registry = PluginRegistryService()
        plugin_registry.register(MockDataSourcePlugin, {})

        service = ImporterService(
            session=mock_session,
            plugin_registry=plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = service.execute_import("mock_plugin")

        assert result.is_ok
        import_result = result.unwrap()
        assert import_result.total_fetched == 0
        assert import_result.total_imported == 0
        assert import_result.total_skipped == 0
        assert import_result.total_failed == 0

    def test_execute_import_with_ai_provider_type(
        self,
        mock_session: MagicMock,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """AIプロバイダー指定でインポートを実行できる."""
        plugin_registry = PluginRegistryService()
        plugin_registry.register(MockDataSourcePlugin, {})

        service = ImporterService(
            session=mock_session,
            plugin_registry=plugin_registry,
            analysis_service=mock_analysis_service,
        )

        # AIプロバイダーを指定してインポート実行（空データなので結果は0件）
        result = service.execute_import(
            "mock_plugin",
            ai_provider_type=AIProviderType.OPENAI,
        )

        assert result.is_ok

    def test_execute_import_success(
        self,
        mock_session: MagicMock,
        sample_raw_data: RawImportData,
        sample_analysis_result: AnalysisResult,
    ) -> None:
        """成功時のインポート実行の完全なハッピーパステスト."""
        # モックプラグインを登録してデータを設定
        plugin_registry = PluginRegistryService()
        plugin_registry.register(MockDataSourcePlugin, {})
        # 登録後にプラグインインスタンスを取得してデータを設定
        plugin = plugin_registry.get_plugin("mock_plugin")
        assert plugin is not None
        plugin.set_data([sample_raw_data])

        # 重複チェックでNone（重複なし）を返すようにモック
        mock_session.query.return_value.filter.return_value.first.return_value = None

        # モックAnalysisServiceを作成
        mock_analysis_service = MagicMock(spec=ImporterAnalysisService)
        mock_analyze_result = MagicMock()
        mock_analyze_result.is_ok = True
        mock_analyze_result.is_err = False
        mock_analyze_result.unwrap.return_value = sample_analysis_result
        mock_analysis_service.analyze.return_value = mock_analyze_result

        # モックInquiryRepositoryを作成
        mock_inquiry_repository = MagicMock()
        mock_inquiry = MagicMock()
        mock_inquiry.id = 123
        mock_inquiry.inquiry_metadata = {}
        mock_inquiry_repository.create.return_value = mock_inquiry
        mock_inquiry_repository.find_by_metadata.return_value = None

        # ImporterServiceを作成
        service = ImporterService(
            session=mock_session,
            plugin_registry=plugin_registry,
            analysis_service=mock_analysis_service,
        )
        service._inquiry_repository = mock_inquiry_repository

        # インポートを実行
        result = service.execute_import("mock_plugin")

        # 結果の検証
        assert result.is_ok
        import_result = result.unwrap()
        assert import_result.total_fetched == 1
        assert import_result.total_imported == 1
        assert import_result.total_skipped == 0
        assert import_result.total_failed == 0
        assert len(import_result.imported_inquiry_ids) == 1
        assert import_result.imported_inquiry_ids[0] == 123
        assert len(import_result.errors) == 0

        # AI解析が呼ばれたことを確認
        mock_analysis_service.analyze.assert_called_once()

        # Inquiryが作成されたことを確認
        mock_inquiry_repository.create.assert_called_once()
        create_call_args = mock_inquiry_repository.create.call_args
        create_data = create_call_args[0][0]
        assert create_data.content == sample_analysis_result.content
        assert create_data.user_id == "importer:mock_plugin"
        assert create_data.source_system == "importer:mock_plugin"

        # メタデータが正しく設定されたことを確認
        assert mock_inquiry.inquiry_metadata["importer"]["source_type"] == "mock_plugin"
        assert (
            mock_inquiry.inquiry_metadata["importer"]["source_id"]
            == sample_raw_data.source_id
        )
        assert (
            mock_inquiry.inquiry_metadata["importer"]["confidence_score"]
            == sample_analysis_result.confidence_score
        )
        assert (
            mock_inquiry.inquiry_metadata["importer"]["needs_review"]
            == sample_analysis_result.needs_review
        )
        assert (
            mock_inquiry.inquiry_metadata["importer"]["original_subject"]
            == sample_raw_data.subject
        )
        assert (
            mock_inquiry.inquiry_metadata["importer"]["original_sender"]
            == sample_raw_data.sender
        )
        assert (
            mock_inquiry.inquiry_metadata["importer"]["ai_provider"]
            == sample_analysis_result.provider_type
        )
        assert (
            mock_inquiry.inquiry_metadata["importer"]["ai_model"]
            == sample_analysis_result.model
        )
        # AI生成のタイトルと優先度が保存されていることを確認
        assert (
            mock_inquiry.inquiry_metadata["importer"]["ai_generated_title"]
            == sample_analysis_result.title
        )
        assert (
            mock_inquiry.inquiry_metadata["importer"]["ai_generated_priority"]
            == sample_analysis_result.priority.value
        )

        # セッションのコミットが呼ばれたことを確認
        assert mock_session.commit.called
        assert mock_session.refresh.called


class TestImporterServiceCheckDuplicate:
    """ImporterServiceの重複チェック機能のテスト (Task 9.2)."""

    def test_check_duplicate_not_found(
        self,
        mock_session: MagicMock,
        mock_plugin_registry: PluginRegistryService,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """重複がない場合Falseを返す."""
        # クエリ結果がNoneを返すようにモック
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = ImporterService(
            session=mock_session,
            plugin_registry=mock_plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = service.check_duplicate("email", "<new-message-id>")
        assert result is False

    def test_check_duplicate_found(
        self,
        mock_session: MagicMock,
        mock_plugin_registry: PluginRegistryService,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """重複がある場合Trueを返す."""
        # クエリ結果が何かを返すようにモック
        mock_session.query.return_value.filter.return_value.first.return_value = (
            MagicMock()
        )

        service = ImporterService(
            session=mock_session,
            plugin_registry=mock_plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = service.check_duplicate("email", "<existing-message-id>")
        assert result is True


# ==============================================================================
# Task 9.3: ImporterService エラーハンドリング機能のテスト
# ==============================================================================


class TestImporterServiceErrorHandling:
    """ImporterServiceのエラーハンドリング機能のテスト (Task 9.3)."""

    def test_log_error(
        self,
        mock_session: MagicMock,
        mock_plugin_registry: PluginRegistryService,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """エラーログが記録される."""
        service = ImporterService(
            session=mock_session,
            plugin_registry=mock_plugin_registry,
            analysis_service=mock_analysis_service,
        )

        # モックのcreateメソッドをセットアップ
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        service._log_error(
            plugin_type="email",
            error_code="GS-304",
            error_message="テストエラー",
            source_id="<test-source-id>",
        )

        # addが呼ばれたことを確認
        assert mock_session.add.called

    def test_consecutive_error_detection(
        self,
        mock_session: MagicMock,
        mock_plugin_registry: PluginRegistryService,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """連続エラーが検出されてアラートが発生する."""
        service = ImporterService(
            session=mock_session,
            plugin_registry=mock_plugin_registry,
            analysis_service=mock_analysis_service,
        )

        # 連続エラー閾値未満
        for _ in range(CONSECUTIVE_ERROR_THRESHOLD - 1):
            service._check_consecutive_errors("test_plugin")

        assert service._consecutive_errors == CONSECUTIVE_ERROR_THRESHOLD - 1

        # 閾値に達する
        with patch("services.importer.importer_service.logger") as mock_logger:
            service._check_consecutive_errors("test_plugin")
            # warning ログが呼ばれたことを確認
            mock_logger.warning.assert_called_once()

        assert service._consecutive_errors == CONSECUTIVE_ERROR_THRESHOLD

    def test_get_error_stats(
        self,
        mock_session: MagicMock,
        mock_plugin_registry: PluginRegistryService,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """エラー統計を取得できる."""
        service = ImporterService(
            session=mock_session,
            plugin_registry=mock_plugin_registry,
            analysis_service=mock_analysis_service,
        )

        # モックの戻り値を設定
        mock_query = mock_session.query.return_value
        mock_filtered = mock_query.filter.return_value.group_by.return_value
        mock_filtered.order_by.return_value.all.return_value = []

        stats = service.get_error_stats()
        assert isinstance(stats, list)


# ==============================================================================
# Task 9.4: ImporterService リトライ機能のテスト
# ==============================================================================


class TestImporterServiceRetry:
    """ImporterServiceのリトライ機能のテスト (Task 9.4)."""

    def test_retry_failed_plugin_not_found(
        self,
        mock_session: MagicMock,
        mock_plugin_registry: PluginRegistryService,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """存在しないプラグインでリトライするとエラーを返す."""
        service = ImporterService(
            session=mock_session,
            plugin_registry=mock_plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = service.retry_failed(
            plugin_type="nonexistent_plugin",
            source_ids=["<msg-1>", "<msg-2>"],
        )

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-301"

    def test_retry_failed_empty_source_ids(
        self,
        mock_session: MagicMock,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """空のソースIDリストでリトライすると空の結果を返す."""
        plugin_registry = PluginRegistryService()
        plugin_registry.register(MockDataSourcePlugin, {})

        service = ImporterService(
            session=mock_session,
            plugin_registry=plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = service.retry_failed(
            plugin_type="mock_plugin",
            source_ids=[],
        )

        assert result.is_ok
        import_result = result.unwrap()
        assert import_result.total_fetched == 0

    def test_retry_failed_source_not_in_data(
        self,
        mock_session: MagicMock,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """リトライ対象データが見つからない場合はスキップされる."""
        plugin_registry = PluginRegistryService()
        plugin_registry.register(MockDataSourcePlugin, {})

        service = ImporterService(
            session=mock_session,
            plugin_registry=plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = service.retry_failed(
            plugin_type="mock_plugin",
            source_ids=["<not-exist-id>"],
        )

        assert result.is_ok
        import_result = result.unwrap()
        assert import_result.total_fetched == 1
        assert import_result.total_skipped == 1

    def test_retry_failed_with_ai_provider(
        self,
        mock_session: MagicMock,
        mock_analysis_service: ImporterAnalysisService,
    ) -> None:
        """AIプロバイダーを指定してリトライできる."""
        plugin_registry = PluginRegistryService()
        plugin_registry.register(MockDataSourcePlugin, {})

        service = ImporterService(
            session=mock_session,
            plugin_registry=plugin_registry,
            analysis_service=mock_analysis_service,
        )

        result = service.retry_failed(
            plugin_type="mock_plugin",
            source_ids=[],
            ai_provider_type=AIProviderType.ANTHROPIC,
        )

        assert result.is_ok

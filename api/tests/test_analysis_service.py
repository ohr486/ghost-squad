"""ImporterAnalysisServiceのテスト.

Task 6.1: ImporterAnalysisServiceの実装
- AIProviderRegistryとの統合
- 解析用プロンプトの構築（全プロバイダー共通、日本語対応）
- プロバイダー選択機能（引数指定またはデフォルト使用）
- AIレスポンスからAnalysisResultへの変換
- 信頼度に基づくneeds_reviewフラグ判定（閾値0.8）
- AnalysisResultデータクラスの定義

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
from datetime import datetime
from unittest.mock import MagicMock

from models.enums.priority import Priority
from services.importer.ai_provider_base import (AIAnalysisRequest,
                                                AIAnalysisResponse,
                                                AIProviderType)
from services.importer.ai_provider_registry import AIProviderRegistryService
from services.importer.analysis_service import (AnalysisError, AnalysisResult,
                                                ImporterAnalysisService)
from services.importer.plugin_base import RawImportData


class TestAnalysisResultDataclass:
    """AnalysisResultデータクラスのテスト."""

    def test_create_with_required_fields(self):
        """必須フィールドで作成できることを確認."""
        result = AnalysisResult(
            title="テストタイトル",
            content="テスト内容",
            priority=Priority.MEDIUM,
            confidence_score=0.85,
            needs_review=False,
            provider_type="openai",
            model="gpt-4",
            analysis_metadata={},
        )
        assert result.title == "テストタイトル"
        assert result.content == "テスト内容"
        assert result.priority == Priority.MEDIUM
        assert result.confidence_score == 0.85
        assert result.needs_review is False
        assert result.provider_type == "openai"
        assert result.model == "gpt-4"

    def test_category_is_optional(self):
        """categoryがオプショナルであることを確認."""
        result = AnalysisResult(
            title="テストタイトル",
            content="テスト内容",
            priority=Priority.HIGH,
            confidence_score=0.9,
            needs_review=False,
            provider_type="anthropic",
            model="claude-3-sonnet",
            analysis_metadata={},
        )
        assert result.category is None

    def test_category_can_be_set(self):
        """categoryを設定できることを確認."""
        result = AnalysisResult(
            title="テストタイトル",
            content="テスト内容",
            priority=Priority.LOW,
            confidence_score=0.7,
            needs_review=True,
            provider_type="openai",
            model="gpt-4",
            category="development",
            analysis_metadata={},
        )
        assert result.category == "development"

    def test_analysis_metadata_stores_additional_info(self):
        """analysis_metadataに追加情報を格納できることを確認."""
        metadata = {
            "raw_response": {"content": "test"},
            "processing_time_ms": 150,
        }
        result = AnalysisResult(
            title="テストタイトル",
            content="テスト内容",
            priority=Priority.MEDIUM,
            confidence_score=0.85,
            needs_review=False,
            provider_type="openai",
            model="gpt-4",
            analysis_metadata=metadata,
        )
        assert result.analysis_metadata["processing_time_ms"] == 150

    def test_all_priority_values(self):
        """すべての優先度値を使用できることを確認."""
        for priority in [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.URGENT]:
            result = AnalysisResult(
                title="タイトル",
                content="内容",
                priority=priority,
                confidence_score=0.8,
                needs_review=False,
                provider_type="openai",
                model="gpt-4",
                analysis_metadata={},
            )
            assert result.priority == priority


class TestAnalysisError:
    """AnalysisErrorデータクラスのテスト."""

    def test_create_analysis_error(self):
        """AnalysisErrorを作成できることを確認."""
        error = AnalysisError(
            code="GS-304",
            message="AI解析に失敗しました",
        )
        assert error.code == "GS-304"
        assert error.message == "AI解析に失敗しました"

    def test_str_representation(self):
        """文字列表現が正しいことを確認."""
        error = AnalysisError(
            code="GS-304",
            message="AI解析に失敗しました",
        )
        assert "[GS-304]" in str(error)
        assert "AI解析に失敗しました" in str(error)


class TestImporterAnalysisServiceInit:
    """ImporterAnalysisServiceの初期化テスト."""

    def test_init_with_registry(self):
        """AIProviderRegistryで初期化できることを確認."""
        registry = AIProviderRegistryService()
        service = ImporterAnalysisService(registry)
        assert service._provider_registry is registry

    def test_init_stores_registry_reference(self):
        """registryの参照が保持されることを確認."""
        registry = AIProviderRegistryService()
        service = ImporterAnalysisService(registry)
        # 同じインスタンスであることを確認
        assert service._provider_registry is registry


class TestImporterAnalysisServiceAnalyze:
    """ImporterAnalysisServiceのanalyzeメソッドテスト."""

    def test_analyze_with_default_provider(self):
        """デフォルトプロバイダーで解析できることを確認."""
        # モックプロバイダーを作成
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="解析タイトル",
            content="解析内容",
            priority="medium",
            category="development",
            confidence_score=0.85,
            raw_response={"test": "response"},
            provider_type="openai",
            model="gpt-4",
        )

        # モックレジストリを作成
        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test-123",
            source_type="email",
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        analysis_result = result.unwrap()
        assert isinstance(analysis_result, AnalysisResult)
        assert analysis_result.title == "解析タイトル"
        mock_registry.get_provider.assert_called_once_with(None)

    def test_analyze_with_specified_provider(self):
        """指定したプロバイダーで解析できることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="Anthropic解析タイトル",
            content="Anthropic解析内容",
            priority="high",
            category="maintenance",
            confidence_score=0.92,
            raw_response={"provider": "anthropic"},
            provider_type="anthropic",
            model="claude-3-sonnet",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test-456",
            source_type="email",
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data, provider_type=AIProviderType.ANTHROPIC)

        assert result.is_ok
        analysis_result = result.unwrap()
        assert analysis_result.provider_type == "anthropic"
        mock_registry.get_provider.assert_called_once_with(AIProviderType.ANTHROPIC)

    def test_analyze_returns_error_when_no_provider(self):
        """プロバイダーが未登録の場合にエラーを返すことを確認."""
        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = None

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test-789",
            source_type="email",
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-308"
        assert "プロバイダー" in error.message

    def test_analyze_returns_error_on_provider_exception(self):
        """プロバイダーが例外を発生させた場合にエラーを返すことを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.side_effect = Exception("API呼び出しエラー")

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test-error",
            source_type="email",
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-304"


class TestImporterAnalysisServiceConversion:
    """AIレスポンスからAnalysisResultへの変換テスト."""

    def test_convert_priority_low(self):
        """優先度lowが正しく変換されることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="low",
            category=None,
            confidence_score=0.8,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        assert result.unwrap().priority == Priority.LOW

    def test_convert_priority_medium(self):
        """優先度mediumが正しく変換されることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="medium",
            category=None,
            confidence_score=0.8,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        assert result.unwrap().priority == Priority.MEDIUM

    def test_convert_priority_high(self):
        """優先度highが正しく変換されることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="high",
            category=None,
            confidence_score=0.8,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        assert result.unwrap().priority == Priority.HIGH

    def test_convert_priority_urgent(self):
        """優先度urgentが正しく変換されることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="urgent",
            category=None,
            confidence_score=0.8,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        assert result.unwrap().priority == Priority.URGENT

    def test_convert_unknown_priority_defaults_to_medium(self):
        """不明な優先度がmediumにデフォルトされることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="unknown_priority",
            category=None,
            confidence_score=0.8,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        assert result.unwrap().priority == Priority.MEDIUM


class TestImporterAnalysisServiceNeedsReview:
    """needs_reviewフラグ判定テスト."""

    def test_needs_review_false_when_confidence_above_threshold(self):
        """信頼度が閾値（0.8）以上の場合needs_reviewがFalseになることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="medium",
            category=None,
            confidence_score=0.85,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        assert result.unwrap().needs_review is False

    def test_needs_review_false_when_confidence_exactly_at_threshold(self):
        """信頼度がちょうど閾値（0.8）の場合needs_reviewがFalseになることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="medium",
            category=None,
            confidence_score=0.8,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        assert result.unwrap().needs_review is False

    def test_needs_review_true_when_confidence_below_threshold(self):
        """信頼度が閾値（0.8）未満の場合needs_reviewがTrueになることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="medium",
            category=None,
            confidence_score=0.79,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        assert result.unwrap().needs_review is True

    def test_needs_review_true_when_confidence_is_very_low(self):
        """信頼度が非常に低い場合needs_reviewがTrueになることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="medium",
            category=None,
            confidence_score=0.3,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        assert result.unwrap().needs_review is True


class TestImporterAnalysisServiceMetadata:
    """analysis_metadataのテスト."""

    def test_analysis_metadata_contains_raw_response(self):
        """analysis_metadataにraw_responseが含まれることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="medium",
            category="development",
            confidence_score=0.85,
            raw_response={"original": "data", "tokens": 100},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        analysis_result = result.unwrap()
        assert "raw_response" in analysis_result.analysis_metadata
        assert analysis_result.analysis_metadata["raw_response"]["tokens"] == 100

    def test_analysis_metadata_contains_source_info(self):
        """analysis_metadataにソース情報が含まれることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="medium",
            category=None,
            confidence_score=0.85,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="msg-123",
            source_type="email",
            content="本文",
            subject="件名",
            sender="test@example.com",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        analysis_result = result.unwrap()
        assert "source_id" in analysis_result.analysis_metadata
        assert analysis_result.analysis_metadata["source_id"] == "msg-123"
        assert analysis_result.analysis_metadata["source_type"] == "email"


class TestImporterAnalysisServiceBuildRequest:
    """AIAnalysisRequestの構築テスト."""

    def test_build_request_includes_all_fields(self):
        """リクエストにすべてのフィールドが含まれることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="タイトル",
            content="内容",
            priority="medium",
            category=None,
            confidence_score=0.8,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="test-id",
            source_type="email",
            content="テスト本文内容",
            subject="テスト件名",
            sender="sender@example.com",
            received_at=datetime.now(),
            raw_metadata={"header": "value"},
        )

        service.analyze(raw_data)

        # analyzeメソッドに渡されたリクエストを確認
        call_args = mock_provider.analyze.call_args
        request = call_args[0][0]

        assert isinstance(request, AIAnalysisRequest)
        assert request.content == "テスト本文内容"
        assert request.subject == "テスト件名"
        assert request.sender == "sender@example.com"
        assert request.source_type == "email"


class TestImporterAnalysisServiceJapaneseContent:
    """日本語コンテンツの解析テスト."""

    def test_analyze_japanese_email(self):
        """日本語メールを正しく解析できることを確認."""
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = AIAnalysisResponse(
            title="【緊急】システム障害報告",
            content="・本番環境でエラー発生\n・データベース接続不可\n・至急対応が必要",
            priority="urgent",
            category="maintenance",
            confidence_score=0.95,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )

        mock_registry = MagicMock(spec=AIProviderRegistryService)
        mock_registry.get_provider.return_value = mock_provider

        service = ImporterAnalysisService(mock_registry)

        raw_data = RawImportData(
            source_id="jp-001",
            source_type="email",
            content="本番環境でデータベース接続エラーが発生しています。至急対応をお願いいたします。",
            subject="【緊急】システム障害について",
            sender="田中太郎 <tanaka@example.co.jp>",
            received_at=datetime.now(),
            raw_metadata={},
        )

        result = service.analyze(raw_data)

        assert result.is_ok
        analysis_result = result.unwrap()
        assert "緊急" in analysis_result.title
        assert analysis_result.priority == Priority.URGENT
        assert analysis_result.needs_review is False  # confidence 0.95 >= 0.8

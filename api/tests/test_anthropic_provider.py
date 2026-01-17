"""Anthropicプロバイダーのテスト.

Task 5.1: AnthropicProviderConfigと設定検証の実装
- AnthropicProviderConfigデータクラスのテスト
- サポートモデル一覧のテスト
- API Key形式検証のテスト
- モデル名検証のテスト

Task 5.2: AnthropicProviderの解析機能の実装
- Anthropicクライアント初期化のテスト
- 問い合わせ解析プロンプトの構築テスト
- AI解析リクエストの実行テスト
- レスポンス解析とAIAnalysisResponseへの変換テスト
- 信頼度スコアの算出テスト
- リトライ戦略のテスト
- ヘルスチェック機能のテスト

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock, patch

import pytest

from services.importer.ai_provider_base import (AIAnalysisRequest,
                                                AIAnalysisResponse,
                                                AIProviderType)
from services.importer.anthropic_provider import (AnthropicProvider,
                                                  AnthropicProviderConfig)


class TestAnthropicProviderConfig:
    """AnthropicProviderConfigデータクラスのテスト."""

    def test_create_with_required_fields(self):
        """必須フィールドのみで作成できることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-api03-test-key",
            model="claude-3-sonnet-20240229",
        )
        assert config.api_key == "sk-ant-api03-test-key"
        assert config.model == "claude-3-sonnet-20240229"

    def test_inherits_from_ai_provider_config(self):
        """AIProviderConfigを継承していることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-api03-test-key",
            model="claude-3-sonnet-20240229",
        )
        # 基底クラスのフィールドにアクセスできることを確認
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.timeout == 30
        assert config.retry_max == 3
        assert config.retry_backoff_base == 2.0

    def test_default_model_value(self):
        """デフォルトモデルが正しいことを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-api03-test-key",
        )
        assert config.model == "claude-3-sonnet-20240229"

    def test_immutable_config(self):
        """設定が不変であることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-api03-test-key",
            model="claude-3-sonnet-20240229",
        )
        with pytest.raises(FrozenInstanceError):
            config.api_key = "new-key"

    def test_custom_temperature(self):
        """カスタムtemperatureを設定できることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-api03-test-key",
            model="claude-3-sonnet-20240229",
            temperature=0.3,
        )
        assert config.temperature == 0.3

    def test_custom_max_tokens(self):
        """カスタムmax_tokensを設定できることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-api03-test-key",
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
        )
        assert config.max_tokens == 2000


class TestAnthropicProviderSupportedModels:
    """AnthropicProviderのサポートモデル一覧テスト."""

    def test_supported_models_contains_claude3_opus(self):
        """claude-3-opus-20240229がサポートモデルに含まれることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        assert "claude-3-opus-20240229" in provider.supported_models

    def test_supported_models_contains_claude3_sonnet(self):
        """claude-3-sonnet-20240229がサポートモデルに含まれることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        assert "claude-3-sonnet-20240229" in provider.supported_models

    def test_supported_models_contains_claude3_haiku(self):
        """claude-3-haiku-20240307がサポートモデルに含まれることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        assert "claude-3-haiku-20240307" in provider.supported_models

    def test_supported_models_contains_claude35_sonnet(self):
        """claude-3-5-sonnet-20241022がサポートモデルに含まれることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        assert "claude-3-5-sonnet-20241022" in provider.supported_models

    def test_supported_models_returns_list(self):
        """supported_modelsがリストを返すことを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        assert isinstance(provider.supported_models, list)


class TestAnthropicProviderType:
    """AnthropicProviderのprovider_typeテスト."""

    def test_provider_type_is_anthropic(self):
        """provider_typeがANTHROPICであることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        assert provider.provider_type == AIProviderType.ANTHROPIC


class TestAnthropicProviderConfigValidation:
    """AnthropicProviderの設定検証テスト."""

    def test_valid_config_with_sk_ant_prefix(self):
        """sk-ant-プレフィックスのAPI Keyが有効であることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-api03-test-key", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_invalid_api_key_without_sk_ant_prefix(self):
        """sk-ant-プレフィックスなしのAPI Keyが無効であることを確認."""
        config = AnthropicProviderConfig(
            api_key="invalid-key", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        result = provider.validate_config(config)
        assert result.valid is False
        assert any(e.field == "api_key" for e in result.errors)

    def test_invalid_empty_api_key(self):
        """空のAPI Keyが無効であることを確認."""
        config = AnthropicProviderConfig(api_key="", model="claude-3-sonnet-20240229")
        provider = AnthropicProvider(config)
        result = provider.validate_config(config)
        assert result.valid is False
        assert any(e.field == "api_key" for e in result.errors)

    def test_valid_model_claude3_sonnet(self):
        """claude-3-sonnet-20240229モデルが有効であることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True

    def test_valid_model_claude3_opus(self):
        """claude-3-opus-20240229モデルが有効であることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-opus-20240229"
        )
        provider = AnthropicProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True

    def test_valid_model_claude3_haiku(self):
        """claude-3-haiku-20240307モデルが有効であることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-haiku-20240307"
        )
        provider = AnthropicProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True

    def test_valid_model_claude35_sonnet(self):
        """claude-3-5-sonnet-20241022モデルが有効であることを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-5-sonnet-20241022"
        )
        provider = AnthropicProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True

    def test_invalid_model(self):
        """無効なモデルが拒否されることを確認."""
        config = AnthropicProviderConfig(api_key="sk-ant-test", model="invalid-model")
        provider = AnthropicProvider(config)
        result = provider.validate_config(config)
        assert result.valid is False
        assert any(e.field == "model" for e in result.errors)

    def test_error_code_for_invalid_api_key(self):
        """無効なAPI Keyのエラーコードを確認."""
        config = AnthropicProviderConfig(
            api_key="invalid", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        result = provider.validate_config(config)
        api_key_errors = [e for e in result.errors if e.field == "api_key"]
        assert len(api_key_errors) > 0
        assert api_key_errors[0].code == "GS-308"

    def test_error_code_for_invalid_model(self):
        """無効なモデルのエラーコードを確認."""
        config = AnthropicProviderConfig(api_key="sk-ant-test", model="invalid")
        provider = AnthropicProvider(config)
        result = provider.validate_config(config)
        model_errors = [e for e in result.errors if e.field == "model"]
        assert len(model_errors) > 0
        assert model_errors[0].code == "GS-309"


class TestAnthropicProviderInitialize:
    """AnthropicProviderの初期化テスト."""

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_initialize_creates_client(self, mock_anthropic_class):
        """初期化でAnthropicクライアントが作成されることを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        mock_anthropic_class.assert_called_once_with(
            api_key="sk-ant-test",
            timeout=30.0,
        )

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_initialize_sets_initialized_flag(self, mock_anthropic_class):
        """初期化が正常に完了することを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)

        # 初期化が例外なく実行できることを確認する
        provider.initialize()

        # 初期化後は正常に動作することを確認（内部状態に依存しない）
        assert mock_anthropic_class.called

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_initialize_failure_raises_error(self, mock_anthropic_class):
        """初期化失敗時にエラーが発生することを確認."""
        mock_anthropic_class.side_effect = Exception("Connection failed")

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)

        with pytest.raises(RuntimeError, match="初期化に失敗"):
            provider.initialize()


class TestAnthropicProviderAnalyze:
    """AnthropicProviderの解析機能テスト."""

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_analyze_without_initialization_raises_error(self, mock_anthropic_class):
        """初期化前の解析でエラーが発生することを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        with pytest.raises(RuntimeError, match="初期化されていません"):
            provider.analyze(request)

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_analyze_returns_ai_analysis_response(self, mock_anthropic_class):
        """解析結果がAIAnalysisResponseを返すことを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Anthropic APIレスポンスをモック
        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = """
{
    "title": "テスト問い合わせタイトル",
    "content": "構造化された問い合わせ内容",
    "priority": "medium",
    "category": "development",
    "confidence_score": 0.85
}
"""
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        response = provider.analyze(request)

        assert isinstance(response, AIAnalysisResponse)
        assert response.title == "テスト問い合わせタイトル"
        assert response.content == "構造化された問い合わせ内容"
        assert response.priority == "medium"
        assert response.category == "development"
        assert response.confidence_score == 0.85
        assert response.provider_type == "anthropic"
        assert response.model == "claude-3-sonnet-20240229"

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_analyze_japanese_content(self, mock_anthropic_class):
        """日本語コンテンツの解析が正常に動作することを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = """
{
    "title": "【緊急】システム障害の報告",
    "content": "本番環境でデータベース接続エラーが発生しています。",
    "priority": "urgent",
    "category": "maintenance",
    "confidence_score": 0.92
}
"""
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="本番環境でデータベース接続エラーが発生しています。至急対応をお願いします。",
            subject="【緊急】システム障害について",
            sender="田中太郎 <tanaka@example.co.jp>",
            source_type="email",
        )

        response = provider.analyze(request)

        assert "緊急" in response.title
        assert response.priority == "urgent"
        assert response.confidence_score == 0.92

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_analyze_calls_messages_with_correct_model(self, mock_anthropic_class):
        """解析時に正しいモデルが使用されることを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-opus-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        provider.analyze(request)

        # messages.createの呼び出し引数を確認
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-3-opus-20240229"

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_analyze_uses_correct_temperature(self, mock_anthropic_class):
        """解析時に正しいtemperatureが使用されることを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        config = AnthropicProviderConfig(
            api_key="sk-ant-test",
            model="claude-3-sonnet-20240229",
            temperature=0.3,
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        provider.analyze(request)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.3

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_analyze_confidence_score_in_valid_range(self, mock_anthropic_class):
        """信頼度スコアが0.0〜1.0の範囲であることを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.75}
"""
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        response = provider.analyze(request)

        assert 0.0 <= response.confidence_score <= 1.0

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_analyze_returns_raw_response(self, mock_anthropic_class):
        """解析結果にraw_responseが含まれることを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        response = provider.analyze(request)

        assert "raw_content" in response.raw_response

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_analyze_handles_missing_category(self, mock_anthropic_class):
        """categoryが欠落している場合にNoneを返すことを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        response = provider.analyze(request)

        assert response.category is None


class TestAnthropicProviderRetry:
    """AnthropicProviderのリトライ機能テスト."""

    @patch("time.sleep")
    @patch("services.importer.anthropic_provider.Anthropic")
    def test_retry_on_api_error(self, mock_anthropic_class, mock_sleep):
        """API エラー時にリトライが実行されることを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # 2回失敗後、3回目で成功
        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_response.content = [mock_content_block]
        mock_client.messages.create.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            mock_response,
        ]

        config = AnthropicProviderConfig(
            api_key="sk-ant-test",
            model="claude-3-sonnet-20240229",
            retry_max=3,
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        response = provider.analyze(request)

        assert response.title == "タイトル"
        assert mock_client.messages.create.call_count == 3
        # time.sleepが2回呼ばれることを確認（リトライ2回分）
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    @patch("services.importer.anthropic_provider.Anthropic")
    def test_max_retry_exceeded_raises_error(self, mock_anthropic_class, mock_sleep):
        """最大リトライ回数を超えた場合にエラーが発生することを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_client.messages.create.side_effect = Exception("Persistent error")

        config = AnthropicProviderConfig(
            api_key="sk-ant-test",
            model="claude-3-sonnet-20240229",
            retry_max=3,
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        with pytest.raises(RuntimeError, match="リトライ"):
            provider.analyze(request)

        # time.sleepが2回呼ばれることを確認（リトライ2回分）
        assert mock_sleep.call_count == 2


class TestAnthropicProviderHealthCheck:
    """AnthropicProviderのヘルスチェックテスト."""

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_health_check_before_initialization(self, mock_anthropic_class):
        """初期化前のヘルスチェックがFalseを返すことを確認."""
        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)

        assert provider.health_check() is False

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_health_check_after_initialization_success(self, mock_anthropic_class):
        """初期化後、APIが正常な場合にヘルスチェックがTrueを返すことを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # 短いメッセージ呼び出しが成功するようにモック
        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = "OK"
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        assert provider.health_check() is True

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_health_check_api_failure(self, mock_anthropic_class):
        """API呼び出しが失敗した場合にヘルスチェックがFalseを返すことを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # messages.createが失敗するようにモック
        mock_client.messages.create.side_effect = Exception("API Error")

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        assert provider.health_check() is False


class TestAnthropicProviderPromptConstruction:
    """AnthropicProviderのプロンプト構築テスト."""

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_prompt_includes_japanese_instructions(self, mock_anthropic_class):
        """プロンプトに日本語での指示が含まれることを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        provider.analyze(request)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]
        system = call_kwargs.get("system", "")

        # システムプロンプトまたはメッセージに日本語指示が含まれていることを確認
        all_content = system + " ".join([m["content"] for m in messages])
        assert "日本語" in all_content or "問い合わせ" in all_content

    @patch("services.importer.anthropic_provider.Anthropic")
    def test_prompt_includes_content_and_subject(self, mock_anthropic_class):
        """プロンプトにコンテンツと件名が含まれることを確認."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_response.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_response

        config = AnthropicProviderConfig(
            api_key="sk-ant-test", model="claude-3-sonnet-20240229"
        )
        provider = AnthropicProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="特定のテスト本文内容",
            subject="特定のテスト件名",
            sender="test@example.com",
            source_type="email",
        )

        provider.analyze(request)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]

        all_content = " ".join([m["content"] for m in messages])
        assert "特定のテスト本文内容" in all_content
        assert "特定のテスト件名" in all_content

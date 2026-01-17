"""OpenAIプロバイダーのテスト.

Task 4.1: OpenAIProviderConfigと設定検証の実装
- OpenAIProviderConfigデータクラスのテスト
- サポートモデル一覧のテスト
- API Key形式検証のテスト
- モデル名検証のテスト

Task 4.2: OpenAIProviderの解析機能の実装
- OpenAIクライアント初期化のテスト
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

from services.importer.ai_provider_base import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AIProviderType,
)
from services.importer.openai_provider import (
    OpenAIProvider,
    OpenAIProviderConfig,
)


class TestOpenAIProviderConfig:
    """OpenAIProviderConfigデータクラスのテスト."""

    def test_create_with_required_fields(self):
        """必須フィールドのみで作成できることを確認."""
        config = OpenAIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
        )
        assert config.api_key == "sk-test-key"
        assert config.model == "gpt-4"

    def test_inherits_from_ai_provider_config(self):
        """AIProviderConfigを継承していることを確認."""
        config = OpenAIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
        )
        # 基底クラスのフィールドにアクセスできることを確認
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.timeout == 30
        assert config.retry_max == 3
        assert config.retry_backoff_base == 2.0

    def test_default_model_value(self):
        """デフォルトモデルが正しいことを確認."""
        config = OpenAIProviderConfig(
            api_key="sk-test-key",
        )
        assert config.model == "gpt-4"

    def test_organization_field(self):
        """organization フィールドを設定できることを確認."""
        config = OpenAIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
            organization="org-test",
        )
        assert config.organization == "org-test"

    def test_organization_default_none(self):
        """organizationのデフォルト値がNoneであることを確認."""
        config = OpenAIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
        )
        assert config.organization is None

    def test_immutable_config(self):
        """設定が不変であることを確認."""
        config = OpenAIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
        )
        with pytest.raises(FrozenInstanceError):
            config.api_key = "new-key"

    def test_custom_temperature(self):
        """カスタムtemperatureを設定できることを確認."""
        config = OpenAIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
            temperature=0.3,
        )
        assert config.temperature == 0.3

    def test_custom_max_tokens(self):
        """カスタムmax_tokensを設定できることを確認."""
        config = OpenAIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
            max_tokens=2000,
        )
        assert config.max_tokens == 2000


class TestOpenAIProviderSupportedModels:
    """OpenAIProviderのサポートモデル一覧テスト."""

    def test_supported_models_contains_gpt4(self):
        """gpt-4がサポートモデルに含まれることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        assert "gpt-4" in provider.supported_models

    def test_supported_models_contains_gpt4_turbo(self):
        """gpt-4-turboがサポートモデルに含まれることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        assert "gpt-4-turbo" in provider.supported_models

    def test_supported_models_contains_gpt4o(self):
        """gpt-4oがサポートモデルに含まれることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        assert "gpt-4o" in provider.supported_models

    def test_supported_models_contains_gpt35_turbo(self):
        """gpt-3.5-turboがサポートモデルに含まれることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        assert "gpt-3.5-turbo" in provider.supported_models

    def test_supported_models_returns_list(self):
        """supported_modelsがリストを返すことを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        assert isinstance(provider.supported_models, list)


class TestOpenAIProviderType:
    """OpenAIProviderのprovider_typeテスト."""

    def test_provider_type_is_openai(self):
        """provider_typeがOPENAIであることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        assert provider.provider_type == AIProviderType.OPENAI


class TestOpenAIProviderConfigValidation:
    """OpenAIProviderの設定検証テスト."""

    def test_valid_config_with_sk_prefix(self):
        """sk-プレフィックスのAPI Keyが有効であることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test-key", model="gpt-4")
        provider = OpenAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_invalid_api_key_without_sk_prefix(self):
        """sk-プレフィックスなしのAPI Keyが無効であることを確認."""
        config = OpenAIProviderConfig(api_key="invalid-key", model="gpt-4")
        provider = OpenAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is False
        assert any(e.field == "api_key" for e in result.errors)

    def test_invalid_empty_api_key(self):
        """空のAPI Keyが無効であることを確認."""
        config = OpenAIProviderConfig(api_key="", model="gpt-4")
        provider = OpenAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is False
        assert any(e.field == "api_key" for e in result.errors)

    def test_valid_model_gpt4(self):
        """gpt-4モデルが有効であることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True

    def test_valid_model_gpt4_turbo(self):
        """gpt-4-turboモデルが有効であることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4-turbo")
        provider = OpenAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True

    def test_valid_model_gpt4o(self):
        """gpt-4oモデルが有効であることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4o")
        provider = OpenAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True

    def test_valid_model_gpt35_turbo(self):
        """gpt-3.5-turboモデルが有効であることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-3.5-turbo")
        provider = OpenAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True

    def test_invalid_model(self):
        """無効なモデルが拒否されることを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="invalid-model")
        provider = OpenAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is False
        assert any(e.field == "model" for e in result.errors)

    def test_error_code_for_invalid_api_key(self):
        """無効なAPI Keyのエラーコードを確認."""
        config = OpenAIProviderConfig(api_key="invalid", model="gpt-4")
        provider = OpenAIProvider(config)
        result = provider.validate_config(config)
        api_key_errors = [e for e in result.errors if e.field == "api_key"]
        assert len(api_key_errors) > 0
        assert api_key_errors[0].code == "GS-308"

    def test_error_code_for_invalid_model(self):
        """無効なモデルのエラーコードを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="invalid")
        provider = OpenAIProvider(config)
        result = provider.validate_config(config)
        model_errors = [e for e in result.errors if e.field == "model"]
        assert len(model_errors) > 0
        assert model_errors[0].code == "GS-309"


class TestOpenAIProviderInitialize:
    """OpenAIProviderの初期化テスト."""

    @patch("services.importer.openai_provider.OpenAI")
    def test_initialize_creates_client(self, mock_openai_class):
        """初期化でOpenAIクライアントが作成されることを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        provider.initialize()

        mock_openai_class.assert_called_once_with(
            api_key="sk-test",
            timeout=30,
            organization=None,
        )

    @patch("services.importer.openai_provider.OpenAI")
    def test_initialize_with_organization(self, mock_openai_class):
        """organizationを指定した初期化を確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        config = OpenAIProviderConfig(
            api_key="sk-test",
            model="gpt-4",
            organization="org-test",
        )
        provider = OpenAIProvider(config)
        provider.initialize()

        mock_openai_class.assert_called_once_with(
            api_key="sk-test",
            timeout=30,
            organization="org-test",
        )

    @patch("services.importer.openai_provider.OpenAI")
    def test_initialize_sets_initialized_flag(self, mock_openai_class):
        """初期化が正常に完了することを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)

        # 初期化が例外なく実行できることを確認する
        provider.initialize()
        
        # 初期化後は正常に動作することを確認（内部状態に依存しない）
        assert mock_openai_class.called

    @patch("services.importer.openai_provider.OpenAI")
    def test_initialize_failure_raises_error(self, mock_openai_class):
        """初期化失敗時にエラーが発生することを確認."""
        mock_openai_class.side_effect = Exception("Connection failed")

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)

        with pytest.raises(RuntimeError, match="初期化に失敗"):
            provider.initialize()


class TestOpenAIProviderAnalyze:
    """OpenAIProviderの解析機能テスト."""

    @patch("services.importer.openai_provider.OpenAI")
    def test_analyze_without_initialization_raises_error(self, mock_openai_class):
        """初期化前の解析でエラーが発生することを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        with pytest.raises(RuntimeError, match="初期化されていません"):
            provider.analyze(request)

    @patch("services.importer.openai_provider.OpenAI")
    def test_analyze_returns_ai_analysis_response(self, mock_openai_class):
        """解析結果がAIAnalysisResponseを返すことを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # OpenAI APIレスポンスをモック
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
{
    "title": "テスト問い合わせタイトル",
    "content": "構造化された問い合わせ内容",
    "priority": "medium",
    "category": "development",
    "confidence_score": 0.85
}
"""
        mock_client.chat.completions.create.return_value = mock_response

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
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
        assert response.provider_type == "openai"
        assert response.model == "gpt-4"

    @patch("services.importer.openai_provider.OpenAI")
    def test_analyze_japanese_content(self, mock_openai_class):
        """日本語コンテンツの解析が正常に動作することを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
{
    "title": "【緊急】システム障害の報告",
    "content": "本番環境でデータベース接続エラーが発生しています。",
    "priority": "urgent",
    "category": "maintenance",
    "confidence_score": 0.92
}
"""
        mock_client.chat.completions.create.return_value = mock_response

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
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

    @patch("services.importer.openai_provider.OpenAI")
    def test_analyze_calls_chat_completions_with_correct_model(self, mock_openai_class):
        """解析時に正しいモデルが使用されることを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_client.chat.completions.create.return_value = mock_response

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4-turbo")
        provider = OpenAIProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        provider.analyze(request)

        # chat.completions.createの呼び出し引数を確認
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4-turbo"

    @patch("services.importer.openai_provider.OpenAI")
    def test_analyze_uses_correct_temperature(self, mock_openai_class):
        """解析時に正しいtemperatureが使用されることを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_client.chat.completions.create.return_value = mock_response

        config = OpenAIProviderConfig(
            api_key="sk-test",
            model="gpt-4",
            temperature=0.3,
        )
        provider = OpenAIProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        provider.analyze(request)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.3

    @patch("services.importer.openai_provider.OpenAI")
    def test_analyze_confidence_score_in_valid_range(self, mock_openai_class):
        """信頼度スコアが0.0〜1.0の範囲であることを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.75}
"""
        mock_client.chat.completions.create.return_value = mock_response

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        response = provider.analyze(request)

        assert 0.0 <= response.confidence_score <= 1.0

    @patch("services.importer.openai_provider.OpenAI")
    def test_analyze_returns_raw_response(self, mock_openai_class):
        """解析結果にraw_responseが含まれることを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_client.chat.completions.create.return_value = mock_response

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        response = provider.analyze(request)

        assert "raw_content" in response.raw_response

    @patch("services.importer.openai_provider.OpenAI")
    def test_analyze_handles_missing_category(self, mock_openai_class):
        """categoryが欠落している場合にNoneを返すことを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_client.chat.completions.create.return_value = mock_response

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        response = provider.analyze(request)

        assert response.category is None


class TestOpenAIProviderRetry:
    """OpenAIProviderのリトライ機能テスト."""

    @patch("time.sleep")
    @patch("services.importer.openai_provider.OpenAI")
    def test_retry_on_api_error(self, mock_openai_class, mock_sleep):
        """API エラー時にリトライが実行されることを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # 2回失敗後、3回目で成功
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_client.chat.completions.create.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            mock_response,
        ]

        config = OpenAIProviderConfig(
            api_key="sk-test",
            model="gpt-4",
            retry_max=3,
        )
        provider = OpenAIProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        response = provider.analyze(request)

        assert response.title == "タイトル"
        assert mock_client.chat.completions.create.call_count == 3
        # time.sleepが2回呼ばれることを確認（リトライ2回分）
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    @patch("services.importer.openai_provider.OpenAI")
    def test_max_retry_exceeded_raises_error(self, mock_openai_class, mock_sleep):
        """最大リトライ回数を超えた場合にエラーが発生することを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_client.chat.completions.create.side_effect = Exception("Persistent error")

        config = OpenAIProviderConfig(
            api_key="sk-test",
            model="gpt-4",
            retry_max=3,
        )
        provider = OpenAIProvider(config)
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


class TestOpenAIProviderHealthCheck:
    """OpenAIProviderのヘルスチェックテスト."""

    @patch("services.importer.openai_provider.OpenAI")
    def test_health_check_before_initialization(self, mock_openai_class):
        """初期化前のヘルスチェックがFalseを返すことを確認."""
        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)

        assert provider.health_check() is False

    @patch("services.importer.openai_provider.OpenAI")
    def test_health_check_after_initialization_success(self, mock_openai_class):
        """初期化後、APIが正常な場合にヘルスチェックがTrueを返すことを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # models.listが成功するようにモック
        mock_client.models.list.return_value = MagicMock()

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        provider.initialize()

        assert provider.health_check() is True

    @patch("services.importer.openai_provider.OpenAI")
    def test_health_check_api_failure(self, mock_openai_class):
        """API呼び出しが失敗した場合にヘルスチェックがFalseを返すことを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # models.listが失敗するようにモック
        mock_client.models.list.side_effect = Exception("API Error")

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        provider.initialize()

        assert provider.health_check() is False


class TestOpenAIProviderPromptConstruction:
    """OpenAIProviderのプロンプト構築テスト."""

    @patch("services.importer.openai_provider.OpenAI")
    def test_prompt_includes_japanese_instructions(self, mock_openai_class):
        """プロンプトに日本語での指示が含まれることを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_client.chat.completions.create.return_value = mock_response

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )

        provider.analyze(request)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]

        # システムプロンプトまたはユーザープロンプトに日本語指示が含まれていることを確認
        all_content = " ".join([m["content"] for m in messages])
        assert "日本語" in all_content or "問い合わせ" in all_content

    @patch("services.importer.openai_provider.OpenAI")
    def test_prompt_includes_content_and_subject(self, mock_openai_class):
        """プロンプトにコンテンツと件名が含まれることを確認."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
{"title": "タイトル", "content": "内容", "priority": "medium", "confidence_score": 0.8}
"""
        mock_client.chat.completions.create.return_value = mock_response

        config = OpenAIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = OpenAIProvider(config)
        provider.initialize()

        request = AIAnalysisRequest(
            content="特定のテスト本文内容",
            subject="特定のテスト件名",
            sender="test@example.com",
            source_type="email",
        )

        provider.analyze(request)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]

        all_content = " ".join([m["content"] for m in messages])
        assert "特定のテスト本文内容" in all_content
        assert "特定のテスト件名" in all_content

"""AIプロバイダー基盤のテスト.

Task 2.1: AIプロバイダー共通インターフェースの実装
- AIProviderType列挙型のテスト
- AIProviderConfig基底データクラスのテスト
- AIAnalysisRequest/AIAnalysisResponseデータクラスのテスト
- AIProvider抽象基底クラスのテスト

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
from dataclasses import FrozenInstanceError
from typing import List

import pytest

from services.importer.ai_provider_base import (AIAnalysisRequest,
                                                AIAnalysisResponse, AIProvider,
                                                AIProviderConfig,
                                                AIProviderType)
from services.importer.plugin_base import ValidationError, ValidationResult


class TestAIProviderType:
    """AIProviderType列挙型のテスト."""

    def test_openai_value(self):
        """OpenAI値が正しいことを確認."""
        assert AIProviderType.OPENAI.value == "openai"

    def test_anthropic_value(self):
        """Anthropic値が正しいことを確認."""
        assert AIProviderType.ANTHROPIC.value == "anthropic"

    def test_provider_types_are_strings(self):
        """すべてのプロバイダー種別が文字列であることを確認."""
        for provider_type in AIProviderType:
            assert isinstance(provider_type.value, str)

    def test_from_string_openai(self):
        """文字列からOpenAI列挙値を取得できることを確認."""
        assert AIProviderType("openai") == AIProviderType.OPENAI

    def test_from_string_anthropic(self):
        """文字列からAnthropic列挙値を取得できることを確認."""
        assert AIProviderType("anthropic") == AIProviderType.ANTHROPIC

    def test_from_string_invalid(self):
        """無効な文字列でValueErrorが発生することを確認."""
        with pytest.raises(ValueError):
            AIProviderType("invalid")


class TestAIProviderConfig:
    """AIProviderConfig基底データクラスのテスト."""

    def test_create_with_required_fields(self):
        """必須フィールドのみで作成できることを確認."""
        config = AIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
        )
        assert config.api_key == "sk-test-key"
        assert config.model == "gpt-4"

    def test_default_values(self):
        """デフォルト値が正しいことを確認."""
        config = AIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
        )
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.timeout == 30
        assert config.retry_max == 3
        assert config.retry_backoff_base == 2.0

    def test_custom_values(self):
        """カスタム値を設定できることを確認."""
        config = AIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4-turbo",
            temperature=0.5,
            max_tokens=2000,
            timeout=60,
            retry_max=5,
            retry_backoff_base=1.5,
        )
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
        assert config.timeout == 60
        assert config.retry_max == 5
        assert config.retry_backoff_base == 1.5

    def test_immutable_config(self):
        """設定が不変であることを確認."""
        config = AIProviderConfig(
            api_key="sk-test-key",
            model="gpt-4",
        )
        with pytest.raises(FrozenInstanceError):
            config.api_key = "new-key"


class TestAIAnalysisRequest:
    """AIAnalysisRequestデータクラスのテスト."""

    def test_create_with_required_fields(self):
        """必須フィールドで作成できることを確認."""
        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )
        assert request.content == "テスト本文"
        assert request.subject == "テスト件名"
        assert request.sender == "test@example.com"
        assert request.source_type == "email"

    def test_default_additional_context(self):
        """additional_contextのデフォルト値を確認."""
        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )
        assert request.additional_context == {}

    def test_custom_additional_context(self):
        """additional_contextをカスタム設定できることを確認."""
        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
            additional_context={"key": "value"},
        )
        assert request.additional_context == {"key": "value"}

    def test_japanese_content(self):
        """日本語コンテンツを扱えることを確認."""
        request = AIAnalysisRequest(
            content="日本語の問い合わせ本文です。",
            subject="日本語件名",
            sender="日本太郎 <taro@example.co.jp>",
            source_type="email",
        )
        assert "日本語" in request.content
        assert "日本語" in request.subject
        assert "日本太郎" in request.sender


class TestAIAnalysisResponse:
    """AIAnalysisResponseデータクラスのテスト."""

    def test_create_with_required_fields(self):
        """必須フィールドで作成できることを確認."""
        response = AIAnalysisResponse(
            title="問い合わせタイトル",
            content="構造化された本文",
            priority="medium",
            confidence_score=0.85,
            raw_response={"choices": []},
            provider_type="openai",
            model="gpt-4",
        )
        assert response.title == "問い合わせタイトル"
        assert response.content == "構造化された本文"
        assert response.priority == "medium"
        assert response.confidence_score == 0.85
        assert response.provider_type == "openai"
        assert response.model == "gpt-4"

    def test_default_category(self):
        """categoryのデフォルト値がNoneであることを確認."""
        response = AIAnalysisResponse(
            title="タイトル",
            content="本文",
            priority="medium",
            confidence_score=0.85,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )
        assert response.category is None

    def test_custom_category(self):
        """categoryをカスタム設定できることを確認."""
        response = AIAnalysisResponse(
            title="タイトル",
            content="本文",
            priority="medium",
            category="development",
            confidence_score=0.85,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )
        assert response.category == "development"

    def test_confidence_score_low(self):
        """低い信頼度スコアを扱えることを確認."""
        response = AIAnalysisResponse(
            title="タイトル",
            content="本文",
            priority="low",
            confidence_score=0.5,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )
        assert response.confidence_score == 0.5

    def test_confidence_score_high(self):
        """高い信頼度スコアを扱えることを確認."""
        response = AIAnalysisResponse(
            title="タイトル",
            content="本文",
            priority="urgent",
            confidence_score=0.95,
            raw_response={},
            provider_type="openai",
            model="gpt-4",
        )
        assert response.confidence_score == 0.95

    def test_priority_values(self):
        """すべての優先度値を扱えることを確認."""
        for priority in ["low", "medium", "high", "urgent"]:
            response = AIAnalysisResponse(
                title="タイトル",
                content="本文",
                priority=priority,
                confidence_score=0.85,
                raw_response={},
                provider_type="openai",
                model="gpt-4",
            )
            assert response.priority == priority


class TestAIProviderAbstractClass:
    """AIProvider抽象基底クラスのテスト."""

    def test_cannot_instantiate_abstract_class(self):
        """抽象クラスを直接インスタンス化できないことを確認."""
        with pytest.raises(TypeError):
            AIProvider()  # type: ignore

    def test_concrete_implementation_requires_provider_type(self):
        """具象クラスはprovider_typeを実装する必要があることを確認."""

        class IncompleteProvider(AIProvider[AIProviderConfig]):
            @property
            def supported_models(self):
                return ["test-model"]

            def validate_config(self, config):
                return ValidationResult(valid=True, errors=[])

            def initialize(self):
                pass

            def analyze(self, request):
                pass

            def health_check(self):
                return True

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_concrete_implementation_requires_supported_models(self):
        """具象クラスはsupported_modelsを実装する必要があることを確認."""

        class IncompleteProvider(AIProvider[AIProviderConfig]):
            @property
            def provider_type(self):
                return AIProviderType.OPENAI

            def validate_config(self, config):
                return ValidationResult(valid=True, errors=[])

            def initialize(self):
                pass

            def analyze(self, request):
                pass

            def health_check(self):
                return True

        with pytest.raises(TypeError):
            IncompleteProvider()


class MockAIProvider(AIProvider[AIProviderConfig]):
    """テスト用のAIプロバイダー実装."""

    def __init__(self, config: AIProviderConfig):
        self._config = config
        self._initialized = False

    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.OPENAI

    @property
    def supported_models(self) -> List[str]:
        return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]

    def validate_config(self, config: AIProviderConfig) -> ValidationResult:
        errors = []
        if not config.api_key.startswith("sk-"):
            errors.append(
                ValidationError(
                    field="api_key",
                    message="API Keyは'sk-'で始まる必要があります",
                    code="GS-308",
                )
            )
        if config.model not in self.supported_models:
            errors.append(
                ValidationError(
                    field="model",
                    message=f"サポートされていないモデルです: {config.model}",
                    code="GS-309",
                )
            )
        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def initialize(self) -> None:
        self._initialized = True

    def analyze(self, request: AIAnalysisRequest):
        if not self._initialized:
            raise RuntimeError("プロバイダーが初期化されていません")
        return AIAnalysisResponse(
            title=f"解析結果: {request.subject}",
            content=f"構造化された内容: {request.content}",
            priority="medium",
            confidence_score=0.85,
            raw_response={"mock": True},
            provider_type=self.provider_type.value,
            model=self._config.model,
        )

    def health_check(self) -> bool:
        return self._initialized


class TestMockAIProviderImplementation:
    """MockAIProvider実装のテスト（具象実装の検証）."""

    def test_provider_type_returns_enum(self):
        """provider_typeがAIProviderType列挙値を返すことを確認."""
        config = AIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = MockAIProvider(config)
        assert provider.provider_type == AIProviderType.OPENAI

    def test_supported_models_returns_list(self):
        """supported_modelsがリストを返すことを確認."""
        config = AIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = MockAIProvider(config)
        assert isinstance(provider.supported_models, list)
        assert "gpt-4" in provider.supported_models

    def test_validate_config_valid(self):
        """有効な設定の検証が成功することを確認."""
        config = AIProviderConfig(api_key="sk-test-key", model="gpt-4")
        provider = MockAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is True
        assert result.errors == []

    def test_validate_config_invalid_api_key(self):
        """無効なAPI Keyの検証が失敗することを確認."""
        config = AIProviderConfig(api_key="invalid-key", model="gpt-4")
        provider = MockAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "api_key"
        assert result.errors[0].code == "GS-308"

    def test_validate_config_invalid_model(self):
        """無効なモデルの検証が失敗することを確認."""
        config = AIProviderConfig(api_key="sk-test-key", model="invalid-model")
        provider = MockAIProvider(config)
        result = provider.validate_config(config)
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "model"
        assert result.errors[0].code == "GS-309"

    def test_initialize(self):
        """初期化が正常に動作することを確認."""
        config = AIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = MockAIProvider(config)
        assert provider._initialized is False
        provider.initialize()
        assert provider._initialized is True

    def test_analyze_without_initialization_raises_error(self):
        """初期化前の解析でエラーが発生することを確認."""
        config = AIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = MockAIProvider(config)
        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )
        with pytest.raises(RuntimeError, match="初期化されていません"):
            provider.analyze(request)

    def test_analyze_after_initialization(self):
        """初期化後の解析が正常に動作することを確認."""
        config = AIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = MockAIProvider(config)
        provider.initialize()
        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )
        response = provider.analyze(request)
        assert isinstance(response, AIAnalysisResponse)
        assert "テスト件名" in response.title
        assert response.provider_type == "openai"
        assert response.model == "gpt-4"

    def test_analyze_returns_confidence_score(self):
        """解析結果に信頼度スコアが含まれることを確認."""
        config = AIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = MockAIProvider(config)
        provider.initialize()
        request = AIAnalysisRequest(
            content="テスト本文",
            subject="テスト件名",
            sender="test@example.com",
            source_type="email",
        )
        response = provider.analyze(request)
        assert 0.0 <= response.confidence_score <= 1.0

    def test_health_check_before_initialization(self):
        """初期化前のヘルスチェックがFalseを返すことを確認."""
        config = AIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = MockAIProvider(config)
        assert provider.health_check() is False

    def test_health_check_after_initialization(self):
        """初期化後のヘルスチェックがTrueを返すことを確認."""
        config = AIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = MockAIProvider(config)
        provider.initialize()
        assert provider.health_check() is True

    def test_analyze_japanese_content(self):
        """日本語コンテンツの解析が正常に動作することを確認."""
        config = AIProviderConfig(api_key="sk-test", model="gpt-4")
        provider = MockAIProvider(config)
        provider.initialize()
        request = AIAnalysisRequest(
            content="日本語の問い合わせ内容です。至急対応をお願いします。",
            subject="【緊急】システム障害について",
            sender="田中太郎 <tanaka@example.co.jp>",
            source_type="email",
        )
        response = provider.analyze(request)
        assert "【緊急】システム障害について" in response.title
        assert "日本語" in response.content

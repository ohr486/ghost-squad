"""AIProviderRegistryサービスのテスト.

Task 2.2: AIProviderRegistryサービスの実装
- プロバイダー登録・解除機能のテスト
- デフォルトプロバイダー設定機能のテスト
- プロバイダー取得機能のテスト
- 一覧機能のテスト
- AIProviderStatusデータクラスのテスト

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
from typing import List

import pytest

from services.importer.ai_provider_base import (AIAnalysisRequest,
                                                AIAnalysisResponse, AIProvider,
                                                AIProviderConfig,
                                                AIProviderType)
from services.importer.ai_provider_registry import (AIProviderError,
                                                    AIProviderRegistryService,
                                                    AIProviderStatus, Result)
from services.importer.plugin_base import ValidationError, ValidationResult


# =============================================================================
# テスト用モッククラス
# =============================================================================
class MockAIProviderConfig(AIProviderConfig):
    """モックAIプロバイダー設定（AIProviderConfigを直接使用）."""

    pass


class MockOpenAIProvider(AIProvider[AIProviderConfig]):
    """テスト用のOpenAI風プロバイダー実装."""

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

    def analyze(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
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


class MockAnthropicProvider(AIProvider[AIProviderConfig]):
    """テスト用のAnthropic風プロバイダー実装."""

    def __init__(self, config: AIProviderConfig):
        self._config = config
        self._initialized = False

    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.ANTHROPIC

    @property
    def supported_models(self) -> List[str]:
        return ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]

    def validate_config(self, config: AIProviderConfig) -> ValidationResult:
        errors = []
        if not config.api_key.startswith("sk-ant-"):
            errors.append(
                ValidationError(
                    field="api_key",
                    message="API Keyは'sk-ant-'で始まる必要があります",
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

    def analyze(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
        if not self._initialized:
            raise RuntimeError("プロバイダーが初期化されていません")
        return AIAnalysisResponse(
            title=f"Claude解析結果: {request.subject}",
            content=f"Claudeによる構造化: {request.content}",
            priority="medium",
            confidence_score=0.90,
            raw_response={"mock": True, "provider": "anthropic"},
            provider_type=self.provider_type.value,
            model=self._config.model,
        )

    def health_check(self) -> bool:
        return self._initialized


class FailingAIProvider(AIProvider[AIProviderConfig]):
    """初期化に失敗するプロバイダー."""

    def __init__(self, config: AIProviderConfig):
        raise RuntimeError("AIプロバイダーの初期化に失敗しました")

    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.OPENAI

    @property
    def supported_models(self) -> List[str]:
        return ["gpt-4"]

    def validate_config(self, config: AIProviderConfig) -> ValidationResult:
        return ValidationResult(valid=True, errors=[])

    def initialize(self) -> None:
        pass

    def analyze(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
        raise NotImplementedError()

    def health_check(self) -> bool:
        return False


# =============================================================================
# AIProviderStatusデータクラスのテスト
# =============================================================================
class TestAIProviderStatus:
    """AIProviderStatusデータクラスのテスト."""

    def test_create_status_with_required_fields(self) -> None:
        """必須フィールドでAIProviderStatusを作成できる."""
        status = AIProviderStatus(
            provider_type=AIProviderType.OPENAI,
            enabled=True,
            initialized=True,
            is_default=False,
            model="gpt-4",
        )

        assert status.provider_type == AIProviderType.OPENAI
        assert status.enabled is True
        assert status.initialized is True
        assert status.is_default is False
        assert status.model == "gpt-4"
        assert status.error_message is None

    def test_create_status_with_error_message(self) -> None:
        """エラーメッセージ付きでAIProviderStatusを作成できる."""
        status = AIProviderStatus(
            provider_type=AIProviderType.ANTHROPIC,
            enabled=False,
            initialized=False,
            is_default=False,
            model="claude-3-sonnet",
            error_message="API Keyが無効です",
        )

        assert status.provider_type == AIProviderType.ANTHROPIC
        assert status.enabled is False
        assert status.initialized is False
        assert status.error_message == "API Keyが無効です"

    def test_status_is_dataclass(self) -> None:
        """AIProviderStatusはデータクラスである."""
        status = AIProviderStatus(
            provider_type=AIProviderType.OPENAI,
            enabled=True,
            initialized=True,
            is_default=True,
            model="gpt-4",
        )

        assert hasattr(status, "__dataclass_fields__")

    def test_default_provider_flag(self) -> None:
        """デフォルトプロバイダーフラグが設定できる."""
        status = AIProviderStatus(
            provider_type=AIProviderType.OPENAI,
            enabled=True,
            initialized=True,
            is_default=True,
            model="gpt-4",
        )

        assert status.is_default is True


# =============================================================================
# AIProviderErrorのテスト
# =============================================================================
class TestAIProviderError:
    """AIProviderErrorのテスト."""

    def test_create_ai_provider_error(self) -> None:
        """AIProviderErrorを作成できる."""
        error = AIProviderError("GS-308", "AIプロバイダーが見つかりません")

        assert error.code == "GS-308"
        assert error.message == "AIプロバイダーが見つかりません"
        assert str(error) == "[GS-308] AIプロバイダーが見つかりません"


# =============================================================================
# AIProviderRegistryServiceのテスト
# =============================================================================
class TestAIProviderRegistryService:
    """AIProviderRegistryServiceのテスト."""

    @pytest.fixture
    def registry(self) -> AIProviderRegistryService:
        """テスト用のAIProviderRegistryServiceインスタンスを作成."""
        return AIProviderRegistryService()

    @pytest.fixture
    def valid_openai_config(self) -> AIProviderConfig:
        """有効なOpenAI設定を作成."""
        return AIProviderConfig(api_key="sk-test-key", model="gpt-4")

    @pytest.fixture
    def valid_anthropic_config(self) -> AIProviderConfig:
        """有効なAnthropic設定を作成."""
        return AIProviderConfig(api_key="sk-ant-test-key", model="claude-3-sonnet")

    @pytest.fixture
    def invalid_config(self) -> AIProviderConfig:
        """無効な設定を作成."""
        return AIProviderConfig(api_key="invalid-key", model="gpt-4")

    # -------------------------------------------------------------------------
    # register() のテスト
    # -------------------------------------------------------------------------
    def test_register_provider_successfully(
        self, registry: AIProviderRegistryService, valid_openai_config: AIProviderConfig
    ) -> None:
        """プロバイダーを正常に登録できる."""
        result = registry.register(MockOpenAIProvider, valid_openai_config)

        assert result.is_ok
        status = result.unwrap()
        assert status.provider_type == AIProviderType.OPENAI
        assert status.enabled is True
        assert status.initialized is True
        assert status.model == "gpt-4"
        assert status.error_message is None

    def test_register_provider_with_invalid_config(
        self, registry: AIProviderRegistryService, invalid_config: AIProviderConfig
    ) -> None:
        """無効な設定でプロバイダーを登録するとエラーになる."""
        result = registry.register(MockOpenAIProvider, invalid_config)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-309"
        assert "設定検証に失敗しました" in error.message

    def test_register_duplicate_provider_fails(
        self, registry: AIProviderRegistryService, valid_openai_config: AIProviderConfig
    ) -> None:
        """同一provider_typeの重複登録は失敗する."""
        # 最初の登録は成功
        result1 = registry.register(MockOpenAIProvider, valid_openai_config)
        assert result1.is_ok

        # 2回目の登録は失敗
        result2 = registry.register(MockOpenAIProvider, valid_openai_config)
        assert result2.is_err
        error = result2.unwrap_err()
        assert error.code == "GS-308"
        assert "既に登録されています" in error.message

    def test_register_provider_with_initialization_failure(
        self, registry: AIProviderRegistryService, valid_openai_config: AIProviderConfig
    ) -> None:
        """プロバイダーの初期化に失敗した場合、エラーが返される."""
        result = registry.register(FailingAIProvider, valid_openai_config)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-309"
        assert "初期化に失敗しました" in error.message

    def test_register_multiple_different_providers(
        self,
        registry: AIProviderRegistryService,
        valid_openai_config: AIProviderConfig,
        valid_anthropic_config: AIProviderConfig,
    ) -> None:
        """異なるprovider_typeの複数プロバイダーを登録できる."""
        result1 = registry.register(MockOpenAIProvider, valid_openai_config)
        result2 = registry.register(MockAnthropicProvider, valid_anthropic_config)

        assert result1.is_ok
        assert result2.is_ok

        providers = registry.list_providers()
        assert len(providers) == 2

    def test_first_registered_provider_becomes_default(
        self, registry: AIProviderRegistryService, valid_openai_config: AIProviderConfig
    ) -> None:
        """最初に登録されたプロバイダーがデフォルトになる."""
        result = registry.register(MockOpenAIProvider, valid_openai_config)

        assert result.is_ok
        status = result.unwrap()
        assert status.is_default is True

    def test_second_registered_provider_is_not_default(
        self,
        registry: AIProviderRegistryService,
        valid_openai_config: AIProviderConfig,
        valid_anthropic_config: AIProviderConfig,
    ) -> None:
        """2番目に登録されたプロバイダーはデフォルトでない."""
        registry.register(MockOpenAIProvider, valid_openai_config)
        result2 = registry.register(MockAnthropicProvider, valid_anthropic_config)

        assert result2.is_ok
        status = result2.unwrap()
        assert status.is_default is False

    # -------------------------------------------------------------------------
    # unregister() のテスト
    # -------------------------------------------------------------------------
    def test_unregister_provider_successfully(
        self, registry: AIProviderRegistryService, valid_openai_config: AIProviderConfig
    ) -> None:
        """プロバイダーを正常に解除できる."""
        registry.register(MockOpenAIProvider, valid_openai_config)

        result = registry.unregister(AIProviderType.OPENAI)

        assert result.is_ok
        assert registry.get_provider(AIProviderType.OPENAI) is None

    def test_unregister_nonexistent_provider_fails(
        self, registry: AIProviderRegistryService
    ) -> None:
        """存在しないプロバイダーの解除は失敗する."""
        result = registry.unregister(AIProviderType.OPENAI)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-308"
        assert "見つかりません" in error.message

    def test_unregister_default_provider_assigns_new_default(
        self,
        registry: AIProviderRegistryService,
        valid_openai_config: AIProviderConfig,
        valid_anthropic_config: AIProviderConfig,
    ) -> None:
        """デフォルトプロバイダーを解除すると、別のプロバイダーがデフォルトになる."""
        registry.register(MockOpenAIProvider, valid_openai_config)
        registry.register(MockAnthropicProvider, valid_anthropic_config)

        # デフォルト（OpenAI）を解除
        registry.unregister(AIProviderType.OPENAI)

        # Anthropicがデフォルトになる
        anthropic_status = registry.get_provider_status(AIProviderType.ANTHROPIC)
        assert anthropic_status is not None
        assert anthropic_status.is_default is True

    # -------------------------------------------------------------------------
    # set_default() のテスト
    # -------------------------------------------------------------------------
    def test_set_default_successfully(
        self,
        registry: AIProviderRegistryService,
        valid_openai_config: AIProviderConfig,
        valid_anthropic_config: AIProviderConfig,
    ) -> None:
        """デフォルトプロバイダーを設定できる."""
        registry.register(MockOpenAIProvider, valid_openai_config)
        registry.register(MockAnthropicProvider, valid_anthropic_config)

        result = registry.set_default(AIProviderType.ANTHROPIC)

        assert result.is_ok
        status = result.unwrap()
        assert status.is_default is True
        assert status.provider_type == AIProviderType.ANTHROPIC

    def test_set_default_updates_previous_default(
        self,
        registry: AIProviderRegistryService,
        valid_openai_config: AIProviderConfig,
        valid_anthropic_config: AIProviderConfig,
    ) -> None:
        """デフォルト設定時、以前のデフォルトが更新される."""
        registry.register(MockOpenAIProvider, valid_openai_config)
        registry.register(MockAnthropicProvider, valid_anthropic_config)

        # Anthropicをデフォルトに
        registry.set_default(AIProviderType.ANTHROPIC)

        # OpenAIはデフォルトでなくなる
        openai_status = registry.get_provider_status(AIProviderType.OPENAI)
        assert openai_status is not None
        assert openai_status.is_default is False

    def test_set_default_nonexistent_provider_fails(
        self, registry: AIProviderRegistryService
    ) -> None:
        """存在しないプロバイダーをデフォルト設定できない."""
        result = registry.set_default(AIProviderType.OPENAI)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-308"
        assert "見つかりません" in error.message

    def test_only_one_default_provider(
        self,
        registry: AIProviderRegistryService,
        valid_openai_config: AIProviderConfig,
        valid_anthropic_config: AIProviderConfig,
    ) -> None:
        """デフォルトプロバイダーは1つのみ."""
        registry.register(MockOpenAIProvider, valid_openai_config)
        registry.register(MockAnthropicProvider, valid_anthropic_config)

        providers = registry.list_providers()
        default_count = sum(1 for p in providers if p.is_default)
        assert default_count == 1

    # -------------------------------------------------------------------------
    # get_provider() のテスト
    # -------------------------------------------------------------------------
    def test_get_provider_returns_provider_instance(
        self, registry: AIProviderRegistryService, valid_openai_config: AIProviderConfig
    ) -> None:
        """get_providerがプロバイダーインスタンスを返す."""
        registry.register(MockOpenAIProvider, valid_openai_config)

        provider = registry.get_provider(AIProviderType.OPENAI)

        assert provider is not None
        assert isinstance(provider, MockOpenAIProvider)
        assert provider.provider_type == AIProviderType.OPENAI

    def test_get_provider_returns_none_for_nonexistent(
        self, registry: AIProviderRegistryService
    ) -> None:
        """存在しないプロバイダーに対してNoneを返す."""
        provider = registry.get_provider(AIProviderType.OPENAI)

        assert provider is None

    def test_get_provider_without_argument_returns_default(
        self, registry: AIProviderRegistryService, valid_openai_config: AIProviderConfig
    ) -> None:
        """引数なしでget_providerを呼ぶとデフォルトプロバイダーを返す."""
        registry.register(MockOpenAIProvider, valid_openai_config)

        provider = registry.get_provider()

        assert provider is not None
        assert provider.provider_type == AIProviderType.OPENAI

    def test_get_provider_without_argument_returns_none_when_empty(
        self, registry: AIProviderRegistryService
    ) -> None:
        """プロバイダーが登録されていない場合、引数なしでNoneを返す."""
        provider = registry.get_provider()

        assert provider is None

    # -------------------------------------------------------------------------
    # list_providers() のテスト
    # -------------------------------------------------------------------------
    def test_list_providers_returns_empty_list_initially(
        self, registry: AIProviderRegistryService
    ) -> None:
        """初期状態では空のリストを返す."""
        providers = registry.list_providers()

        assert providers == []

    def test_list_providers_returns_all_registered_providers(
        self,
        registry: AIProviderRegistryService,
        valid_openai_config: AIProviderConfig,
        valid_anthropic_config: AIProviderConfig,
    ) -> None:
        """登録済みプロバイダーの一覧を返す."""
        registry.register(MockOpenAIProvider, valid_openai_config)
        registry.register(MockAnthropicProvider, valid_anthropic_config)

        providers = registry.list_providers()

        assert len(providers) == 2
        provider_types = [p.provider_type for p in providers]
        assert AIProviderType.OPENAI in provider_types
        assert AIProviderType.ANTHROPIC in provider_types

    # -------------------------------------------------------------------------
    # get_provider_status() のテスト
    # -------------------------------------------------------------------------
    def test_get_provider_status_returns_status(
        self, registry: AIProviderRegistryService, valid_openai_config: AIProviderConfig
    ) -> None:
        """プロバイダーのステータスを取得できる."""
        registry.register(MockOpenAIProvider, valid_openai_config)

        status = registry.get_provider_status(AIProviderType.OPENAI)

        assert status is not None
        assert status.provider_type == AIProviderType.OPENAI
        assert status.enabled is True
        assert status.initialized is True
        assert status.model == "gpt-4"

    def test_get_provider_status_returns_none_for_nonexistent(
        self, registry: AIProviderRegistryService
    ) -> None:
        """存在しないプロバイダーに対してNoneを返す."""
        status = registry.get_provider_status(AIProviderType.OPENAI)

        assert status is None

    # -------------------------------------------------------------------------
    # 設定検証のテスト
    # -------------------------------------------------------------------------
    def test_validate_config_called_during_registration(
        self, registry: AIProviderRegistryService, invalid_config: AIProviderConfig
    ) -> None:
        """登録時にvalidate_configが呼び出される."""
        result = registry.register(MockOpenAIProvider, invalid_config)

        assert result.is_err
        error = result.unwrap_err()
        assert "設定検証に失敗しました" in error.message


# =============================================================================
# Result型のテスト
# =============================================================================
class TestResult:
    """Result型のテスト."""

    def test_result_ok(self) -> None:
        """成功結果を作成できる."""
        result = Result.ok("success")

        assert result.is_ok
        assert not result.is_err
        assert result.unwrap() == "success"

    def test_result_err(self) -> None:
        """失敗結果を作成できる."""
        error = AIProviderError("GS-308", "エラーメッセージ")
        result = Result.err(error)

        assert not result.is_ok
        assert result.is_err
        assert result.unwrap_err() == error

    def test_unwrap_on_err_raises(self) -> None:
        """失敗結果でunwrapを呼ぶと例外が発生する."""
        error = AIProviderError("GS-308", "エラーメッセージ")
        result = Result.err(error)

        with pytest.raises(ValueError, match="Called unwrap on an Err value"):
            result.unwrap()

    def test_unwrap_err_on_ok_raises(self) -> None:
        """成功結果でunwrap_errを呼ぶと例外が発生する."""
        result = Result.ok("success")

        with pytest.raises(ValueError, match="Called unwrap_err on an Ok value"):
            result.unwrap_err()

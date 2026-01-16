"""AIProviderRegistryサービスモジュール.

Task 2.2: AIProviderRegistryサービスの実装
- プロバイダー登録・解除機能
- デフォルトプロバイダー設定機能
- プロバイダー取得機能
- 一覧機能
- AIProviderStatusデータクラス

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
import logging
from dataclasses import dataclass
from typing import Any, Callable, Generic, List, Optional, TypeVar

from services.importer.ai_provider_base import AIProvider, AIProviderType

# ジェネリック型パラメータ
T = TypeVar("T")
TConfig = TypeVar("TConfig")

# ロガー設定
logger = logging.getLogger(__name__)


@dataclass
class AIProviderStatus:
    """AIプロバイダーの状態を表すデータクラス.

    Attributes:
        provider_type: プロバイダー種別（OPENAI、ANTHROPIC等）
        enabled: プロバイダーが有効かどうか
        initialized: プロバイダーが正常に初期化されたかどうか
        is_default: デフォルトプロバイダーかどうか
        model: 使用しているモデル名
        error_message: 初期化失敗時のエラーメッセージ
    """

    provider_type: AIProviderType
    enabled: bool
    initialized: bool
    is_default: bool
    model: str
    error_message: Optional[str] = None


class AIProviderError(Exception):
    """AIプロバイダー関連のエラー.

    Attributes:
        code: エラーコード（GS-3xx形式）
        message: エラーメッセージ
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class Result(Generic[T]):
    """Result型：成功または失敗を表す.

    Rust風のResult型を簡易実装。
    """

    def __init__(
        self, value: Optional[T] = None, error: Optional[AIProviderError] = None
    ) -> None:
        self._value = value
        self._error = error

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        """成功結果を作成."""
        return cls(value=value)

    @classmethod
    def err(cls, error: AIProviderError) -> "Result[T]":
        """失敗結果を作成."""
        return cls(error=error)

    @property
    def is_ok(self) -> bool:
        """成功かどうかを返す."""
        return self._error is None

    @property
    def is_err(self) -> bool:
        """失敗かどうかを返す."""
        return self._error is not None

    def unwrap(self) -> T:
        """成功時の値を取得。成功でない場合は例外を発生。"""
        if self._error is not None:
            raise ValueError(f"Called unwrap on an Err value: {self._error}")
        return self._value  # type: ignore

    def unwrap_err(self) -> AIProviderError:
        """失敗時のエラーを取得。失敗でない場合は例外を発生."""
        if self._error is None:
            raise ValueError("Called unwrap_err on an Ok value")
        return self._error


@dataclass
class _RegisteredProvider:
    """登録されたプロバイダーの内部表現."""

    provider: AIProvider[Any]
    enabled: bool
    initialized: bool
    is_default: bool
    model: str
    error_message: Optional[str] = None


class AIProviderRegistryService:
    """AIプロバイダー管理サービス.

    AIプロバイダーの登録・解除・デフォルト設定を管理する。

    契約:
        - Preconditions: provider_classはAIProviderを継承していること
        - Postconditions: 登録成功時、get_provider()でインスタンス取得可能
        - Invariants: デフォルトプロバイダーは1つのみ
    """

    def __init__(self) -> None:
        """AIProviderRegistryServiceを初期化."""
        self._providers: dict[AIProviderType, _RegisteredProvider] = {}
        self._default_provider: Optional[AIProviderType] = None

    def register(
        self,
        provider_class: Callable[[TConfig], AIProvider[TConfig]],
        config: TConfig,
    ) -> Result[AIProviderStatus]:
        """プロバイダーを登録する.

        Args:
            provider_class: プロバイダークラス
            config: プロバイダー設定

        Returns:
            Result[AIProviderStatus]: 登録結果
        """
        # 一時的なインスタンスを作成してprovider_typeを取得する
        try:
            temp_instance = provider_class(config)
            provider_type = temp_instance.provider_type
        except Exception as e:
            # 初期化時に例外が発生した場合
            logger.error(f"AIプロバイダー初期化に失敗しました: {e}")
            return Result.err(AIProviderError("GS-309", f"AIプロバイダー初期化に失敗しました: {e}"))

        # 重複チェック
        if provider_type in self._providers:
            return Result.err(
                AIProviderError(
                    "GS-308", f"AIプロバイダー '{provider_type.value}' は既に登録されています"
                )
            )

        # 設定検証
        validation_result = temp_instance.validate_config(config)
        if not validation_result.valid:
            error_messages = "; ".join(
                [f"{e.field}: {e.message}" for e in validation_result.errors]
            )
            logger.error(f"設定検証に失敗しました: {error_messages}")
            return Result.err(
                AIProviderError("GS-309", f"設定検証に失敗しました: {error_messages}")
            )

        # プロバイダーの初期化
        try:
            temp_instance.initialize()
        except Exception as e:
            logger.error(f"AIプロバイダーの初期化に失敗しました: {e}")
            return Result.err(
                AIProviderError("GS-309", f"AIプロバイダーの初期化に失敗しました: {e}")
            )
        # 最初のプロバイダーはデフォルトにする
        is_first = len(self._providers) == 0
        is_default = is_first

        # config からモデル名を取得（AIProviderConfigにmodel属性があることを期待）
        model = getattr(config, "model", "unknown")

        # プロバイダーを登録
        registered = _RegisteredProvider(
            provider=temp_instance,
            enabled=True,
            initialized=True,
            is_default=is_default,
            model=model,
        )
        self._providers[provider_type] = registered

        if is_default:
            self._default_provider = provider_type

        logger.info(
            f"AIプロバイダー '{provider_type.value}' を登録しました " f"(デフォルト: {is_default})"
        )

        return Result.ok(
            AIProviderStatus(
                provider_type=provider_type,
                enabled=True,
                initialized=True,
                is_default=is_default,
                model=model,
            )
        )

    def unregister(self, provider_type: AIProviderType) -> Result[None]:
        """プロバイダーを解除する.

        Args:
            provider_type: 解除するプロバイダーの種別

        Returns:
            Result[None]: 解除結果
        """
        if provider_type not in self._providers:
            return Result.err(
                AIProviderError("GS-308", f"AIプロバイダー '{provider_type.value}' が見つかりません")
            )

        was_default = self._providers[provider_type].is_default

        del self._providers[provider_type]

        # デフォルトプロバイダーが解除された場合、別のプロバイダーをデフォルトにする
        if was_default:
            self._default_provider = None
            if self._providers:
                # 最初に見つかったプロバイダーをデフォルトにする
                new_default_type = next(iter(self._providers.keys()))
                self._providers[new_default_type].is_default = True
                self._default_provider = new_default_type
                logger.info(f"新しいデフォルトプロバイダー: '{new_default_type.value}'")

        logger.info(f"AIプロバイダー '{provider_type.value}' を解除しました")
        return Result.ok(None)

    def set_default(self, provider_type: AIProviderType) -> Result[AIProviderStatus]:
        """デフォルトプロバイダーを設定する.

        Args:
            provider_type: デフォルトに設定するプロバイダーの種別

        Returns:
            Result[AIProviderStatus]: 設定結果
        """
        if provider_type not in self._providers:
            return Result.err(
                AIProviderError("GS-308", f"AIプロバイダー '{provider_type.value}' が見つかりません")
            )

        # 以前のデフォルトを解除
        if self._default_provider and self._default_provider in self._providers:
            self._providers[self._default_provider].is_default = False

        # 新しいデフォルトを設定
        self._providers[provider_type].is_default = True
        self._default_provider = provider_type

        registered = self._providers[provider_type]
        logger.info(f"デフォルトプロバイダーを '{provider_type.value}' に設定しました")

        return Result.ok(
            AIProviderStatus(
                provider_type=provider_type,
                enabled=registered.enabled,
                initialized=registered.initialized,
                is_default=True,
                model=registered.model,
                error_message=registered.error_message,
            )
        )

    def get_provider(
        self, provider_type: Optional[AIProviderType] = None
    ) -> Optional[AIProvider[Any]]:
        """プロバイダーインスタンスを取得する.

        Args:
            provider_type: 取得するプロバイダーの種別（未指定時はデフォルト）

        Returns:
            Optional[AIProvider]: プロバイダーインスタンス（存在しない場合はNone）
        """
        # 引数未指定時はデフォルトプロバイダーを返す
        if provider_type is None:
            if self._default_provider is None:
                return None
            provider_type = self._default_provider

        if provider_type not in self._providers:
            return None

        registered = self._providers[provider_type]
        return registered.provider

    def list_providers(self) -> List[AIProviderStatus]:
        """登録済みプロバイダー一覧を取得する.

        Returns:
            List[AIProviderStatus]: プロバイダーステータスのリスト
        """
        return [
            AIProviderStatus(
                provider_type=provider_type,
                enabled=registered.enabled,
                initialized=registered.initialized,
                is_default=registered.is_default,
                model=registered.model,
                error_message=registered.error_message,
            )
            for provider_type, registered in self._providers.items()
        ]

    def get_provider_status(
        self, provider_type: AIProviderType
    ) -> Optional[AIProviderStatus]:
        """プロバイダーのステータスを取得する.

        Args:
            provider_type: 取得するプロバイダーの種別

        Returns:
            Optional[AIProviderStatus]: プロバイダーステータス（存在しない場合はNone）
        """
        if provider_type not in self._providers:
            return None

        registered = self._providers[provider_type]
        return AIProviderStatus(
            provider_type=provider_type,
            enabled=registered.enabled,
            initialized=registered.initialized,
            is_default=registered.is_default,
            model=registered.model,
            error_message=registered.error_message,
        )

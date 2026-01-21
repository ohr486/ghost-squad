"""YAML設定ファイルローダーモジュール.

Task 11.1: YAML設定ファイルローダーの実装
- importer_config.yaml設定ファイルスキーマの定義
- 環境変数展開機能の実装（${IMAP_SERVER}等）
- プラグイン設定の読み込み
- AIプロバイダー設定の読み込み
- デフォルトプロバイダー設定の読み込み
- アプリケーション起動時のレジストリ初期化

Requirements: 1.1, 1.2, 1.3, 3.1
"""
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from services.importer.ai_provider_base import AIProviderType
from services.importer.ai_provider_registry import AIProviderRegistryService
from services.importer.anthropic_provider import (AnthropicProvider,
                                                  AnthropicProviderConfig)
from services.importer.email_plugin import EmailPlugin, EmailPluginConfig
from services.importer.openai_provider import (OpenAIProvider,
                                               OpenAIProviderConfig)
from services.importer.plugin_registry import PluginRegistryService

# ロガー設定
logger = logging.getLogger(__name__)

# 環境変数パターン: ${VAR_NAME}
ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def expand_env_vars(value: Any) -> Any:
    """環境変数を展開する.

    ${VAR_NAME} 形式の環境変数を実際の値に置換する。
    辞書やリストは再帰的に処理する。

    Args:
        value: 展開対象の値（文字列、辞書、リスト、その他）

    Returns:
        Any: 環境変数が展開された値

    Examples:
        >>> expand_env_vars("${HOME}/test")  # 環境変数が展開される
        "/home/user/test"
        >>> expand_env_vars({"key": "${VAR}"})  # 辞書内も展開
        {"key": "value"}
    """
    if isinstance(value, str):
        # 文字列内の環境変数を展開

        def replace_env_var(match: re.Match[str]) -> str:
            var_name = match.group(1)
            return os.environ.get(var_name, "")

        return ENV_VAR_PATTERN.sub(replace_env_var, value)

    elif isinstance(value, dict):
        # 辞書の場合は再帰的に展開
        return {k: expand_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        # リストの場合は再帰的に展開
        return [expand_env_vars(item) for item in value]

    else:
        # その他の型（int、float、bool、None等）はそのまま返す
        return value


@dataclass
class PluginConfigEntry:
    """プラグイン設定エントリ.

    YAMLファイルから読み込んだプラグイン設定を保持する。

    Attributes:
        enabled: プラグインが有効かどうか
        config: プラグイン固有の設定辞書
    """

    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIProviderConfigEntry:
    """AIプロバイダー設定エントリ.

    YAMLファイルから読み込んだAIプロバイダー設定を保持する。

    Attributes:
        enabled: プロバイダーが有効かどうか
        api_key: API認証キー
        model: 使用するモデル名
        temperature: 生成温度（オプション）
        max_tokens: 最大トークン数（オプション）
        timeout: タイムアウト（オプション）
        retry_max: リトライ回数（オプション）
        retry_backoff_base: リトライバックオフ基数（オプション）
        organization: OpenAI組織ID（オプション）
    """

    api_key: str
    model: str
    enabled: bool = True
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    retry_max: int = 3
    retry_backoff_base: float = 2.0
    organization: Optional[str] = None


@dataclass
class ImporterConfig:
    """インポーター設定.

    YAMLファイルから読み込んだ全体設定を保持する。

    Attributes:
        plugins: プラグイン設定辞書（プラグイン種別 → 設定）
        ai_providers: AIプロバイダー設定辞書（プロバイダー種別 → 設定）
        default_ai_provider: デフォルトAIプロバイダー種別
    """

    plugins: Dict[str, PluginConfigEntry] = field(default_factory=dict)
    ai_providers: Dict[str, AIProviderConfigEntry] = field(default_factory=dict)
    default_ai_provider: Optional[str] = None


def load_importer_config(config_path: Path) -> ImporterConfig:
    """YAML設定ファイルを読み込む.

    Args:
        config_path: 設定ファイルのパス

    Returns:
        ImporterConfig: 読み込んだ設定

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        yaml.YAMLError: YAML形式が不正な場合
    """
    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    # 空ファイルの場合
    if raw_config is None:
        return ImporterConfig()

    # 環境変数を展開
    config_data = expand_env_vars(raw_config)

    # プラグイン設定をパース
    plugins: Dict[str, PluginConfigEntry] = {}
    plugins_data = config_data.get("plugins", {})
    for plugin_type, plugin_config in plugins_data.items():
        plugins[plugin_type] = PluginConfigEntry(
            enabled=plugin_config.get("enabled", True),
            config=plugin_config.get("config", {}),
        )

    # AIプロバイダー設定をパース
    ai_providers: Dict[str, AIProviderConfigEntry] = {}
    ai_providers_data = config_data.get("ai_providers", {})
    providers_data = ai_providers_data.get("providers", {})
    for provider_type, provider_config in providers_data.items():
        ai_providers[provider_type] = AIProviderConfigEntry(
            enabled=provider_config.get("enabled", True),
            api_key=provider_config.get("api_key", ""),
            model=provider_config.get("model", ""),
            temperature=provider_config.get("temperature", 0.7),
            max_tokens=provider_config.get("max_tokens", 1000),
            timeout=provider_config.get("timeout", 30),
            retry_max=provider_config.get("retry_max", 3),
            retry_backoff_base=provider_config.get("retry_backoff_base", 2.0),
            organization=provider_config.get("organization"),
        )

    default_ai_provider = ai_providers_data.get("default")

    return ImporterConfig(
        plugins=plugins,
        ai_providers=ai_providers,
        default_ai_provider=default_ai_provider,
    )


class ImporterConfigLoader:
    """インポーター設定ローダー.

    YAML設定ファイルを読み込み、PluginRegistryとAIProviderRegistryを初期化する。

    使用例:
        ```python
        plugin_registry = PluginRegistryService()
        ai_provider_registry = AIProviderRegistryService()

        loader = ImporterConfigLoader(
            plugin_registry=plugin_registry,
            ai_provider_registry=ai_provider_registry,
        )
        loader.load_from_file(Path("config/importer_config.yaml"))
        ```
    """

    # サポートするプラグイン種別とそのクラス・設定クラスのマッピング
    SUPPORTED_PLUGINS: Dict[str, tuple[type, type]] = {
        "email": (EmailPlugin, EmailPluginConfig),
    }

    # サポートするAIプロバイダー種別とそのクラス・設定クラスのマッピング
    SUPPORTED_AI_PROVIDERS: Dict[str, tuple[type, type, AIProviderType]] = {
        "openai": (OpenAIProvider, OpenAIProviderConfig, AIProviderType.OPENAI),
        "anthropic": (
            AnthropicProvider,
            AnthropicProviderConfig,
            AIProviderType.ANTHROPIC,
        ),
    }

    def __init__(
        self,
        plugin_registry: PluginRegistryService,
        ai_provider_registry: AIProviderRegistryService,
    ) -> None:
        """ImporterConfigLoaderを初期化.

        Args:
            plugin_registry: プラグインレジストリ
            ai_provider_registry: AIプロバイダーレジストリ
        """
        self._plugin_registry = plugin_registry
        self._ai_provider_registry = ai_provider_registry

    def load_from_file(self, config_path: Path) -> None:
        """設定ファイルを読み込んでレジストリを初期化する.

        Args:
            config_path: 設定ファイルのパス

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            yaml.YAMLError: YAML形式が不正な場合
        """
        logger.info(f"設定ファイルを読み込みます: {config_path}")

        config = load_importer_config(config_path)

        # プラグインを登録
        self._register_plugins(config.plugins)

        # AIプロバイダーを登録
        self._register_ai_providers(config.ai_providers)

        # デフォルトAIプロバイダーを設定
        if config.default_ai_provider:
            self._set_default_ai_provider(config.default_ai_provider)

        logger.info("設定ファイルの読み込みが完了しました")

    def _register_plugins(self, plugins: Dict[str, PluginConfigEntry]) -> None:
        """プラグインをレジストリに登録する.

        Args:
            plugins: プラグイン設定辞書
        """
        for plugin_type, entry in plugins.items():
            # 無効なプラグインはスキップ
            if not entry.enabled:
                logger.info(f"プラグイン '{plugin_type}' は無効のためスキップします")
                continue

            # サポートされていないプラグインはスキップ
            if plugin_type not in self.SUPPORTED_PLUGINS:
                logger.warning(f"プラグイン '{plugin_type}' はサポートされていません。スキップします")
                continue

            plugin_class, config_class = self.SUPPORTED_PLUGINS[plugin_type]

            # 設定オブジェクトを作成
            try:
                plugin_config = config_class(**entry.config)
            except TypeError as e:
                logger.error(f"プラグイン '{plugin_type}' の設定が不正です: {e}")
                continue

            # プラグインを登録
            result = self._plugin_registry.register(plugin_class, plugin_config)
            if result.is_err:
                logger.error(f"プラグイン '{plugin_type}' の登録に失敗しました: {result.unwrap_err()}")
            else:
                logger.info(f"プラグイン '{plugin_type}' を登録しました")

    def _register_ai_providers(
        self, ai_providers: Dict[str, AIProviderConfigEntry]
    ) -> None:
        """AIプロバイダーをレジストリに登録する.

        Args:
            ai_providers: AIプロバイダー設定辞書
        """
        for provider_type, entry in ai_providers.items():
            # 無効なプロバイダーはスキップ
            if not entry.enabled:
                logger.info(f"AIプロバイダー '{provider_type}' は無効のためスキップします")
                continue

            # サポートされていないプロバイダーはスキップ
            if provider_type not in self.SUPPORTED_AI_PROVIDERS:
                logger.warning(f"AIプロバイダー '{provider_type}' はサポートされていません。スキップします")
                continue

            provider_class, config_class, _ = self.SUPPORTED_AI_PROVIDERS[provider_type]

            # 設定オブジェクトを作成
            config_kwargs = {
                "api_key": entry.api_key,
                "model": entry.model,
                "temperature": entry.temperature,
                "max_tokens": entry.max_tokens,
                "timeout": entry.timeout,
                "retry_max": entry.retry_max,
                "retry_backoff_base": entry.retry_backoff_base,
            }

            # OpenAI固有の設定
            if provider_type == "openai" and entry.organization:
                config_kwargs["organization"] = entry.organization

            try:
                provider_config = config_class(**config_kwargs)
            except TypeError as e:
                logger.error(f"AIプロバイダー '{provider_type}' の設定が不正です: {e}")
                continue

            # プロバイダーを登録
            result = self._ai_provider_registry.register(
                provider_class, provider_config
            )
            if result.is_err:
                logger.error(
                    f"AIプロバイダー '{provider_type}' の登録に失敗しました: {result.unwrap_err()}"
                )
            else:
                logger.info(f"AIプロバイダー '{provider_type}' を登録しました")

    def _set_default_ai_provider(self, provider_type: str) -> None:
        """デフォルトAIプロバイダーを設定する.

        Args:
            provider_type: デフォルトに設定するプロバイダー種別
        """
        if provider_type not in self.SUPPORTED_AI_PROVIDERS:
            logger.warning(f"デフォルトAIプロバイダー '{provider_type}' はサポートされていません")
            return

        _, _, ai_provider_type = self.SUPPORTED_AI_PROVIDERS[provider_type]

        result = self._ai_provider_registry.set_default(ai_provider_type)
        if result.is_err:
            logger.error(f"デフォルトAIプロバイダーの設定に失敗しました: {result.unwrap_err()}")
        else:
            logger.info(f"デフォルトAIプロバイダーを '{provider_type}' に設定しました")

"""PluginRegistryサービスモジュール.

Task 1.2: PluginRegistryサービスの実装
- プラグイン登録・解除機能
- プラグイン有効/無効切り替え機能
- 設定情報検証機能
- 初期化失敗時のエラーログ記録と自動無効化
- PluginStatusデータクラス

Requirements: 1.1, 1.2, 1.3, 1.5
"""
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from services.importer.plugin_base import DataSourcePlugin
from services.importer.result import BaseError, Result

# ジェネリック型パラメータ
T = TypeVar("T")
TConfig = TypeVar("TConfig")

# ロガー設定
logger = logging.getLogger(__name__)


@dataclass
class PluginStatus:
    """プラグインの状態を表すデータクラス.

    Attributes:
        plugin_type: プラグイン種別（例: 'email', 'sentry'）
        enabled: プラグインが有効かどうか
        initialized: プラグインが正常に初期化されたかどうか
        error_message: 初期化失敗時のエラーメッセージ
    """

    plugin_type: str
    enabled: bool
    initialized: bool
    error_message: Optional[str] = None


@dataclass
class PluginError(BaseError):
    """プラグイン関連のエラー.

    Attributes:
        code: エラーコード（GS-3xx形式）
        message: エラーメッセージ
    """

    pass


@dataclass
class _RegisteredPlugin:
    """登録されたプラグインの内部表現."""

    plugin: DataSourcePlugin[Any]
    enabled: bool
    initialized: bool
    error_message: Optional[str] = None


class PluginRegistryService:
    """プラグイン管理サービス.

    データソースプラグインの登録・解除・有効/無効管理を行う。

    契約:
        - Preconditions: plugin_classはDataSourcePluginを継承していること
        - Postconditions: 登録成功時、get_plugin()でインスタンス取得可能
        - Invariants: 同一plugin_typeは1つのみ登録可能
    """

    def __init__(self) -> None:
        """PluginRegistryServiceを初期化."""
        self._plugins: Dict[str, _RegisteredPlugin] = {}

    def register(
        self,
        plugin_class: Callable[[TConfig], DataSourcePlugin[TConfig]],
        config: TConfig,
    ) -> Result[PluginStatus]:
        """プラグインを登録する.

        Args:
            plugin_class: プラグインクラス
            config: プラグイン設定

        Returns:
            Result[PluginStatus]: 登録結果
        """
        # 一時的なインスタンスを作成して plugin_type を取得する
        # （初期化に失敗した場合は plugin_type は取得できず、エラーとして登録処理を中断する）
        try:
            temp_instance = plugin_class(config)
            plugin_type = temp_instance.plugin_type
        except Exception as e:
            # 初期化時に例外が発生した場合
            logger.error(f"プラグイン初期化に失敗しました: {e}")
            return Result.err(PluginError("GS-302", f"プラグイン初期化に失敗しました: {e}"))

        # 重複チェック
        if plugin_type in self._plugins:
            return Result.err(
                PluginError("GS-301", f"プラグイン '{plugin_type}' は既に登録されています")
            )

        # 設定検証
        validation_result = temp_instance.validate_config(config)
        if not validation_result.valid:
            error_messages = "; ".join(
                [f"{e.field}: {e.message}" for e in validation_result.errors]
            )
            logger.error(f"設定検証に失敗しました: {error_messages}")
            return Result.err(PluginError("GS-302", f"設定検証に失敗しました: {error_messages}"))

        # プラグインを登録
        registered = _RegisteredPlugin(
            plugin=temp_instance,
            enabled=True,
            initialized=True,
        )
        self._plugins[plugin_type] = registered

        logger.info(f"プラグイン '{plugin_type}' を登録しました")

        return Result.ok(
            PluginStatus(
                plugin_type=plugin_type,
                enabled=True,
                initialized=True,
            )
        )

    def unregister(self, plugin_type: str) -> Result[None]:
        """プラグインを解除する.

        Args:
            plugin_type: 解除するプラグインの種別

        Returns:
            Result[None]: 解除結果
        """
        if plugin_type not in self._plugins:
            return Result.err(PluginError("GS-301", f"プラグイン '{plugin_type}' が見つかりません"))

        del self._plugins[plugin_type]
        logger.info(f"プラグイン '{plugin_type}' を解除しました")
        return Result.ok(None)

    def enable(self, plugin_type: str) -> Result[PluginStatus]:
        """プラグインを有効化する.

        Args:
            plugin_type: 有効化するプラグインの種別

        Returns:
            Result[PluginStatus]: 有効化結果
        """
        if plugin_type not in self._plugins:
            return Result.err(PluginError("GS-301", f"プラグイン '{plugin_type}' が見つかりません"))

        registered = self._plugins[plugin_type]
        registered.enabled = True
        logger.info(f"プラグイン '{plugin_type}' を有効化しました")

        return Result.ok(
            PluginStatus(
                plugin_type=plugin_type,
                enabled=True,
                initialized=registered.initialized,
                error_message=registered.error_message,
            )
        )

    def disable(self, plugin_type: str) -> Result[PluginStatus]:
        """プラグインを無効化する.

        Args:
            plugin_type: 無効化するプラグインの種別

        Returns:
            Result[PluginStatus]: 無効化結果
        """
        if plugin_type not in self._plugins:
            return Result.err(PluginError("GS-301", f"プラグイン '{plugin_type}' が見つかりません"))

        registered = self._plugins[plugin_type]
        registered.enabled = False
        logger.info(f"プラグイン '{plugin_type}' を無効化しました")

        return Result.ok(
            PluginStatus(
                plugin_type=plugin_type,
                enabled=False,
                initialized=registered.initialized,
                error_message=registered.error_message,
            )
        )

    def get_plugin(
        self, plugin_type: str, include_disabled: bool = False
    ) -> Optional[DataSourcePlugin[Any]]:
        """プラグインインスタンスを取得する.

        Args:
            plugin_type: 取得するプラグインの種別
            include_disabled: 無効なプラグインも含める場合はTrue

        Returns:
            Optional[DataSourcePlugin]: プラグインインスタンス（存在しない場合はNone）
        """
        if plugin_type not in self._plugins:
            return None

        registered = self._plugins[plugin_type]

        # 無効なプラグインは include_disabled=True の場合のみ返す
        if not registered.enabled and not include_disabled:
            return None

        return registered.plugin

    def list_plugins(self) -> List[PluginStatus]:
        """登録済みプラグイン一覧を取得する.

        Returns:
            List[PluginStatus]: プラグインステータスのリスト
        """
        return [
            PluginStatus(
                plugin_type=plugin_type,
                enabled=registered.enabled,
                initialized=registered.initialized,
                error_message=registered.error_message,
            )
            for plugin_type, registered in self._plugins.items()
        ]

    def get_plugin_status(self, plugin_type: str) -> Optional[PluginStatus]:
        """プラグインのステータスを取得する.

        Args:
            plugin_type: 取得するプラグインの種別

        Returns:
            Optional[PluginStatus]: プラグインステータス（存在しない場合はNone）
        """
        if plugin_type not in self._plugins:
            return None

        registered = self._plugins[plugin_type]
        return PluginStatus(
            plugin_type=plugin_type,
            enabled=registered.enabled,
            initialized=registered.initialized,
            error_message=registered.error_message,
        )

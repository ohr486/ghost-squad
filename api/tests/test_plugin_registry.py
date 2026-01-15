"""PluginRegistryサービスのテスト.

Task 1.2: PluginRegistryサービスの実装
- プラグイン登録・解除機能のテスト
- プラグイン有効/無効切り替え機能のテスト
- 設定情報検証機能のテスト
- 初期化失敗時のエラーログ記録と自動無効化のテスト
- PluginStatusデータクラスのテスト

Requirements: 1.1, 1.2, 1.3, 1.5
"""
from datetime import datetime, timezone
from typing import List

import pytest

from services.importer.plugin_base import (DataSourcePlugin, RawImportData,
                                           ValidationError, ValidationResult)
from services.importer.plugin_registry import (PluginError,
                                               PluginRegistryService,
                                               PluginStatus)


# =============================================================================
# テスト用モッククラス
# =============================================================================
class MockPluginConfig:
    """モックプラグイン設定."""

    def __init__(self, server: str = "localhost", valid: bool = True):
        self.server = server
        self.valid = valid


class MockPlugin(DataSourcePlugin[MockPluginConfig]):
    """テスト用の具象プラグインクラス."""

    def __init__(self, config: MockPluginConfig):
        self._config = config
        self._connected = False
        self._initialized = False

    @property
    def plugin_type(self) -> str:
        return "mock"

    def validate_config(self, config: MockPluginConfig) -> ValidationResult:
        if not config.valid:
            return ValidationResult(
                valid=False,
                errors=[
                    ValidationError(
                        field="server",
                        message="サーバー設定が不正です",
                        code="GS-301",
                    )
                ],
            )
        return ValidationResult(valid=True, errors=[])

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def fetch(self) -> List[RawImportData]:
        if not self._connected:
            raise RuntimeError("Not connected")
        return [
            RawImportData(
                source_id="test-001",
                source_type="mock",
                content="Test content",
                subject="Test subject",
                sender="test@example.com",
                received_at=datetime.now(timezone.utc),
                raw_metadata={},
            )
        ]

    def mark_as_processed(self, source_id: str) -> None:
        pass


class FailingPlugin(DataSourcePlugin[MockPluginConfig]):
    """初期化に失敗するプラグイン."""

    def __init__(self, config: MockPluginConfig):
        # 初期化時に例外をスロー
        raise RuntimeError("初期化に失敗しました")

    @property
    def plugin_type(self) -> str:
        return "failing"

    def validate_config(self, config: MockPluginConfig) -> ValidationResult:
        return ValidationResult(valid=True, errors=[])

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def fetch(self) -> List[RawImportData]:
        return []

    def mark_as_processed(self, source_id: str) -> None:
        pass


class AnotherMockPlugin(DataSourcePlugin[MockPluginConfig]):
    """別のテスト用プラグイン."""

    def __init__(self, config: MockPluginConfig):
        self._config = config

    @property
    def plugin_type(self) -> str:
        return "another"

    def validate_config(self, config: MockPluginConfig) -> ValidationResult:
        return ValidationResult(valid=True, errors=[])

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def fetch(self) -> List[RawImportData]:
        return []

    def mark_as_processed(self, source_id: str) -> None:
        pass


# =============================================================================
# PluginStatusデータクラスのテスト
# =============================================================================
class TestPluginStatus:
    """PluginStatusデータクラスのテスト."""

    def test_create_plugin_status_with_required_fields(self) -> None:
        """必須フィールドでPluginStatusを作成できる."""
        status = PluginStatus(
            plugin_type="email",
            enabled=True,
            initialized=True,
        )

        assert status.plugin_type == "email"
        assert status.enabled is True
        assert status.initialized is True
        assert status.error_message is None

    def test_create_plugin_status_with_error_message(self) -> None:
        """エラーメッセージ付きでPluginStatusを作成できる."""
        status = PluginStatus(
            plugin_type="email",
            enabled=False,
            initialized=False,
            error_message="初期化に失敗しました",
        )

        assert status.plugin_type == "email"
        assert status.enabled is False
        assert status.initialized is False
        assert status.error_message == "初期化に失敗しました"

    def test_plugin_status_is_dataclass(self) -> None:
        """PluginStatusはデータクラスである."""
        status = PluginStatus(
            plugin_type="email",
            enabled=True,
            initialized=True,
        )

        assert hasattr(status, "__dataclass_fields__")


# =============================================================================
# PluginErrorのテスト
# =============================================================================
class TestPluginError:
    """PluginErrorのテスト."""

    def test_create_plugin_error(self) -> None:
        """PluginErrorを作成できる."""
        error = PluginError("GS-301", "プラグインが見つかりません")

        assert error.code == "GS-301"
        assert error.message == "プラグインが見つかりません"
        assert str(error) == "[GS-301] プラグインが見つかりません"


# =============================================================================
# PluginRegistryServiceのテスト
# =============================================================================
class TestPluginRegistryService:
    """PluginRegistryServiceのテスト."""

    @pytest.fixture
    def registry(self) -> PluginRegistryService:
        """テスト用のPluginRegistryServiceインスタンスを作成."""
        return PluginRegistryService()

    @pytest.fixture
    def valid_config(self) -> MockPluginConfig:
        """有効な設定を作成."""
        return MockPluginConfig(server="localhost", valid=True)

    @pytest.fixture
    def invalid_config(self) -> MockPluginConfig:
        """無効な設定を作成."""
        return MockPluginConfig(server="", valid=False)

    # -------------------------------------------------------------------------
    # register() のテスト
    # -------------------------------------------------------------------------
    def test_register_plugin_successfully(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """プラグインを正常に登録できる."""
        result = registry.register(MockPlugin, valid_config)

        assert result.is_ok
        status = result.unwrap()
        assert status.plugin_type == "mock"
        assert status.enabled is True
        assert status.initialized is True
        assert status.error_message is None

    def test_register_plugin_with_invalid_config(
        self, registry: PluginRegistryService, invalid_config: MockPluginConfig
    ) -> None:
        """無効な設定でプラグインを登録するとエラーになる."""
        result = registry.register(MockPlugin, invalid_config)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-302"
        assert "設定検証に失敗しました" in error.message

    def test_register_duplicate_plugin_fails(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """同一plugin_typeの重複登録は失敗する."""
        # 最初の登録は成功
        result1 = registry.register(MockPlugin, valid_config)
        assert result1.is_ok

        # 2回目の登録は失敗
        result2 = registry.register(MockPlugin, valid_config)
        assert result2.is_err
        error = result2.unwrap_err()
        assert error.code == "GS-301"
        assert "既に登録されています" in error.message

    def test_register_plugin_with_initialization_failure(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """プラグインの初期化に失敗した場合、エラーが返される."""
        result = registry.register(FailingPlugin, valid_config)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-302"
        assert "初期化に失敗しました" in error.message

    def test_register_multiple_different_plugins(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """異なるplugin_typeの複数プラグインを登録できる."""
        result1 = registry.register(MockPlugin, valid_config)
        result2 = registry.register(AnotherMockPlugin, valid_config)

        assert result1.is_ok
        assert result2.is_ok

        plugins = registry.list_plugins()
        assert len(plugins) == 2

    # -------------------------------------------------------------------------
    # unregister() のテスト
    # -------------------------------------------------------------------------
    def test_unregister_plugin_successfully(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """プラグインを正常に解除できる."""
        registry.register(MockPlugin, valid_config)

        result = registry.unregister("mock")

        assert result.is_ok
        assert registry.get_plugin("mock") is None

    def test_unregister_nonexistent_plugin_fails(
        self, registry: PluginRegistryService
    ) -> None:
        """存在しないプラグインの解除は失敗する."""
        result = registry.unregister("nonexistent")

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-301"
        assert "見つかりません" in error.message

    # -------------------------------------------------------------------------
    # enable() のテスト
    # -------------------------------------------------------------------------
    def test_enable_plugin_successfully(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """プラグインを有効化できる."""
        registry.register(MockPlugin, valid_config)
        registry.disable("mock")

        result = registry.enable("mock")

        assert result.is_ok
        status = result.unwrap()
        assert status.enabled is True

    def test_enable_already_enabled_plugin(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """既に有効なプラグインを有効化しても成功する."""
        registry.register(MockPlugin, valid_config)

        result = registry.enable("mock")

        assert result.is_ok
        status = result.unwrap()
        assert status.enabled is True

    def test_enable_nonexistent_plugin_fails(
        self, registry: PluginRegistryService
    ) -> None:
        """存在しないプラグインの有効化は失敗する."""
        result = registry.enable("nonexistent")

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-301"

    # -------------------------------------------------------------------------
    # disable() のテスト
    # -------------------------------------------------------------------------
    def test_disable_plugin_successfully(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """プラグインを無効化できる."""
        registry.register(MockPlugin, valid_config)

        result = registry.disable("mock")

        assert result.is_ok
        status = result.unwrap()
        assert status.enabled is False

    def test_disable_already_disabled_plugin(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """既に無効なプラグインを無効化しても成功する."""
        registry.register(MockPlugin, valid_config)
        registry.disable("mock")

        result = registry.disable("mock")

        assert result.is_ok
        status = result.unwrap()
        assert status.enabled is False

    def test_disable_nonexistent_plugin_fails(
        self, registry: PluginRegistryService
    ) -> None:
        """存在しないプラグインの無効化は失敗する."""
        result = registry.disable("nonexistent")

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-301"

    # -------------------------------------------------------------------------
    # get_plugin() のテスト
    # -------------------------------------------------------------------------
    def test_get_plugin_returns_plugin_instance(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """get_pluginがプラグインインスタンスを返す."""
        registry.register(MockPlugin, valid_config)

        plugin = registry.get_plugin("mock")

        assert plugin is not None
        assert isinstance(plugin, MockPlugin)
        assert plugin.plugin_type == "mock"

    def test_get_plugin_returns_none_for_nonexistent(
        self, registry: PluginRegistryService
    ) -> None:
        """存在しないプラグインに対してNoneを返す."""
        plugin = registry.get_plugin("nonexistent")

        assert plugin is None

    def test_get_disabled_plugin_returns_none(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """無効なプラグインに対してNoneを返す."""
        registry.register(MockPlugin, valid_config)
        registry.disable("mock")

        plugin = registry.get_plugin("mock")

        assert plugin is None

    def test_get_disabled_plugin_with_include_disabled(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """include_disabled=Trueの場合、無効なプラグインも取得できる."""
        registry.register(MockPlugin, valid_config)
        registry.disable("mock")

        plugin = registry.get_plugin("mock", include_disabled=True)

        assert plugin is not None
        assert plugin.plugin_type == "mock"

    # -------------------------------------------------------------------------
    # list_plugins() のテスト
    # -------------------------------------------------------------------------
    def test_list_plugins_returns_empty_list_initially(
        self, registry: PluginRegistryService
    ) -> None:
        """初期状態では空のリストを返す."""
        plugins = registry.list_plugins()

        assert plugins == []

    def test_list_plugins_returns_all_registered_plugins(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """登録済みプラグインの一覧を返す."""
        registry.register(MockPlugin, valid_config)
        registry.register(AnotherMockPlugin, valid_config)

        plugins = registry.list_plugins()

        assert len(plugins) == 2
        plugin_types = [p.plugin_type for p in plugins]
        assert "mock" in plugin_types
        assert "another" in plugin_types

    def test_list_plugins_includes_disabled_plugins(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """無効なプラグインも一覧に含まれる."""
        registry.register(MockPlugin, valid_config)
        registry.disable("mock")

        plugins = registry.list_plugins()

        assert len(plugins) == 1
        assert plugins[0].enabled is False

    # -------------------------------------------------------------------------
    # get_plugin_status() のテスト
    # -------------------------------------------------------------------------
    def test_get_plugin_status_returns_status(
        self, registry: PluginRegistryService, valid_config: MockPluginConfig
    ) -> None:
        """プラグインのステータスを取得できる."""
        registry.register(MockPlugin, valid_config)

        status = registry.get_plugin_status("mock")

        assert status is not None
        assert status.plugin_type == "mock"
        assert status.enabled is True
        assert status.initialized is True

    def test_get_plugin_status_returns_none_for_nonexistent(
        self, registry: PluginRegistryService
    ) -> None:
        """存在しないプラグインに対してNoneを返す."""
        status = registry.get_plugin_status("nonexistent")

        assert status is None

    # -------------------------------------------------------------------------
    # 設定検証のテスト
    # -------------------------------------------------------------------------
    def test_validate_config_called_during_registration(
        self, registry: PluginRegistryService, invalid_config: MockPluginConfig
    ) -> None:
        """登録時にvalidate_configが呼び出される."""
        result = registry.register(MockPlugin, invalid_config)

        assert result.is_err
        error = result.unwrap_err()
        assert "設定検証に失敗しました" in error.message

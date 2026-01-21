"""YAML設定ファイルローダーのテストモジュール.

Task 11.1: YAML設定ファイルローダーの実装
- importer_config.yaml設定ファイルスキーマの定義
- 環境変数展開機能の実装（${IMAP_SERVER}等）
- プラグイン設定の読み込み
- AIプロバイダー設定の読み込み
- デフォルトプロバイダー設定の読み込み
- アプリケーション起動時のレジストリ初期化

Requirements: 1.1, 1.2, 1.3, 3.1
"""
import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
import yaml

from services.importer.importer_config_loader import (AIProviderConfigEntry,
                                                      ImporterConfig,
                                                      ImporterConfigLoader,
                                                      PluginConfigEntry,
                                                      expand_env_vars,
                                                      load_importer_config)


class TestExpandEnvVars:
    """環境変数展開機能のテスト."""

    def test_expand_single_env_var(self) -> None:
        """単一の環境変数が展開される."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = expand_env_vars("${TEST_VAR}")
            assert result == "test_value"

    def test_expand_multiple_env_vars(self) -> None:
        """複数の環境変数が展開される."""
        with patch.dict(os.environ, {"VAR1": "value1", "VAR2": "value2"}):
            result = expand_env_vars("${VAR1} and ${VAR2}")
            assert result == "value1 and value2"

    def test_expand_env_var_in_text(self) -> None:
        """テキスト中の環境変数が展開される."""
        with patch.dict(os.environ, {"SERVER": "imap.example.com"}):
            result = expand_env_vars("Server is ${SERVER}:993")
            assert result == "Server is imap.example.com:993"

    def test_missing_env_var_returns_empty(self) -> None:
        """存在しない環境変数は空文字に置換される."""
        with patch.dict(os.environ, {}, clear=True):
            # 環境変数が存在しない場合は空文字に置換
            result = expand_env_vars("${NONEXISTENT_VAR}")
            assert result == ""

    def test_no_env_vars_returns_original(self) -> None:
        """環境変数がない文字列はそのまま返される."""
        result = expand_env_vars("plain text without vars")
        assert result == "plain text without vars"

    def test_empty_string_returns_empty(self) -> None:
        """空文字列は空文字列のまま返される."""
        result = expand_env_vars("")
        assert result == ""

    def test_expand_env_var_in_dict(self) -> None:
        """辞書内の環境変数が再帰的に展開される."""
        with patch.dict(os.environ, {"SERVER": "imap.example.com", "USER": "test"}):
            data = {
                "imap_server": "${SERVER}",
                "username": "${USER}",
                "port": 993,  # 数値はそのまま
            }
            result = expand_env_vars(data)
            assert result == {
                "imap_server": "imap.example.com",
                "username": "test",
                "port": 993,
            }

    def test_expand_env_var_in_list(self) -> None:
        """リスト内の環境変数が再帰的に展開される."""
        with patch.dict(os.environ, {"VAR1": "value1", "VAR2": "value2"}):
            data = ["${VAR1}", "${VAR2}", "plain"]
            result = expand_env_vars(data)
            assert result == ["value1", "value2", "plain"]


class TestPluginConfigEntry:
    """PluginConfigEntryのテスト."""

    def test_create_plugin_config_entry(self) -> None:
        """PluginConfigEntryの作成."""
        entry = PluginConfigEntry(
            enabled=True,
            config={
                "imap_server": "imap.example.com",
                "username": "user@example.com",
                "password": "secret",
            },
        )
        assert entry.enabled is True
        assert entry.config["imap_server"] == "imap.example.com"

    def test_plugin_config_entry_defaults(self) -> None:
        """PluginConfigEntryのデフォルト値."""
        entry = PluginConfigEntry()
        assert entry.enabled is True
        assert entry.config == {}


class TestAIProviderConfigEntry:
    """AIProviderConfigEntryのテスト."""

    def test_create_ai_provider_config_entry(self) -> None:
        """AIProviderConfigEntryの作成."""
        entry = AIProviderConfigEntry(
            enabled=True,
            api_key="sk-test-key",
            model="gpt-4",
        )
        assert entry.enabled is True
        assert entry.api_key == "sk-test-key"
        assert entry.model == "gpt-4"

    def test_ai_provider_config_entry_defaults(self) -> None:
        """AIProviderConfigEntryのデフォルト値."""
        entry = AIProviderConfigEntry(api_key="", model="")
        assert entry.enabled is True
        assert entry.api_key == ""
        assert entry.model == ""


class TestImporterConfig:
    """ImporterConfigのテスト."""

    def test_create_importer_config(self) -> None:
        """ImporterConfigの作成."""
        config = ImporterConfig(
            plugins={
                "email": PluginConfigEntry(
                    enabled=True,
                    config={"imap_server": "imap.example.com"},
                )
            },
            ai_providers={
                "openai": AIProviderConfigEntry(
                    enabled=True,
                    api_key="sk-test",
                    model="gpt-4",
                )
            },
            default_ai_provider="openai",
        )
        assert "email" in config.plugins
        assert "openai" in config.ai_providers
        assert config.default_ai_provider == "openai"

    def test_importer_config_defaults(self) -> None:
        """ImporterConfigのデフォルト値."""
        config = ImporterConfig()
        assert config.plugins == {}
        assert config.ai_providers == {}
        assert config.default_ai_provider is None


class TestLoadImporterConfig:
    """設定ファイル読み込み機能のテスト."""

    @pytest.fixture
    def temp_config_file(self) -> Generator[Path, None, None]:
        """一時的な設定ファイルを作成するフィクスチャ."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yield Path(f.name)
        # クリーンアップ
        Path(f.name).unlink(missing_ok=True)

    def test_load_valid_config(self, temp_config_file: Path) -> None:
        """有効な設定ファイルを読み込む."""
        config_content = {
            "plugins": {
                "email": {
                    "enabled": True,
                    "config": {
                        "imap_server": "imap.example.com",
                        "imap_port": 993,
                        "username": "user@example.com",
                        "password": "secret",
                        "folder": "INBOX",
                    },
                }
            },
            "ai_providers": {
                "default": "openai",
                "providers": {
                    "openai": {
                        "enabled": True,
                        "api_key": "sk-test-key",
                        "model": "gpt-4",
                    }
                },
            },
        }
        temp_config_file.write_text(yaml.dump(config_content))

        result = load_importer_config(temp_config_file)

        assert "email" in result.plugins
        assert result.plugins["email"].enabled is True
        assert result.plugins["email"].config["imap_server"] == "imap.example.com"
        assert "openai" in result.ai_providers
        assert result.ai_providers["openai"].api_key == "sk-test-key"
        assert result.default_ai_provider == "openai"

    def test_load_config_with_env_vars(self, temp_config_file: Path) -> None:
        """環境変数を含む設定ファイルを読み込む."""
        config_content = {
            "plugins": {
                "email": {
                    "enabled": True,
                    "config": {
                        "imap_server": "${IMAP_SERVER}",
                        "username": "${IMAP_USERNAME}",
                        "password": "${IMAP_PASSWORD}",
                    },
                }
            },
            "ai_providers": {
                "default": "openai",
                "providers": {
                    "openai": {
                        "enabled": True,
                        "api_key": "${OPENAI_API_KEY}",
                        "model": "gpt-4",
                    }
                },
            },
        }
        temp_config_file.write_text(yaml.dump(config_content))

        with patch.dict(
            os.environ,
            {
                "IMAP_SERVER": "imap.test.com",
                "IMAP_USERNAME": "testuser",
                "IMAP_PASSWORD": "testpass",
                "OPENAI_API_KEY": "sk-expanded-key",
            },
        ):
            result = load_importer_config(temp_config_file)

        assert result.plugins["email"].config["imap_server"] == "imap.test.com"
        assert result.plugins["email"].config["username"] == "testuser"
        assert result.plugins["email"].config["password"] == "testpass"
        assert result.ai_providers["openai"].api_key == "sk-expanded-key"

    def test_load_config_file_not_found(self) -> None:
        """存在しないファイルを読み込むとエラー."""
        with pytest.raises(FileNotFoundError):
            load_importer_config(Path("/nonexistent/path/config.yaml"))

    def test_load_config_invalid_yaml(self, temp_config_file: Path) -> None:
        """不正なYAML形式のファイルを読み込むとエラー."""
        temp_config_file.write_text("invalid: yaml: content: :")

        with pytest.raises(yaml.YAMLError):
            load_importer_config(temp_config_file)

    def test_load_empty_config(self, temp_config_file: Path) -> None:
        """空の設定ファイルを読み込む."""
        temp_config_file.write_text("")

        result = load_importer_config(temp_config_file)

        assert result.plugins == {}
        assert result.ai_providers == {}
        assert result.default_ai_provider is None


class TestImporterConfigLoader:
    """ImporterConfigLoaderクラスのテスト."""

    @pytest.fixture
    def temp_config_file(self) -> Generator[Path, None, None]:
        """一時的な設定ファイルを作成するフィクスチャ."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def mock_plugin_registry(self) -> MagicMock:
        """モックのPluginRegistry."""
        return MagicMock()

    @pytest.fixture
    def mock_ai_provider_registry(self) -> MagicMock:
        """モックのAIProviderRegistry."""
        return MagicMock()

    def test_loader_init(
        self,
        mock_plugin_registry: MagicMock,
        mock_ai_provider_registry: MagicMock,
    ) -> None:
        """ImporterConfigLoaderの初期化."""
        loader = ImporterConfigLoader(
            plugin_registry=mock_plugin_registry,
            ai_provider_registry=mock_ai_provider_registry,
        )
        assert loader._plugin_registry is mock_plugin_registry
        assert loader._ai_provider_registry is mock_ai_provider_registry

    def test_load_and_initialize_plugins(
        self,
        temp_config_file: Path,
        mock_plugin_registry: MagicMock,
        mock_ai_provider_registry: MagicMock,
    ) -> None:
        """プラグイン設定を読み込んでレジストリに登録する."""
        config_content = {
            "plugins": {
                "email": {
                    "enabled": True,
                    "config": {
                        "imap_server": "imap.example.com",
                        "imap_port": 993,
                        "username": "user@example.com",
                        "password": "secret",
                        "folder": "INBOX",
                    },
                }
            },
            "ai_providers": {"default": None, "providers": {}},
        }
        temp_config_file.write_text(yaml.dump(config_content))

        # registerがResult.okを返すようにモック (is_errプロパティを持つResultを使用)
        from services.importer.plugin_registry import PluginStatus
        from services.importer.result import Result

        result_mock = Result.ok(
            PluginStatus(
                plugin_type="email",
                enabled=True,
                initialized=True,
            )
        )
        mock_plugin_registry.register.return_value = result_mock

        loader = ImporterConfigLoader(
            plugin_registry=mock_plugin_registry,
            ai_provider_registry=mock_ai_provider_registry,
        )
        loader.load_from_file(temp_config_file)

        # registerが呼ばれたことを確認
        mock_plugin_registry.register.assert_called_once()

    def test_load_and_initialize_ai_providers(
        self,
        temp_config_file: Path,
        mock_plugin_registry: MagicMock,
        mock_ai_provider_registry: MagicMock,
    ) -> None:
        """AIプロバイダー設定を読み込んでレジストリに登録する."""
        config_content = {
            "plugins": {},
            "ai_providers": {
                "default": "openai",
                "providers": {
                    "openai": {
                        "enabled": True,
                        "api_key": "sk-test-key",
                        "model": "gpt-4",
                    }
                },
            },
        }
        temp_config_file.write_text(yaml.dump(config_content))

        # registerがResult.okを返すようにモック (is_errプロパティを持つResultを使用)
        from services.importer.ai_provider_base import AIProviderType
        from services.importer.ai_provider_registry import AIProviderStatus
        from services.importer.result import Result

        result_mock = Result.ok(
            AIProviderStatus(
                provider_type=AIProviderType.OPENAI,
                enabled=True,
                initialized=True,
                is_default=True,
                model="gpt-4",
            )
        )
        mock_ai_provider_registry.register.return_value = result_mock
        mock_ai_provider_registry.set_default.return_value = result_mock

        loader = ImporterConfigLoader(
            plugin_registry=mock_plugin_registry,
            ai_provider_registry=mock_ai_provider_registry,
        )
        loader.load_from_file(temp_config_file)

        # registerが呼ばれたことを確認
        mock_ai_provider_registry.register.assert_called_once()

    def test_load_sets_default_ai_provider(
        self,
        temp_config_file: Path,
        mock_plugin_registry: MagicMock,
        mock_ai_provider_registry: MagicMock,
    ) -> None:
        """デフォルトAIプロバイダーを設定する."""
        config_content = {
            "plugins": {},
            "ai_providers": {
                "default": "anthropic",
                "providers": {
                    "openai": {
                        "enabled": True,
                        "api_key": "sk-test-key",
                        "model": "gpt-4",
                    },
                    "anthropic": {
                        "enabled": True,
                        "api_key": "sk-ant-test-key",
                        "model": "claude-3-sonnet-20240229",
                    },
                },
            },
        }
        temp_config_file.write_text(yaml.dump(config_content))

        from services.importer.ai_provider_base import AIProviderType
        from services.importer.ai_provider_registry import AIProviderStatus
        from services.importer.result import Result

        # registerがResult.okを返すようにモック (is_errプロパティを持つResultを使用)
        register_result = Result.ok(
            AIProviderStatus(
                provider_type=AIProviderType.OPENAI,
                enabled=True,
                initialized=True,
                is_default=False,
                model="gpt-4",
            )
        )
        set_default_result = Result.ok(
            AIProviderStatus(
                provider_type=AIProviderType.ANTHROPIC,
                enabled=True,
                initialized=True,
                is_default=True,
                model="claude-3-sonnet-20240229",
            )
        )
        mock_ai_provider_registry.register.return_value = register_result
        mock_ai_provider_registry.set_default.return_value = set_default_result

        loader = ImporterConfigLoader(
            plugin_registry=mock_plugin_registry,
            ai_provider_registry=mock_ai_provider_registry,
        )
        loader.load_from_file(temp_config_file)

        # set_defaultが呼ばれたことを確認
        mock_ai_provider_registry.set_default.assert_called_once_with(
            AIProviderType.ANTHROPIC
        )

    def test_load_disabled_plugin_not_registered(
        self,
        temp_config_file: Path,
        mock_plugin_registry: MagicMock,
        mock_ai_provider_registry: MagicMock,
    ) -> None:
        """無効なプラグインは登録されない."""
        config_content = {
            "plugins": {
                "email": {
                    "enabled": False,  # 無効
                    "config": {
                        "imap_server": "imap.example.com",
                    },
                }
            },
            "ai_providers": {"default": None, "providers": {}},
        }
        temp_config_file.write_text(yaml.dump(config_content))

        loader = ImporterConfigLoader(
            plugin_registry=mock_plugin_registry,
            ai_provider_registry=mock_ai_provider_registry,
        )
        loader.load_from_file(temp_config_file)

        # registerが呼ばれないことを確認
        mock_plugin_registry.register.assert_not_called()

    def test_load_disabled_ai_provider_not_registered(
        self,
        temp_config_file: Path,
        mock_plugin_registry: MagicMock,
        mock_ai_provider_registry: MagicMock,
    ) -> None:
        """無効なAIプロバイダーは登録されない."""
        config_content = {
            "plugins": {},
            "ai_providers": {
                "default": None,
                "providers": {
                    "openai": {
                        "enabled": False,  # 無効
                        "api_key": "sk-test-key",
                        "model": "gpt-4",
                    }
                },
            },
        }
        temp_config_file.write_text(yaml.dump(config_content))

        loader = ImporterConfigLoader(
            plugin_registry=mock_plugin_registry,
            ai_provider_registry=mock_ai_provider_registry,
        )
        loader.load_from_file(temp_config_file)

        # registerが呼ばれないことを確認
        mock_ai_provider_registry.register.assert_not_called()

    def test_load_multiple_plugins(
        self,
        temp_config_file: Path,
        mock_plugin_registry: MagicMock,
        mock_ai_provider_registry: MagicMock,
    ) -> None:
        """複数のプラグインを読み込む（将来の拡張性テスト）."""
        config_content = {
            "plugins": {
                "email": {
                    "enabled": True,
                    "config": {
                        "imap_server": "imap.example.com",
                        "username": "user@example.com",
                        "password": "secret",
                    },
                },
                # 将来追加されるプラグイン（現在は未実装なのでスキップされる）
                "sentry": {
                    "enabled": True,
                    "config": {"dsn": "https://sentry.example.com"},
                },
            },
            "ai_providers": {"default": None, "providers": {}},
        }
        temp_config_file.write_text(yaml.dump(config_content))

        from services.importer.plugin_registry import PluginStatus
        from services.importer.result import Result

        result_mock = Result.ok(
            PluginStatus(plugin_type="email", enabled=True, initialized=True)
        )
        mock_plugin_registry.register.return_value = result_mock

        loader = ImporterConfigLoader(
            plugin_registry=mock_plugin_registry,
            ai_provider_registry=mock_ai_provider_registry,
        )
        # 登録可能なプラグインのみ登録される（emailのみ）
        loader.load_from_file(temp_config_file)

        # emailプラグインのみ登録される
        assert mock_plugin_registry.register.call_count == 1


class TestImporterConfigLoaderIntegration:
    """ImporterConfigLoaderの統合テスト（実際のレジストリを使用）."""

    @pytest.fixture
    def temp_config_file(self) -> Generator[Path, None, None]:
        """一時的な設定ファイルを作成するフィクスチャ."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    def test_full_integration_with_email_plugin(self, temp_config_file: Path) -> None:
        """メールプラグインの完全な統合テスト."""
        config_content = {
            "plugins": {
                "email": {
                    "enabled": True,
                    "config": {
                        "imap_server": "imap.example.com",
                        "imap_port": 993,
                        "username": "user@example.com",
                        "password": "secret",
                        "folder": "INBOX",
                        "use_ssl": True,
                        "fetch_limit": 50,
                        "retry_max": 3,
                        "retry_backoff_base": 2.0,
                    },
                }
            },
            "ai_providers": {"default": None, "providers": {}},
        }
        temp_config_file.write_text(yaml.dump(config_content))

        from services.importer.ai_provider_registry import \
            AIProviderRegistryService
        from services.importer.plugin_registry import PluginRegistryService

        plugin_registry = PluginRegistryService()
        ai_provider_registry = AIProviderRegistryService()

        loader = ImporterConfigLoader(
            plugin_registry=plugin_registry,
            ai_provider_registry=ai_provider_registry,
        )
        loader.load_from_file(temp_config_file)

        # プラグインが登録されていることを確認
        plugins = plugin_registry.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].plugin_type == "email"
        assert plugins[0].enabled is True
        assert plugins[0].initialized is True

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-for-integration"})
    def test_full_integration_with_openai_provider(
        self, temp_config_file: Path
    ) -> None:
        """OpenAIプロバイダーの完全な統合テスト（API呼び出しはしない）."""
        config_content = {
            "plugins": {},
            "ai_providers": {
                "default": "openai",
                "providers": {
                    "openai": {
                        "enabled": True,
                        "api_key": "${OPENAI_API_KEY}",
                        "model": "gpt-4",
                    }
                },
            },
        }
        temp_config_file.write_text(yaml.dump(config_content))

        from services.importer.ai_provider_registry import \
            AIProviderRegistryService
        from services.importer.plugin_registry import PluginRegistryService

        plugin_registry = PluginRegistryService()
        ai_provider_registry = AIProviderRegistryService()

        loader = ImporterConfigLoader(
            plugin_registry=plugin_registry,
            ai_provider_registry=ai_provider_registry,
        )

        # OpenAI初期化をモックしてAPI呼び出しを避ける
        with patch("services.importer.openai_provider.OpenAI"):
            loader.load_from_file(temp_config_file)

        # プロバイダーが登録されていることを確認
        providers = ai_provider_registry.list_providers()
        assert len(providers) == 1
        from services.importer.ai_provider_base import AIProviderType

        assert providers[0].provider_type == AIProviderType.OPENAI
        assert providers[0].is_default is True

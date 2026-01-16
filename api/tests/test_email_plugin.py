"""EmailPluginConfigとEmailPluginのユニットテスト.

Task 3.1: EmailPluginConfigと設定検証の実装
- EmailPluginConfigデータクラスのテスト
- 設定検証ロジックのテスト（必須フィールド、ポート範囲、フォルダ名形式）

Requirements: 2.1, 2.3
"""
import pytest

from services.importer.email_plugin import (EmailPlugin, EmailPluginConfig,
                                            EmailPluginConfigValidator)


class TestEmailPluginConfig:
    """EmailPluginConfigのテストスイート."""

    def test_create_with_defaults(self) -> None:
        """デフォルト値でConfigを作成できることを確認."""
        config = EmailPluginConfig(
            imap_server="imap.example.com",
            username="user@example.com",
            password="secret123",
        )

        assert config.imap_server == "imap.example.com"
        assert config.username == "user@example.com"
        assert config.password == "secret123"
        assert config.imap_port == 993
        assert config.folder == "INBOX"
        assert config.use_ssl is True
        assert config.fetch_limit == 50
        assert config.retry_max == 3
        assert config.retry_backoff_base == 2.0

    def test_create_with_custom_values(self) -> None:
        """カスタム値でConfigを作成できることを確認."""
        config = EmailPluginConfig(
            imap_server="mail.example.com",
            imap_port=143,
            username="admin@example.com",
            password="admin_pass",
            folder="Support/Tickets",
            use_ssl=False,
            fetch_limit=100,
            retry_max=5,
            retry_backoff_base=3.0,
        )

        assert config.imap_server == "mail.example.com"
        assert config.imap_port == 143
        assert config.username == "admin@example.com"
        assert config.password == "admin_pass"
        assert config.folder == "Support/Tickets"
        assert config.use_ssl is False
        assert config.fetch_limit == 100
        assert config.retry_max == 5
        assert config.retry_backoff_base == 3.0

    def test_config_is_frozen(self) -> None:
        """Configが不変（frozen）であることを確認."""
        config = EmailPluginConfig(
            imap_server="imap.example.com",
            username="user@example.com",
            password="secret123",
        )

        with pytest.raises(AttributeError):
            config.imap_server = "other.example.com"  # type: ignore


class TestEmailPluginConfigValidator:
    """EmailPluginConfigValidatorのテストスイート."""

    def _create_valid_config(self, **overrides) -> EmailPluginConfig:
        """テスト用の有効なConfigを作成."""
        defaults = {
            "imap_server": "imap.example.com",
            "username": "user@example.com",
            "password": "secret123",
        }
        defaults.update(overrides)
        return EmailPluginConfig(**defaults)

    # --- 有効な設定のテスト ---

    def test_valid_config_passes_validation(self) -> None:
        """有効な設定が検証を通過することを確認."""
        config = self._create_valid_config()
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_valid_config_with_custom_folder(self) -> None:
        """カスタムフォルダ名が検証を通過することを確認."""
        config = self._create_valid_config(folder="Support/Tickets")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is True

    def test_valid_config_with_japanese_folder(self) -> None:
        """日本語フォルダ名が検証を通過することを確認."""
        config = self._create_valid_config(folder="受信トレイ/サポート")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is True

    def test_valid_config_with_underscore_folder(self) -> None:
        """アンダースコアを含むフォルダ名が検証を通過することを確認."""
        config = self._create_valid_config(folder="INBOX_archive")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is True

    def test_valid_config_with_dot_folder(self) -> None:
        """ドットを含むフォルダ名が検証を通過することを確認."""
        config = self._create_valid_config(folder="INBOX.Archive")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is True

    def test_valid_config_with_min_port(self) -> None:
        """最小ポート番号（1）が検証を通過することを確認."""
        config = self._create_valid_config(imap_port=1)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is True

    def test_valid_config_with_max_port(self) -> None:
        """最大ポート番号（65535）が検証を通過することを確認."""
        config = self._create_valid_config(imap_port=65535)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is True

    def test_valid_config_with_retry_zero(self) -> None:
        """リトライ回数0が検証を通過することを確認."""
        config = self._create_valid_config(retry_max=0)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is True

    # --- imap_server検証のテスト ---

    def test_empty_imap_server_fails(self) -> None:
        """空のIMAPサーバーが検証に失敗することを確認."""
        config = self._create_valid_config(imap_server="")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "imap_server"
        assert result.errors[0].code == "GS-310"
        assert "必須" in result.errors[0].message

    def test_whitespace_imap_server_fails(self) -> None:
        """空白のみのIMAPサーバーが検証に失敗することを確認."""
        config = self._create_valid_config(imap_server="   ")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert any(e.field == "imap_server" for e in result.errors)

    # --- imap_port検証のテスト ---

    def test_port_below_minimum_fails(self) -> None:
        """ポート番号0が検証に失敗することを確認."""
        config = self._create_valid_config(imap_port=0)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "imap_port"
        assert result.errors[0].code == "GS-311"

    def test_port_above_maximum_fails(self) -> None:
        """ポート番号65536が検証に失敗することを確認."""
        config = self._create_valid_config(imap_port=65536)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "imap_port"
        assert result.errors[0].code == "GS-311"

    def test_negative_port_fails(self) -> None:
        """負のポート番号が検証に失敗することを確認."""
        config = self._create_valid_config(imap_port=-1)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert any(e.field == "imap_port" for e in result.errors)

    # --- username検証のテスト ---

    def test_empty_username_fails(self) -> None:
        """空のユーザー名が検証に失敗することを確認."""
        config = self._create_valid_config(username="")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "username"
        assert result.errors[0].code == "GS-312"
        assert "必須" in result.errors[0].message

    def test_whitespace_username_fails(self) -> None:
        """空白のみのユーザー名が検証に失敗することを確認."""
        config = self._create_valid_config(username="   ")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert any(e.field == "username" for e in result.errors)

    # --- password検証のテスト ---

    def test_empty_password_fails(self) -> None:
        """空のパスワードが検証に失敗することを確認."""
        config = self._create_valid_config(password="")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "password"
        assert result.errors[0].code == "GS-313"
        assert "必須" in result.errors[0].message

    def test_whitespace_password_fails(self) -> None:
        """空白のみのパスワードが検証に失敗することを確認."""
        config = self._create_valid_config(password="   ")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert any(e.field == "password" for e in result.errors)

    # --- folder検証のテスト ---

    def test_empty_folder_fails(self) -> None:
        """空のフォルダ名が検証に失敗することを確認."""
        config = self._create_valid_config(folder="")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert any(e.field == "folder" for e in result.errors)
        assert any(e.code == "GS-314" for e in result.errors)

    def test_whitespace_folder_fails(self) -> None:
        """空白のみのフォルダ名が検証に失敗することを確認."""
        config = self._create_valid_config(folder="   ")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert any(e.field == "folder" for e in result.errors)

    def test_folder_with_invalid_chars_fails(self) -> None:
        """無効な文字を含むフォルダ名が検証に失敗することを確認."""
        # 制御文字を含むフォルダ名
        config = self._create_valid_config(folder="INBOX\x00Archive")
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert any(e.field == "folder" for e in result.errors)
        assert any(e.code == "GS-315" for e in result.errors)

    # --- fetch_limit検証のテスト ---

    def test_fetch_limit_zero_fails(self) -> None:
        """取得上限0が検証に失敗することを確認."""
        config = self._create_valid_config(fetch_limit=0)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "fetch_limit"
        assert result.errors[0].code == "GS-316"

    def test_fetch_limit_negative_fails(self) -> None:
        """負の取得上限が検証に失敗することを確認."""
        config = self._create_valid_config(fetch_limit=-1)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert any(e.field == "fetch_limit" for e in result.errors)

    def test_fetch_limit_above_maximum_fails(self) -> None:
        """取得上限が最大値を超えた場合に検証に失敗することを確認."""
        config = self._create_valid_config(fetch_limit=1001)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "fetch_limit"
        assert result.errors[0].code == "GS-317"

    def test_fetch_limit_at_maximum_passes(self) -> None:
        """取得上限が最大値の場合に検証を通過することを確認."""
        config = self._create_valid_config(fetch_limit=1000)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is True

    # --- retry_max検証のテスト ---

    def test_negative_retry_max_fails(self) -> None:
        """負のリトライ回数が検証に失敗することを確認."""
        config = self._create_valid_config(retry_max=-1)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "retry_max"
        assert result.errors[0].code == "GS-318"

    # --- retry_backoff_base検証のテスト ---

    def test_zero_backoff_base_fails(self) -> None:
        """リトライバックオフ基数0が検証に失敗することを確認."""
        config = self._create_valid_config(retry_backoff_base=0.0)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "retry_backoff_base"
        assert result.errors[0].code == "GS-319"

    def test_negative_backoff_base_fails(self) -> None:
        """負のリトライバックオフ基数が検証に失敗することを確認."""
        config = self._create_valid_config(retry_backoff_base=-1.0)
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        assert any(e.field == "retry_backoff_base" for e in result.errors)

    # --- 複数エラーのテスト ---

    def test_multiple_errors_returned(self) -> None:
        """複数のエラーが同時に返されることを確認."""
        config = EmailPluginConfig(
            imap_server="",
            username="",
            password="",
            imap_port=0,
            folder="",
            fetch_limit=0,
            retry_max=-1,
            retry_backoff_base=0.0,
        )
        result = EmailPluginConfigValidator.validate(config)

        assert result.valid is False
        # 少なくとも複数のエラーが返される
        assert len(result.errors) >= 5

        # 各フィールドのエラーが含まれることを確認
        error_fields = [e.field for e in result.errors]
        assert "imap_server" in error_fields
        assert "username" in error_fields
        assert "password" in error_fields
        assert "imap_port" in error_fields
        assert "folder" in error_fields


class TestEmailPlugin:
    """EmailPluginのテストスイート."""

    def _create_valid_config(self) -> EmailPluginConfig:
        """テスト用の有効なConfigを作成."""
        return EmailPluginConfig(
            imap_server="imap.example.com",
            username="user@example.com",
            password="secret123",
        )

    def test_plugin_type_is_email(self) -> None:
        """plugin_typeが'email'であることを確認."""
        plugin = EmailPlugin(self._create_valid_config())
        assert plugin.plugin_type == "email"

    def test_config_is_accessible(self) -> None:
        """設定にアクセスできることを確認."""
        config = self._create_valid_config()
        plugin = EmailPlugin(config)

        assert plugin.config == config
        assert plugin.config.imap_server == "imap.example.com"

    def test_validate_config_with_valid_config(self) -> None:
        """有効な設定でvalidate_configが成功することを確認."""
        plugin = EmailPlugin(self._create_valid_config())
        result = plugin.validate_config(self._create_valid_config())

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_config_with_invalid_config(self) -> None:
        """無効な設定でvalidate_configが失敗することを確認."""
        plugin = EmailPlugin(self._create_valid_config())
        invalid_config = EmailPluginConfig(
            imap_server="",
            username="",
            password="",
        )
        result = plugin.validate_config(invalid_config)

        assert result.valid is False
        assert len(result.errors) > 0

    def test_connect_raises_not_implemented(self) -> None:
        """connectがNotImplementedErrorを発生させることを確認."""
        plugin = EmailPlugin(self._create_valid_config())

        with pytest.raises(NotImplementedError):
            plugin.connect()

    def test_disconnect_raises_not_implemented(self) -> None:
        """disconnectがNotImplementedErrorを発生させることを確認."""
        plugin = EmailPlugin(self._create_valid_config())

        with pytest.raises(NotImplementedError):
            plugin.disconnect()

    def test_fetch_raises_not_implemented(self) -> None:
        """fetchがNotImplementedErrorを発生させることを確認."""
        plugin = EmailPlugin(self._create_valid_config())

        with pytest.raises(NotImplementedError):
            plugin.fetch()

    def test_mark_as_processed_raises_not_implemented(self) -> None:
        """mark_as_processedがNotImplementedErrorを発生させることを確認."""
        plugin = EmailPlugin(self._create_valid_config())

        with pytest.raises(NotImplementedError):
            plugin.mark_as_processed("test-message-id")


class TestEmailPluginWithPluginRegistry:
    """EmailPluginとPluginRegistryの統合テスト."""

    def test_register_email_plugin(self) -> None:
        """EmailPluginをPluginRegistryに登録できることを確認."""
        from services.importer.plugin_registry import PluginRegistryService

        registry = PluginRegistryService()
        config = EmailPluginConfig(
            imap_server="imap.example.com",
            username="user@example.com",
            password="secret123",
        )

        result = registry.register(EmailPlugin, config)

        assert result.is_ok
        status = result.unwrap()
        assert status.plugin_type == "email"
        assert status.enabled is True
        assert status.initialized is True

    def test_register_email_plugin_with_invalid_config(self) -> None:
        """無効な設定でEmailPluginを登録するとエラーになることを確認."""
        from services.importer.plugin_registry import PluginRegistryService

        registry = PluginRegistryService()
        config = EmailPluginConfig(
            imap_server="",  # 無効
            username="user@example.com",
            password="secret123",
        )

        result = registry.register(EmailPlugin, config)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == "GS-302"

    def test_get_registered_email_plugin(self) -> None:
        """登録したEmailPluginを取得できることを確認."""
        from services.importer.plugin_registry import PluginRegistryService

        registry = PluginRegistryService()
        config = EmailPluginConfig(
            imap_server="imap.example.com",
            username="user@example.com",
            password="secret123",
        )
        registry.register(EmailPlugin, config)

        plugin = registry.get_plugin("email")

        assert plugin is not None
        assert plugin.plugin_type == "email"
        assert isinstance(plugin, EmailPlugin)

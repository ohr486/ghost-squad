"""EmailPluginConfigとEmailPluginのユニットテスト.

Task 3.1: EmailPluginConfigと設定検証の実装
- EmailPluginConfigデータクラスのテスト
- 設定検証ロジックのテスト（必須フィールド、ポート範囲、フォルダ名形式）

Task 3.2: EmailPluginのIMAP接続機能の実装
- IMAP4_SSLによるメールサーバー接続のテスト
- 接続切断のテスト
- リトライ戦略のテスト

Requirements: 2.1, 2.3, 2.5
"""
import socket
from datetime import timezone
from unittest.mock import MagicMock, call, patch

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

    def test_connect_attempts_connection(self) -> None:
        """connectが接続を試みることを確認（実際のサーバーがないためエラーになる）."""
        from services.importer.email_plugin import EmailConnectionError

        plugin = EmailPlugin(
            EmailPluginConfig(
                imap_server="nonexistent.server.example.com",
                username="user@example.com",
                password="secret123",
                retry_max=0,  # リトライなしで即座にエラー
            )
        )

        with pytest.raises(EmailConnectionError):
            plugin.connect()

    def test_disconnect_when_not_connected_is_safe(self) -> None:
        """未接続状態でdisconnectを呼び出しても安全であることを確認."""
        plugin = EmailPlugin(self._create_valid_config())

        # エラーが発生しないことを確認
        plugin.disconnect()
        assert plugin.is_connected is False

    def test_fetch_raises_error_when_not_connected(self) -> None:
        """未接続状態でfetchがRuntimeErrorを発生させることを確認."""
        plugin = EmailPlugin(self._create_valid_config())

        with pytest.raises(RuntimeError) as exc_info:
            plugin.fetch()

        assert "接続されていません" in str(exc_info.value)

    def test_mark_as_processed_raises_error_when_not_connected(self) -> None:
        """未接続状態でmark_as_processedがRuntimeErrorを発生させることを確認."""
        plugin = EmailPlugin(self._create_valid_config())

        with pytest.raises(RuntimeError) as exc_info:
            plugin.mark_as_processed("test-message-id")

        assert "接続されていません" in str(exc_info.value)


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


class TestEmailPluginConnection:
    """EmailPluginのIMAP接続機能テストスイート.

    Task 3.2: EmailPluginのIMAP接続機能の実装
    - IMAP4_SSLによるメールサーバー接続の実装（connect）
    - 接続切断の実装（disconnect）
    - 指数バックオフによるリトライ戦略の実装（最大3回、2^n秒）
    - 接続失敗時のエラーハンドリングとエラー通知
    - タイムアウト設定（30秒）

    Requirements: 2.1, 2.5
    """

    def _create_valid_config(self, **overrides) -> EmailPluginConfig:
        """テスト用の有効なConfigを作成."""
        defaults = {
            "imap_server": "imap.example.com",
            "username": "user@example.com",
            "password": "secret123",
        }
        defaults.update(overrides)
        return EmailPluginConfig(**defaults)

    # --- 接続成功のテスト ---

    def test_connect_success_with_ssl(self) -> None:
        """SSL接続が成功することを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ) as mock_imap_class:
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            mock_imap_class.assert_called_once_with("imap.example.com", 993, timeout=30)
            mock_imap.login.assert_called_once_with("user@example.com", "secret123")
            mock_imap.select.assert_called_once_with("INBOX")
            assert plugin.is_connected is True

    def test_connect_success_without_ssl(self) -> None:
        """非SSL接続が成功することを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4",
            return_value=mock_imap,
        ) as mock_imap_class:
            config = self._create_valid_config(use_ssl=False, imap_port=143)
            plugin = EmailPlugin(config)
            plugin.connect()

            mock_imap_class.assert_called_once_with("imap.example.com", 143, timeout=30)
            mock_imap.login.assert_called_once()
            assert plugin.is_connected is True

    def test_connect_with_custom_folder(self) -> None:
        """カスタムフォルダへの接続が成功することを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config(folder="Support/Tickets")
            plugin = EmailPlugin(config)
            plugin.connect()

            mock_imap.select.assert_called_once_with("Support/Tickets")

    # --- 接続失敗とリトライのテスト ---

    def test_connect_retries_on_connection_error(self) -> None:
        """接続エラー時にリトライすることを確認."""
        mock_imap_success = MagicMock()
        mock_imap_success.login.return_value = ("OK", [b"Logged in"])
        mock_imap_success.select.return_value = ("OK", [b"1"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
        ) as mock_imap_class, patch(
            "services.importer.email_plugin.time.sleep"
        ) as mock_sleep:
            # 最初の2回は失敗、3回目で成功
            mock_imap_class.side_effect = [
                socket.error("Connection refused"),
                socket.timeout("Connection timed out"),
                mock_imap_success,
            ]

            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            # 3回呼ばれることを確認
            assert mock_imap_class.call_count == 3
            # 指数バックオフで待機: 2^0=1秒、2^1=2秒
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1.0)  # 2^0
            mock_sleep.assert_any_call(2.0)  # 2^1
            assert plugin.is_connected is True

    def test_connect_raises_after_max_retries(self) -> None:
        """最大リトライ回数を超えた場合にエラーが発生することを確認."""
        from services.importer.email_plugin import EmailConnectionError

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
        ) as mock_imap_class, patch(
            "services.importer.email_plugin.time.sleep"
        ) as mock_sleep:
            # 全回失敗
            mock_imap_class.side_effect = socket.error("Connection refused")

            config = self._create_valid_config(retry_max=3)
            plugin = EmailPlugin(config)

            with pytest.raises(EmailConnectionError) as exc_info:
                plugin.connect()

            # 初回 + 3回リトライ = 4回
            assert mock_imap_class.call_count == 4
            assert mock_sleep.call_count == 3
            assert plugin.is_connected is False
            assert "GS-303" in str(exc_info.value)

    def test_connect_with_zero_retries(self) -> None:
        """リトライ回数0の場合、リトライなしでエラーが発生することを確認."""
        from services.importer.email_plugin import EmailConnectionError

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
        ) as mock_imap_class, patch(
            "services.importer.email_plugin.time.sleep"
        ) as mock_sleep:
            mock_imap_class.side_effect = socket.error("Connection refused")

            config = self._create_valid_config(retry_max=0)
            plugin = EmailPlugin(config)

            with pytest.raises(EmailConnectionError):
                plugin.connect()

            assert mock_imap_class.call_count == 1
            assert mock_sleep.call_count == 0

    def test_connect_retries_with_custom_backoff_base(self) -> None:
        """カスタムバックオフ基数でリトライすることを確認."""
        from services.importer.email_plugin import EmailConnectionError

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
        ) as mock_imap_class, patch(
            "services.importer.email_plugin.time.sleep"
        ) as mock_sleep:
            mock_imap_class.side_effect = socket.error("Connection refused")

            config = self._create_valid_config(retry_max=2, retry_backoff_base=3.0)
            plugin = EmailPlugin(config)

            with pytest.raises(EmailConnectionError):
                plugin.connect()

            # バックオフ: リトライ回数 n (1 始まり) に対して base^(n-1)
            # 今回は 3^(1-1)=1 秒、3^(2-1)=3 秒 となる
            mock_sleep.assert_any_call(1.0)  # 1回目のリトライ: 3^(1-1)=1
            mock_sleep.assert_any_call(3.0)  # 2回目のリトライ: 3^(2-1)=3

    # --- 認証エラーのテスト ---

    def test_connect_fails_on_login_error(self) -> None:
        """ログインエラー時に接続が失敗することを確認."""
        from services.importer.email_plugin import EmailAuthenticationError

        mock_imap = MagicMock()
        mock_imap.login.return_value = ("NO", [b"Invalid credentials"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)

            with pytest.raises(EmailAuthenticationError) as exc_info:
                plugin.connect()

            assert plugin.is_connected is False
            assert "GS-320" in str(exc_info.value)

    def test_connect_fails_on_folder_not_found(self) -> None:
        """フォルダが見つからない場合に接続が失敗することを確認."""
        from services.importer.email_plugin import EmailFolderError

        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("NO", [b"Folder not found"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config(folder="NonExistent")
            plugin = EmailPlugin(config)

            with pytest.raises(EmailFolderError) as exc_info:
                plugin.connect()

            assert plugin.is_connected is False
            assert "GS-321" in str(exc_info.value)

    # --- 切断のテスト ---

    def test_disconnect_success(self) -> None:
        """切断が成功することを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            plugin.disconnect()

            mock_imap.close.assert_called_once()
            mock_imap.logout.assert_called_once()
            assert plugin.is_connected is False

    def test_disconnect_when_not_connected(self) -> None:
        """未接続状態での切断が安全に行えることを確認."""
        config = self._create_valid_config()
        plugin = EmailPlugin(config)

        # エラーが発生しないことを確認
        plugin.disconnect()
        assert plugin.is_connected is False

    def test_disconnect_handles_connection_errors(self) -> None:
        """切断時のエラーが適切に処理されることを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.close.side_effect = Exception("Connection lost")

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            # エラーが発生しても切断処理が完了することを確認
            plugin.disconnect()
            assert plugin.is_connected is False

    # --- 接続状態の確認 ---

    def test_is_connected_initially_false(self) -> None:
        """初期状態では接続されていないことを確認."""
        config = self._create_valid_config()
        plugin = EmailPlugin(config)

        assert plugin.is_connected is False

    def test_double_connect_succeeds(self) -> None:
        """既に接続済みの場合、再接続が安全に行えることを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()
            plugin.connect()  # 再接続

            assert plugin.is_connected is True

    # --- タイムアウトのテスト ---

    def test_connect_uses_30_second_timeout(self) -> None:
        """接続時に30秒のタイムアウトが設定されることを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ) as mock_imap_class:
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            # タイムアウトが30秒に設定されていることを確認
            call_args = mock_imap_class.call_args
            assert call_args[1]["timeout"] == 30

    def test_connect_timeout_triggers_retry(self) -> None:
        """タイムアウト時にリトライが実行されることを確認."""
        mock_imap_success = MagicMock()
        mock_imap_success.login.return_value = ("OK", [b"Logged in"])
        mock_imap_success.select.return_value = ("OK", [b"1"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
        ) as mock_imap_class, patch("services.importer.email_plugin.time.sleep"):
            # 最初はタイムアウト、2回目で成功
            mock_imap_class.side_effect = [
                socket.timeout("Connection timed out"),
                mock_imap_success,
            ]

            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            assert mock_imap_class.call_count == 2
            assert plugin.is_connected is True


class TestEmailPluginFetch:
    """EmailPlugin.fetch()のテストスイート.

    Task 3.3: EmailPluginのメール取得・解析機能の実装
    - 指定フォルダからの未読メール取得の実装（fetch）
    - メール本文・件名・送信者情報の抽出
    - Message-IDをsource_idとして使用
    - RawImportDataへの変換処理
    - fetch_limit件数制限の適用
    - フォルダフィルタリング機能の実装
    - 取り込み進捗状況の記録

    Requirements: 2.2, 2.3, 2.4, 2.6
    """

    def _create_valid_config(self, **overrides) -> EmailPluginConfig:
        """テスト用の有効なConfigを作成."""
        defaults = {
            "imap_server": "imap.example.com",
            "username": "user@example.com",
            "password": "secret123",
        }
        defaults.update(overrides)
        return EmailPluginConfig(**defaults)

    def _create_mock_email(
        self,
        message_id: str = "<test@example.com>",
        subject: str = "テスト件名",
        from_addr: str = "sender@example.com",
        body: str = "テスト本文",
        date_str: str = "Sat, 11 Jan 2026 10:30:00 +0900",
    ) -> bytes:
        """テスト用のモックメールを作成."""
        email_content = f"""From: {from_addr}
Subject: {subject}
Date: {date_str}
Message-ID: {message_id}
Content-Type: text/plain; charset=utf-8

{body}"""
        return email_content.encode("utf-8")

    # --- 接続状態のチェック ---

    def test_fetch_raises_error_when_not_connected(self) -> None:
        """未接続状態でfetchを呼び出すとエラーが発生することを確認."""
        config = self._create_valid_config()
        plugin = EmailPlugin(config)

        with pytest.raises(RuntimeError) as exc_info:
            plugin.fetch()

        assert "接続されていません" in str(exc_info.value)

    # --- メール取得の成功ケース ---

    def test_fetch_returns_empty_list_when_no_emails(self) -> None:
        """未読メールがない場合に空のリストを返すことを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"0"])
        mock_imap.search.return_value = ("OK", [b""])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            result = plugin.fetch()

            assert result == []
            mock_imap.search.assert_called_once()

    def test_fetch_returns_raw_import_data_for_single_email(self) -> None:
        """1件のメールをRawImportDataに変換して返すことを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.search.return_value = ("OK", [b"1"])
        mock_imap.fetch.return_value = (
            "OK",
            [(b"1 (RFC822 {1234}", self._create_mock_email())],
        )

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            result = plugin.fetch()

            assert len(result) == 1
            assert result[0].source_id == "<test@example.com>"
            assert result[0].source_type == "email"
            assert result[0].subject == "テスト件名"
            assert result[0].sender == "sender@example.com"
            assert "テスト本文" in result[0].content

    def test_fetch_returns_multiple_emails(self) -> None:
        """複数のメールを取得できることを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"3"])
        mock_imap.search.return_value = ("OK", [b"1 2 3"])
        mock_imap.fetch.side_effect = [
            (
                "OK",
                [
                    (
                        b"1 (RFC822 {1234}",
                        self._create_mock_email(
                            message_id="<msg1@example.com>",
                            subject="件名1",
                        ),
                    )
                ],
            ),
            (
                "OK",
                [
                    (
                        b"2 (RFC822 {1234}",
                        self._create_mock_email(
                            message_id="<msg2@example.com>",
                            subject="件名2",
                        ),
                    )
                ],
            ),
            (
                "OK",
                [
                    (
                        b"3 (RFC822 {1234}",
                        self._create_mock_email(
                            message_id="<msg3@example.com>",
                            subject="件名3",
                        ),
                    )
                ],
            ),
        ]

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            result = plugin.fetch()

            assert len(result) == 3
            assert result[0].source_id == "<msg1@example.com>"
            assert result[1].source_id == "<msg2@example.com>"
            assert result[2].source_id == "<msg3@example.com>"

    # --- fetch_limit制限のテスト ---

    def test_fetch_respects_fetch_limit(self) -> None:
        """fetch_limitによる件数制限が適用され、最新メールから取得されることを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"10"])
        # 10件のメールIDを昇順で返す（IMAPの仕様通り、古い順）
        mock_imap.search.return_value = ("OK", [b"1 2 3 4 5 6 7 8 9 10"])
        # 最新5件（ID: 10, 9, 8, 7, 6）に対応するメールを返す
        mock_imap.fetch.side_effect = [
            (
                "OK",
                [
                    (
                        b"1 (RFC822 {1234}",
                        self._create_mock_email(
                            message_id=f"<msg{i}@example.com>",
                        ),
                    )
                ],
            )
            for i in [10, 9, 8, 7, 6]  # 最新から古い順
        ]

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config(fetch_limit=5)
            plugin = EmailPlugin(config)
            plugin.connect()

            result = plugin.fetch()

            assert len(result) == 5
            # fetchは5回だけ呼ばれる
            assert mock_imap.fetch.call_count == 5
            
            # 最新メールから取得されることを確認（ID: 10, 9, 8, 7, 6の順）
            expected_calls = [
                call("10", "(RFC822)"),
                call("9", "(RFC822)"),
                call("8", "(RFC822)"),
                call("7", "(RFC822)"),
                call("6", "(RFC822)"),
            ]
            mock_imap.fetch.assert_has_calls(expected_calls, any_order=False)

    # --- メールパースのテスト ---

    def test_fetch_parses_email_date_correctly(self) -> None:
        """メールの日付が正しくパースされることを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.search.return_value = ("OK", [b"1"])
        mock_imap.fetch.return_value = (
            "OK",
            [
                (
                    b"1 (RFC822 {1234}",
                    self._create_mock_email(date_str="Sat, 11 Jan 2026 10:30:00 +0900"),
                )
            ],
        )

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            result = plugin.fetch()

            assert len(result) == 1
            # メールヘッダーの日付（+0900）がUTCに変換されていることを確認
            # 2026-01-11 10:30:00 +0900 -> 2026-01-11 01:30:00 +0000
            assert result[0].received_at.year == 2026
            assert result[0].received_at.month == 1
            assert result[0].received_at.day == 11
            assert result[0].received_at.hour == 1
            assert result[0].received_at.minute == 30
            assert result[0].received_at.tzinfo == timezone.utc

    def test_fetch_handles_multipart_email(self) -> None:
        """マルチパートメールを正しく処理できることを確認."""
        multipart_email = """From: sender@example.com
Subject: =?utf-8?B?44OG44K544OI?=
Date: Sat, 11 Jan 2026 10:30:00 +0900
Message-ID: <multipart@example.com>
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset=utf-8

プレーンテキスト本文
--boundary123
Content-Type: text/html; charset=utf-8

<html><body>HTML本文</body></html>
--boundary123--""".encode(
            "utf-8"
        )

        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.search.return_value = ("OK", [b"1"])
        mock_imap.fetch.return_value = ("OK", [(b"1 (RFC822 {1234}", multipart_email)])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            result = plugin.fetch()

            assert len(result) == 1
            # プレーンテキスト部分が優先して抽出される
            assert "プレーンテキスト本文" in result[0].content

    def test_fetch_handles_encoded_subject(self) -> None:
        """エンコードされた件名を正しくデコードできることを確認."""
        encoded_email = """From: sender@example.com
Subject: =?utf-8?B?44OG44K544OI5Lu25ZCN?=
Date: Sat, 11 Jan 2026 10:30:00 +0900
Message-ID: <encoded@example.com>
Content-Type: text/plain; charset=utf-8

本文""".encode(
            "utf-8"
        )

        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.search.return_value = ("OK", [b"1"])
        mock_imap.fetch.return_value = ("OK", [(b"1 (RFC822 {1234}", encoded_email)])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            result = plugin.fetch()

            assert len(result) == 1
            assert result[0].subject == "テスト件名"

    # --- メタデータのテスト ---

    def test_fetch_includes_raw_metadata(self) -> None:
        """raw_metadataにメールヘッダー情報が含まれることを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.search.return_value = ("OK", [b"1"])
        mock_imap.fetch.return_value = (
            "OK",
            [(b"1 (RFC822 {1234}", self._create_mock_email())],
        )

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            result = plugin.fetch()

            assert len(result) == 1
            assert "imap_uid" in result[0].raw_metadata
            assert "folder" in result[0].raw_metadata
            assert result[0].raw_metadata["folder"] == "INBOX"

    # --- エラーハンドリングのテスト ---

    def test_fetch_handles_search_error(self) -> None:
        """検索エラー時に適切なエラーが発生することを確認."""
        from services.importer.email_plugin import EmailPluginError

        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.search.return_value = ("NO", [b"Search failed"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            with pytest.raises(EmailPluginError) as exc_info:
                plugin.fetch()

            assert "GS-306" in str(exc_info.value)

    def test_fetch_handles_individual_fetch_error(self) -> None:
        """個別メール取得エラー時にスキップして他のメールを処理することを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"2"])
        mock_imap.search.return_value = ("OK", [b"1 2"])
        # 1件目はエラー、2件目は成功
        mock_imap.fetch.side_effect = [
            ("NO", [b"Fetch failed"]),
            (
                "OK",
                [
                    (
                        b"2 (RFC822 {1234}",
                        self._create_mock_email(
                            message_id="<msg2@example.com>",
                        ),
                    )
                ],
            ),
        ]

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            result = plugin.fetch()

            # エラーのメールをスキップして、成功したメールのみ返す
            assert len(result) == 1
            assert result[0].source_id == "<msg2@example.com>"

    def test_fetch_handles_missing_message_id(self) -> None:
        """Message-IDがないメールを適切に処理することを確認."""
        email_without_id = """From: sender@example.com
Subject: No Message-ID
Date: Sat, 11 Jan 2026 10:30:00 +0900
Content-Type: text/plain; charset=utf-8

本文""".encode(
            "utf-8"
        )

        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.search.return_value = ("OK", [b"1"])
        mock_imap.fetch.return_value = ("OK", [(b"1 (RFC822 {1234}", email_without_id)])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            result = plugin.fetch()

            assert len(result) == 1
            # Message-IDがない場合はUIDベースのIDを生成
            assert result[0].source_id.startswith("email-uid-")


class TestEmailPluginMarkAsProcessed:
    """EmailPlugin.mark_as_processed()のテストスイート.

    Task 3.3: メール既読マーク処理の実装
    - メールを既読にマーク（\\Seen フラグ設定）

    Requirements: 2.6 (重複取り込み防止)
    """

    def _create_valid_config(self, **overrides) -> EmailPluginConfig:
        """テスト用の有効なConfigを作成."""
        defaults = {
            "imap_server": "imap.example.com",
            "username": "user@example.com",
            "password": "secret123",
        }
        defaults.update(overrides)
        return EmailPluginConfig(**defaults)

    def test_mark_as_processed_raises_error_when_not_connected(self) -> None:
        """未接続状態でmark_as_processedを呼び出すとエラーが発生することを確認."""
        config = self._create_valid_config()
        plugin = EmailPlugin(config)

        with pytest.raises(RuntimeError) as exc_info:
            plugin.mark_as_processed("<test@example.com>")

        assert "接続されていません" in str(exc_info.value)

    def test_mark_as_processed_sets_seen_flag(self) -> None:
        """mark_as_processedがSEENフラグを設定することを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.search.return_value = ("OK", [b"1"])
        mock_imap.store.return_value = ("OK", [b"1 (FLAGS (\\Seen))"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            plugin.mark_as_processed("<test@example.com>")

            # SEARCHでMessage-IDを検索してUIDを取得
            mock_imap.search.assert_called()
            # STOREで\\Seenフラグを設定
            mock_imap.store.assert_called()
            call_args = mock_imap.store.call_args
            assert "\\Seen" in str(call_args)

    def test_mark_as_processed_handles_not_found(self) -> None:
        """存在しないメールIDを処理できることを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        # メールが見つからない
        mock_imap.search.return_value = ("OK", [b""])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            # エラーが発生しないことを確認（警告ログは出力されるが例外は発生しない）
            plugin.mark_as_processed("<nonexistent@example.com>")

            # storeは呼ばれない
            mock_imap.store.assert_not_called()

    def test_mark_as_processed_with_uid_based_id(self) -> None:
        """UID形式のIDを処理できることを確認."""
        mock_imap = MagicMock()
        mock_imap.login.return_value = ("OK", [b"Logged in"])
        mock_imap.select.return_value = ("OK", [b"1"])
        mock_imap.store.return_value = ("OK", [b"1 (FLAGS (\\Seen))"])

        with patch(
            "services.importer.email_plugin.imaplib.IMAP4_SSL",
            return_value=mock_imap,
        ):
            config = self._create_valid_config()
            plugin = EmailPlugin(config)
            plugin.connect()

            # UID形式のID（Message-IDがない場合に生成されるID）
            plugin.mark_as_processed("email-uid-1")

            # UIDを直接使用してSTOREを呼び出す
            mock_imap.store.assert_called_once_with("1", "+FLAGS", "\\Seen")

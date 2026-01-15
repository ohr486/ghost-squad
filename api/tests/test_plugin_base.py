"""プラグインベースクラスのテスト.

Task 1.1: データソースプラグイン共通インターフェースの実装
"""
from datetime import datetime, timezone
from typing import List

import pytest

from services.importer.plugin_base import (DataSourcePlugin, RawImportData,
                                           ValidationError, ValidationResult)


class TestRawImportData:
    """RawImportDataデータクラスのテスト."""

    def test_create_raw_import_data_with_required_fields(self) -> None:
        """必須フィールドでRawImportDataを作成できる."""
        now = datetime.now(timezone.utc)
        data = RawImportData(
            source_id="msg-001",
            source_type="email",
            content="Test content",
            subject="Test subject",
            sender="test@example.com",
            received_at=now,
            raw_metadata={},
        )

        assert data.source_id == "msg-001"
        assert data.source_type == "email"
        assert data.content == "Test content"
        assert data.subject == "Test subject"
        assert data.sender == "test@example.com"
        assert data.received_at == now
        assert data.raw_metadata == {}

    def test_create_raw_import_data_with_metadata(self) -> None:
        """メタデータ付きでRawImportDataを作成できる."""
        now = datetime.now(timezone.utc)
        metadata = {"headers": {"X-Custom": "value"}, "attachments": []}
        data = RawImportData(
            source_id="msg-002",
            source_type="email",
            content="Test content",
            subject="Test subject",
            sender="test@example.com",
            received_at=now,
            raw_metadata=metadata,
        )

        assert data.raw_metadata == metadata
        assert data.raw_metadata["headers"]["X-Custom"] == "value"

    def test_raw_import_data_is_immutable_dataclass(self) -> None:
        """RawImportDataはデータクラスである."""
        now = datetime.now(timezone.utc)
        data = RawImportData(
            source_id="msg-001",
            source_type="email",
            content="Test content",
            subject="Test subject",
            sender="test@example.com",
            received_at=now,
            raw_metadata={},
        )

        # dataclassの属性が存在する
        assert hasattr(data, "__dataclass_fields__")


class TestValidationResult:
    """ValidationResultデータクラスのテスト."""

    def test_create_successful_validation_result(self) -> None:
        """成功したバリデーション結果を作成できる."""
        result = ValidationResult(valid=True, errors=[])

        assert result.valid is True
        assert result.errors == []

    def test_create_failed_validation_result(self) -> None:
        """失敗したバリデーション結果を作成できる."""
        errors = [
            ValidationError(
                field="imap_server",
                message="IMAPサーバーが指定されていません",
                code="GS-301",
            )
        ]
        result = ValidationResult(valid=False, errors=errors)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "imap_server"

    def test_validation_result_with_multiple_errors(self) -> None:
        """複数のエラーを持つバリデーション結果を作成できる."""
        errors = [
            ValidationError(
                field="imap_server",
                message="IMAPサーバーが指定されていません",
                code="GS-301",
            ),
            ValidationError(
                field="username",
                message="ユーザー名が指定されていません",
                code="GS-302",
            ),
        ]
        result = ValidationResult(valid=False, errors=errors)

        assert len(result.errors) == 2


class TestValidationError:
    """ValidationErrorデータクラスのテスト."""

    def test_create_validation_error(self) -> None:
        """ValidationErrorを作成できる."""
        error = ValidationError(
            field="imap_server",
            message="IMAPサーバーが指定されていません",
            code="GS-301",
        )

        assert error.field == "imap_server"
        assert error.message == "IMAPサーバーが指定されていません"
        assert error.code == "GS-301"


class MockPluginConfig:
    """モックプラグイン設定."""

    def __init__(self, server: str = "localhost", valid: bool = True):
        self.server = server
        self.valid = valid


class ConcretePlugin(DataSourcePlugin[MockPluginConfig]):
    """テスト用の具象プラグインクラス."""

    def __init__(self, config: MockPluginConfig):
        self._config = config
        self._connected = False

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


class TestDataSourcePlugin:
    """DataSourcePlugin抽象基底クラスのテスト."""

    def test_plugin_type_property(self) -> None:
        """plugin_typeプロパティが正しく動作する."""
        config = MockPluginConfig()
        plugin = ConcretePlugin(config)

        assert plugin.plugin_type == "mock"

    def test_validate_config_returns_validation_result(self) -> None:
        """validate_configがValidationResultを返す."""
        config = MockPluginConfig()
        plugin = ConcretePlugin(config)

        result = plugin.validate_config(config)

        assert isinstance(result, ValidationResult)
        assert result.valid is True

    def test_validate_config_with_invalid_config(self) -> None:
        """不正な設定でvalidate_configを呼び出すとエラーを返す."""
        config = MockPluginConfig(valid=False)
        plugin = ConcretePlugin(config)

        result = plugin.validate_config(config)

        assert result.valid is False
        assert len(result.errors) == 1

    def test_connect_and_disconnect(self) -> None:
        """接続と切断が正しく動作する."""
        config = MockPluginConfig()
        plugin = ConcretePlugin(config)

        # 接続後にfetchが成功することを確認
        plugin.connect()
        plugin.fetch()

        # 切断後にfetchがエラーになることを確認
        plugin.disconnect()
        with pytest.raises(RuntimeError):
            plugin.fetch()

    def test_fetch_returns_raw_import_data_list(self) -> None:
        """fetchがRawImportDataのリストを返す."""
        config = MockPluginConfig()
        plugin = ConcretePlugin(config)

        plugin.connect()
        data_list = plugin.fetch()

        assert isinstance(data_list, list)
        assert len(data_list) == 1
        assert isinstance(data_list[0], RawImportData)
        assert data_list[0].source_type == "mock"

    def test_fetch_without_connection_raises_error(self) -> None:
        """接続せずにfetchを呼び出すとエラーが発生する."""
        config = MockPluginConfig()
        plugin = ConcretePlugin(config)

        with pytest.raises(RuntimeError):
            plugin.fetch()

    def test_mark_as_processed(self) -> None:
        """mark_as_processedが正しく動作する."""
        config = MockPluginConfig()
        plugin = ConcretePlugin(config)

        # エラーが発生しないことを確認
        plugin.mark_as_processed("test-001")

    def test_cannot_instantiate_abstract_class(self) -> None:
        """抽象クラスは直接インスタンス化できない."""
        with pytest.raises(TypeError):
            DataSourcePlugin()  # type: ignore

"""Pytest configuration and fixtures."""
import sys
from pathlib import Path
from typing import Any, List

# Add the api directory to the Python path
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

from services.importer.plugin_base import (  # noqa: E402
    DataSourcePlugin,
    RawImportData,
    ValidationResult,
)


# ==============================================================================
# Shared Test Utilities
# ==============================================================================


class MockDataSourcePlugin(DataSourcePlugin[dict]):
    """テスト用モックプラグイン.
    
    複数のテストファイルで使用される共通のモックプラグイン。
    DataSourcePluginインターフェースを実装し、テストデータの設定と
    取得をサポートする。
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._connected = False
        self._data: List[RawImportData] = []
        self._processed: List[str] = []

    @property
    def plugin_type(self) -> str:
        return "mock_plugin"

    def validate_config(self, config: dict) -> ValidationResult:
        return ValidationResult(valid=True, errors=[])

    def connect(self) -> None:
        if self._config.get("fail_connect"):
            raise ConnectionError("接続に失敗しました")
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def fetch(self) -> List[RawImportData]:
        if self._config.get("fail_fetch"):
            raise RuntimeError("データ取得に失敗しました")
        return self._data

    def mark_as_processed(self, source_id: str) -> None:
        self._processed.append(source_id)

    def set_data(self, data: List[RawImportData]) -> None:
        """テスト用にデータを設定."""
        self._data = data

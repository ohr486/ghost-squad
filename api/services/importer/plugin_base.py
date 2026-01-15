"""データソースプラグイン基盤モジュール.

Task 1.1: データソースプラグイン共通インターフェースの実装
- RawImportDataデータクラスの定義
- DataSourcePlugin抽象基底クラスの定義
- ValidationResultデータクラスの定義
- ValidationErrorデータクラスの定義

Requirements: 1.4 (共通インターフェース)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Generic, List, TypeVar

# 設定型のジェネリック型パラメータ
TConfig = TypeVar("TConfig")


@dataclass
class ValidationError:
    """バリデーションエラー情報.

    Attributes:
        field: エラーが発生したフィールド名
        message: エラーメッセージ（日本語）
        code: エラーコード（GS-3xx形式）
    """

    field: str
    message: str
    code: str


@dataclass
class ValidationResult:
    """バリデーション結果.

    Attributes:
        valid: バリデーション成功フラグ
        errors: バリデーションエラーのリスト
    """

    valid: bool
    errors: List[ValidationError]


@dataclass
class RawImportData:
    """プラグインから取得した生データ.

    外部システムから取得したデータを標準化された形式で保持する。

    Attributes:
        source_id: 外部システムのID（Message-ID等）
        source_type: データソース種別（email, sentry等）
        content: 本文
        subject: 件名/タイトル
        sender: 送信者
        received_at: 受信日時
        raw_metadata: 追加メタデータ（ヘッダー、添付ファイル情報等）
    """

    source_id: str
    source_type: str
    content: str
    subject: str
    sender: str
    received_at: datetime
    raw_metadata: Dict[str, Any]


class DataSourcePlugin(ABC, Generic[TConfig]):
    """データソースプラグインの抽象基底クラス.

    すべてのデータソースプラグイン（Email, Sentry等）はこのクラスを継承し、
    共通インターフェースを実装する。

    型パラメータ:
        TConfig: プラグイン固有の設定クラス

    使用例:
        ```python
        class EmailPlugin(DataSourcePlugin[EmailPluginConfig]):
            @property
            def plugin_type(self) -> str:
                return "email"

            def validate_config(self, config: EmailPluginConfig) -> ValidationResult:
                # 設定検証ロジック
                pass

            # ... 他のメソッド実装
        ```

    契約:
        - Preconditions: validate_config()が成功していること
        - Postconditions: fetch()は重複しないRawImportDataのリストを返す
        - Invariants: source_idは外部システム内で一意
    """

    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """プラグイン種別を返す.

        Returns:
            str: プラグイン種別（例: 'email', 'sentry'）
        """
        ...

    @abstractmethod
    def validate_config(self, config: TConfig) -> ValidationResult:
        """設定情報を検証する.

        Args:
            config: プラグイン固有の設定

        Returns:
            ValidationResult: バリデーション結果
        """
        ...

    @abstractmethod
    def connect(self) -> None:
        """データソースに接続する.

        Raises:
            ConnectionError: 接続に失敗した場合
        """
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """データソースから切断する."""
        ...

    @abstractmethod
    def fetch(self) -> List[RawImportData]:
        """データを取得する.

        Returns:
            List[RawImportData]: 取得したデータのリスト

        Raises:
            RuntimeError: 接続されていない場合
        """
        ...

    @abstractmethod
    def mark_as_processed(self, source_id: str) -> None:
        """処理済みとしてマークする.

        Args:
            source_id: 処理済みとしてマークするデータのソースID
        """
        ...

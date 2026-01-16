"""メールプラグインモジュール.

Task 3.1: EmailPluginConfigと設定検証の実装
- EmailPluginConfigデータクラスの定義（imap_server、imap_port、username、password、
  folder、use_ssl、fetch_limit、retry_max、retry_backoff_base）
- 設定検証ロジックの実装（必須フィールド、ポート範囲、フォルダ名形式）

Requirements: 2.1, 2.3 (IMAP/POP3接続、フォルダフィルタリング)
"""
import re
from dataclasses import dataclass
from typing import List

from services.importer.plugin_base import (DataSourcePlugin, RawImportData,
                                           ValidationError, ValidationResult)


@dataclass(frozen=True)
class EmailPluginConfig:
    """メールプラグイン設定.

    IMAPプロトコルによるメールサーバー接続の設定を保持する。

    Attributes:
        imap_server: IMAPサーバーホスト名
        imap_port: IMAPサーバーポート（デフォルト: 993）
        username: メールアカウントのユーザー名
        password: メールアカウントのパスワード
        folder: 取り込み対象フォルダ（デフォルト: INBOX）
        use_ssl: SSL/TLS接続を使用するか（デフォルト: True）
        fetch_limit: 一度に取得するメールの最大件数（デフォルト: 50）
        retry_max: 最大リトライ回数（デフォルト: 3）
        retry_backoff_base: リトライ指数バックオフの基数（デフォルト: 2.0）

    契約:
        - imap_serverは空でないこと
        - imap_portは1〜65535の範囲
        - usernameは空でないこと
        - passwordは空でないこと（機密情報、ログに出力しない）
        - folderは有効なIMAPフォルダ名形式
        - fetch_limitは1〜1000の範囲
        - retry_maxは0以上
        - retry_backoff_baseは0より大きいこと
    """

    imap_server: str
    username: str
    password: str
    imap_port: int = 993
    folder: str = "INBOX"
    use_ssl: bool = True
    fetch_limit: int = 50
    retry_max: int = 3
    retry_backoff_base: float = 2.0


class EmailPluginConfigValidator:
    """EmailPluginConfig用のバリデーター.

    設定値の検証ロジックを提供する。
    """

    # 有効なポート範囲
    MIN_PORT = 1
    MAX_PORT = 65535

    # IMAPフォルダ名の正規表現パターン
    # - 英数字、日本語、スペース、ハイフン、アンダースコア、ドット、スラッシュを許可
    # - 空文字は不可
    FOLDER_PATTERN = re.compile(
        r"^[\w\s\-_.\/\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+$"
    )

    # フェッチ上限の制約
    MIN_FETCH_LIMIT = 1
    MAX_FETCH_LIMIT = 1000

    @classmethod
    def validate(cls, config: EmailPluginConfig) -> ValidationResult:
        """設定情報を検証する.

        Args:
            config: 検証対象の設定

        Returns:
            ValidationResult: バリデーション結果
        """
        errors: List[ValidationError] = []

        # imap_server検証
        if not config.imap_server or not config.imap_server.strip():
            errors.append(
                ValidationError(
                    field="imap_server",
                    message="IMAPサーバーは必須です",
                    code="GS-310",
                )
            )

        # imap_port検証
        if not cls.MIN_PORT <= config.imap_port <= cls.MAX_PORT:
            errors.append(
                ValidationError(
                    field="imap_port",
                    message=f"ポート番号は{cls.MIN_PORT}〜{cls.MAX_PORT}の範囲で指定してください",
                    code="GS-311",
                )
            )

        # username検証
        if not config.username or not config.username.strip():
            errors.append(
                ValidationError(
                    field="username",
                    message="ユーザー名は必須です",
                    code="GS-312",
                )
            )

        # password検証
        if not config.password:
            errors.append(
                ValidationError(
                    field="password",
                    message="パスワードは必須です",
                    code="GS-313",
                )
            )

        # folder検証
        if not config.folder or not config.folder.strip():
            errors.append(
                ValidationError(
                    field="folder",
                    message="フォルダ名は必須です",
                    code="GS-314",
                )
            )
        elif not cls.FOLDER_PATTERN.match(config.folder):
            errors.append(
                ValidationError(
                    field="folder",
                    message="フォルダ名に無効な文字が含まれています",
                    code="GS-315",
                )
            )

        # fetch_limit検証
        if config.fetch_limit < cls.MIN_FETCH_LIMIT:
            errors.append(
                ValidationError(
                    field="fetch_limit",
                    message=f"取得上限は{cls.MIN_FETCH_LIMIT}以上で指定してください",
                    code="GS-316",
                )
            )
        elif config.fetch_limit > cls.MAX_FETCH_LIMIT:
            errors.append(
                ValidationError(
                    field="fetch_limit",
                    message=f"取得上限は{cls.MAX_FETCH_LIMIT}以下で指定してください",
                    code="GS-317",
                )
            )

        # retry_max検証
        if config.retry_max < 0:
            errors.append(
                ValidationError(
                    field="retry_max",
                    message="リトライ回数は0以上で指定してください",
                    code="GS-318",
                )
            )

        # retry_backoff_base検証
        if config.retry_backoff_base <= 0:
            errors.append(
                ValidationError(
                    field="retry_backoff_base",
                    message="リトライバックオフ基数は0より大きい値を指定してください",
                    code="GS-319",
                )
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)


class EmailPlugin(DataSourcePlugin[EmailPluginConfig]):
    """メールデータソースプラグイン.

    IMAPプロトコルによるメールサーバーからのデータ取り込みを提供する。

    Attributes:
        _config: プラグイン設定
        _connection: IMAPサーバー接続（未接続時はNone）

    契約:
        - Preconditions: 有効なIMAP接続設定
        - Postconditions: fetch()は最大fetch_limit件のメールを返す
        - Invariants: Message-IDはsource_idとして使用
    """

    def __init__(self, config: EmailPluginConfig) -> None:
        """EmailPluginを初期化.

        Args:
            config: プラグイン設定
        """
        self._config = config
        self._connection = None  # Task 3.2で実装

    @property
    def plugin_type(self) -> str:
        """プラグイン種別を返す.

        Returns:
            str: "email"
        """
        return "email"

    @property
    def config(self) -> EmailPluginConfig:
        """設定を取得する.

        Returns:
            EmailPluginConfig: プラグイン設定
        """
        return self._config

    def validate_config(self, config: EmailPluginConfig) -> ValidationResult:
        """設定情報を検証する.

        Args:
            config: プラグイン設定

        Returns:
            ValidationResult: バリデーション結果
        """
        return EmailPluginConfigValidator.validate(config)

    def connect(self) -> None:
        """IMAPサーバーに接続する.

        Raises:
            ConnectionError: 接続に失敗した場合

        Note:
            Task 3.2で実装予定
        """
        raise NotImplementedError("Task 3.2で実装予定")

    def disconnect(self) -> None:
        """IMAP接続を切断する.

        Note:
            Task 3.2で実装予定
        """
        raise NotImplementedError("Task 3.2で実装予定")

    def fetch(self) -> List[RawImportData]:
        """未読メールを取得する.

        Returns:
            List[RawImportData]: 取得したメールデータのリスト

        Raises:
            RuntimeError: 接続されていない場合

        Note:
            Task 3.3で実装予定
        """
        raise NotImplementedError("Task 3.3で実装予定")

    def mark_as_processed(self, source_id: str) -> None:
        """メールを既読にマークする.

        Args:
            source_id: メールのMessage-ID

        Note:
            Task 3.3で実装予定
        """
        raise NotImplementedError("Task 3.3で実装予定")

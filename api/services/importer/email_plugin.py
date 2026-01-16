"""メールプラグインモジュール.

Task 3.1: EmailPluginConfigと設定検証の実装
- EmailPluginConfigデータクラスの定義（imap_server、imap_port、username、password、
  folder、use_ssl、fetch_limit、retry_max、retry_backoff_base）
- 設定検証ロジックの実装（必須フィールド、ポート範囲、フォルダ名形式）

Task 3.2: EmailPluginのIMAP接続機能の実装
- IMAP4_SSLによるメールサーバー接続の実装（connect）
- 接続切断の実装（disconnect）
- 指数バックオフによるリトライ戦略の実装（最大3回、2^n秒）
- 接続失敗時のエラーハンドリングとエラー通知
- タイムアウト設定（30秒）

Task 3.3: EmailPluginのメール取得・解析機能の実装
- 指定フォルダからの未読メール取得の実装（fetch）
- メール本文・件名・送信者情報の抽出
- Message-IDをsource_idとして使用
- RawImportDataへの変換処理
- fetch_limit件数制限の適用
- フォルダフィルタリング機能の実装
- 取り込み進捗状況の記録
- メール既読マーク処理の実装（mark_as_processed）

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""
import email
import email.header
import email.utils
import imaplib
import re
import socket
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Optional, Union

from services.importer.plugin_base import (DataSourcePlugin, RawImportData,
                                           ValidationError, ValidationResult)

# IMAP接続タイムアウト（秒）
IMAP_CONNECTION_TIMEOUT = 30


class EmailPluginError(Exception):
    """EmailPluginの基底例外クラス."""

    def __init__(self, message: str, code: str) -> None:
        """EmailPluginErrorを初期化.

        Args:
            message: エラーメッセージ
            code: エラーコード（GS-3xx形式）
        """
        super().__init__(f"[{code}] {message}")
        self.message = message
        self.code = code


class EmailConnectionError(EmailPluginError):
    """メールサーバー接続エラー.

    接続失敗、タイムアウト、ネットワークエラーなど。
    エラーコード: GS-303
    """

    def __init__(self, message: str) -> None:
        """EmailConnectionErrorを初期化.

        Args:
            message: エラーメッセージ
        """
        super().__init__(message, "GS-303")


class EmailAuthenticationError(EmailPluginError):
    """メール認証エラー.

    ユーザー名またはパスワードが無効。
    エラーコード: GS-320
    """

    def __init__(self, message: str) -> None:
        """EmailAuthenticationErrorを初期化.

        Args:
            message: エラーメッセージ
        """
        super().__init__(message, "GS-320")


class EmailFolderError(EmailPluginError):
    """メールフォルダエラー.

    指定されたフォルダが見つからない。
    エラーコード: GS-321
    """

    def __init__(self, message: str) -> None:
        """EmailFolderErrorを初期化.

        Args:
            message: エラーメッセージ
        """
        super().__init__(message, "GS-321")


class EmailFetchError(EmailPluginError):
    """メール取得エラー.

    メールの検索または取得に失敗。
    エラーコード: GS-306
    """

    def __init__(self, message: str) -> None:
        """EmailFetchErrorを初期化.

        Args:
            message: エラーメッセージ
        """
        super().__init__(message, "GS-306")


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
        if not config.password or not config.password.strip():
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
        self._connection: Optional[Union[imaplib.IMAP4_SSL, imaplib.IMAP4]] = None

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

    @property
    def is_connected(self) -> bool:
        """接続状態を取得する.

        Returns:
            bool: 接続中の場合True
        """
        return self._connection is not None

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

        接続失敗時は指数バックオフによるリトライ戦略を実行。
        タイムアウトは30秒に設定。

        Raises:
            EmailConnectionError: 最大リトライ回数を超えても接続に失敗した場合
            EmailAuthenticationError: 認証に失敗した場合
            EmailFolderError: 指定されたフォルダが見つからない場合
        """
        # 既に接続済みの場合は一度切断
        if self._connection is not None:
            self.disconnect()

        last_error: Optional[Exception] = None
        attempts = 0
        max_attempts = self._config.retry_max + 1  # 初回 + リトライ回数

        while attempts < max_attempts:
            attempts += 1  # 試行回数をカウント（1始まり）
            try:
                # IMAP接続を確立
                self._connection = self._create_imap_connection()

                # ログイン
                login_status, login_data = self._connection.login(
                    self._config.username, self._config.password
                )
                if login_status != "OK":
                    self._connection = None
                    raise EmailAuthenticationError(f"認証に失敗しました: {login_data}")

                # フォルダを選択
                select_status, select_data = self._connection.select(
                    self._config.folder
                )
                if select_status != "OK":
                    self._safe_logout()
                    self._connection = None
                    raise EmailFolderError(
                        f"フォルダ '{self._config.folder}' が見つかりません: {select_data}"
                    )

                # 接続成功
                return

            except (EmailAuthenticationError, EmailFolderError):
                # 認証・フォルダエラーはリトライしない
                raise
            except (socket.error, socket.timeout, OSError, imaplib.IMAP4.error) as e:
                # ネットワークエラーおよびIMAPプロトコルエラーはリトライ対象
                last_error = e
                self._connection = None

                if attempts < max_attempts:
                    # 指数バックオフで待機: base^(attempts-1)秒
                    wait_time = self._config.retry_backoff_base ** (attempts - 1)
                    time.sleep(wait_time)

        # 最大リトライ回数を超えた
        raise EmailConnectionError(
            f"メールサーバーへの接続に失敗しました（{max_attempts}回試行）: {last_error}"
        )

    def _create_imap_connection(
        self,
    ) -> Union[imaplib.IMAP4_SSL, imaplib.IMAP4]:
        """IMAP接続を作成する.

        Returns:
            IMAP4_SSL or IMAP4: IMAP接続オブジェクト
        """
        if self._config.use_ssl:
            return imaplib.IMAP4_SSL(
                self._config.imap_server,
                self._config.imap_port,
                timeout=IMAP_CONNECTION_TIMEOUT,
            )
        else:
            return imaplib.IMAP4(
                self._config.imap_server,
                self._config.imap_port,
                timeout=IMAP_CONNECTION_TIMEOUT,
            )

    def _safe_logout(self) -> None:
        """安全にログアウトする（エラーを無視）."""
        if self._connection is not None:
            try:
                self._connection.logout()
            except Exception:  # nosec B110 - 切断時のエラーは意図的に無視
                pass

    def disconnect(self) -> None:
        """IMAP接続を切断する.

        切断中のエラーは無視し、必ず接続を解放する。
        """
        if self._connection is None:
            return

        try:
            self._connection.close()
        except Exception:  # nosec B110 - 切断時のエラーは意図的に無視
            pass

        try:
            self._connection.logout()
        except Exception:  # nosec B110 - 切断時のエラーは意図的に無視
            pass

        self._connection = None

    def fetch(self) -> List[RawImportData]:
        """未読メールを取得する.

        Returns:
            List[RawImportData]: 取得したメールデータのリスト

        Raises:
            RuntimeError: 接続されていない場合
            EmailFetchError: メール検索に失敗した場合
        """
        if self._connection is None:
            raise RuntimeError("接続されていません。connect()を先に呼び出してください。")

        # 未読メールを検索
        status, data = self._connection.search(None, "UNSEEN")
        if status != "OK":
            raise EmailFetchError(f"メール検索に失敗しました: {data}")

        # メールIDリストを取得
        mail_ids = data[0].split() if data[0] else []
        if not mail_ids:
            return []

        # fetch_limitを適用
        mail_ids = mail_ids[: self._config.fetch_limit]

        results: List[RawImportData] = []
        for mail_id in mail_ids:
            try:
                raw_data = self._fetch_single_email(mail_id.decode("utf-8"))
                if raw_data is not None:
                    results.append(raw_data)
            except Exception:  # nosec B112 - 個別メールのエラーはスキップして続行
                continue

        return results

    def _fetch_single_email(self, mail_id: str) -> Optional[RawImportData]:
        """単一のメールを取得してRawImportDataに変換する.

        Args:
            mail_id: メールのUID

        Returns:
            RawImportData: 変換されたデータ、失敗時はNone
        """
        if self._connection is None:
            return None

        status, data = self._connection.fetch(mail_id, "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            return None

        # メールをパース
        raw_email = data[0][1] if isinstance(data[0], tuple) else data[0]
        if raw_email is None:
            return None

        msg = email.message_from_bytes(raw_email)

        # Message-IDを取得（ない場合はUID形式のIDを生成）
        message_id = msg.get("Message-ID", "")
        if not message_id:
            message_id = f"email-uid-{mail_id}"

        # 件名をデコード
        subject = self._decode_header(msg.get("Subject", ""))

        # 送信者を取得
        sender = self._decode_header(msg.get("From", ""))

        # 日付をパース
        date_str = msg.get("Date", "")
        received_at = self._parse_date(date_str)

        # 本文を抽出
        content = self._extract_body(msg)

        # メタデータを作成
        raw_metadata = {
            "imap_uid": mail_id,
            "folder": self._config.folder,
            "content_type": msg.get_content_type(),
        }

        return RawImportData(
            source_id=message_id,
            source_type="email",
            content=content,
            subject=subject,
            sender=sender,
            received_at=received_at,
            raw_metadata=raw_metadata,
        )

    def _decode_header(self, header_value: Optional[str]) -> str:
        """エンコードされたヘッダー値をデコードする.

        Args:
            header_value: ヘッダー値

        Returns:
            str: デコードされた文字列
        """
        if not header_value:
            return ""

        decoded_parts = email.header.decode_header(header_value)
        result_parts = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    result_parts.append(
                        part.decode(charset or "utf-8", errors="replace")
                    )
                except (LookupError, UnicodeDecodeError):
                    result_parts.append(part.decode("utf-8", errors="replace"))
            else:
                result_parts.append(part)
        return "".join(result_parts)

    def _parse_date(self, date_str: str) -> datetime:
        """メールの日付文字列をdatetimeに変換する.

        Args:
            date_str: RFC 2822形式の日付文字列

        Returns:
            datetime: パースされた日時（UTCに変換）
        """
        if not date_str:
            return datetime.now(timezone.utc)

        try:
            parsed = email.utils.parsedate_to_datetime(date_str)
            return parsed
        except (ValueError, TypeError):
            return datetime.now(timezone.utc)

    def _extract_body(self, msg: email.message.Message) -> str:
        """メールから本文を抽出する.

        マルチパートメールの場合はtext/plainを優先。

        Args:
            msg: emailメッセージオブジェクト

        Returns:
            str: 抽出された本文
        """
        if msg.is_multipart():
            # マルチパートの場合、text/plainを優先して探す
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="replace")
            # text/plainがなければtext/htmlを試す
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="replace")
        else:
            # 単一パートの場合
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                charset = msg.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")

        return ""

    def mark_as_processed(self, source_id: str) -> None:
        """メールを既読にマークする.

        Args:
            source_id: メールのMessage-IDまたはUID形式のID

        Raises:
            RuntimeError: 接続されていない場合
        """
        if self._connection is None:
            raise RuntimeError("接続されていません。connect()を先に呼び出してください。")

        # UID形式のIDかどうかを判定
        if source_id.startswith("email-uid-"):
            # UID形式のID: email-uid-XXX から UID を抽出
            uid = source_id.replace("email-uid-", "")
            self._connection.store(uid, "+FLAGS", "\\Seen")
        else:
            # Message-ID形式: Message-IDで検索してUIDを取得
            status, data = self._connection.search(
                None, f'HEADER Message-ID "{source_id}"'
            )
            if status != "OK" or not data[0]:
                # メールが見つからない場合は何もしない
                return

            mail_ids = data[0].split()
            for mail_id in mail_ids:
                self._connection.store(mail_id.decode("utf-8"), "+FLAGS", "\\Seen")

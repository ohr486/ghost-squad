"""ImporterServiceモジュール.

Task 9.1, 9.2, 9.3, 9.4: ImporterServiceの実装
- ImporterMetadata, ImportResult, ImportErrorのデータクラス
- インポート実行機能
- エラーハンドリング機能
- リトライ機能

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.enums.inquiry_status import InquiryStatus
from services.importer.ai_provider_base import AIProviderType
from services.importer.analysis_service import ImporterAnalysisService
from services.importer.import_error_log_repository import (
    CreateErrorLogData, ErrorStats, ImportErrorLogRepository)
from services.importer.plugin_base import RawImportData
from services.importer.plugin_registry import PluginRegistryService
from services.importer.result import BaseError, Result
from services.inquiry_repository import CreateInquiryData, InquiryRepository

# ロガー設定
logger = logging.getLogger(__name__)

# 連続エラー検出閾値
CONSECUTIVE_ERROR_THRESHOLD = 5


@dataclass
class ImporterMetadata:
    """インポート元メタデータ（inquiry_metadataに格納）.

    Task 9.1で定義。

    Attributes:
        source_type: データソース種別
        source_id: 外部システムID
        imported_at: インポート日時
        confidence_score: AI解析信頼度
        needs_review: レビュー必要フラグ
        original_subject: 元の件名
        original_sender: 元の送信者
        ai_provider: 使用したAIプロバイダー
        ai_model: 使用したAIモデル

    契約:
        - source_type + source_idの組み合わせは一意
        - confidence_scoreは0.0〜1.0の範囲
    """

    source_type: str
    source_id: str
    imported_at: datetime
    confidence_score: float
    needs_review: bool
    original_subject: str
    original_sender: str
    ai_provider: str
    ai_model: str


@dataclass
class ImportError:
    """インポートエラー情報.

    Task 9.1で定義。

    Attributes:
        source_id: エラーが発生したソースID
        error_code: エラーコード（GS-3xx形式）
        error_message: エラーメッセージ
    """

    source_id: str
    error_code: str
    error_message: str


@dataclass
class ImportResult:
    """インポート結果.

    Task 9.1で定義。

    Attributes:
        total_fetched: 取得件数
        total_imported: インポート成功件数
        total_skipped: スキップ件数（重複等）
        total_failed: 失敗件数
        imported_inquiry_ids: インポートされた問い合わせIDのリスト
        errors: エラー情報のリスト
    """

    total_fetched: int
    total_imported: int
    total_skipped: int
    total_failed: int
    imported_inquiry_ids: List[int]
    errors: List[ImportError]


@dataclass
class ImporterServiceError(BaseError):
    """ImporterService固有のエラー.

    Task 9.1で定義。

    Attributes:
        code: エラーコード（GS-3xx形式）
        message: エラーメッセージ
    """

    pass


class ImporterService:
    """インポート統括サービス.

    プラグインからのデータ取得、AI解析、問い合わせ生成を統括する。

    契約:
        - Preconditions: plugin_typeが登録済みであること
        - Postconditions: 成功時、問い合わせがステータス「received」で作成される
        - Invariants: source_type + source_idの組み合わせは一意

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5
    """

    def __init__(
        self,
        session: Session,
        plugin_registry: PluginRegistryService,
        analysis_service: ImporterAnalysisService,
    ) -> None:
        """ImporterServiceを初期化.

        Args:
            session: SQLAlchemyセッション
            plugin_registry: プラグインレジストリ
            analysis_service: AI解析サービス
        """
        self._session = session
        self._plugin_registry = plugin_registry
        self._analysis_service = analysis_service
        self._inquiry_repository = InquiryRepository(session)
        self._error_log_repository = ImportErrorLogRepository(session)
        self._consecutive_errors = 0

    def execute_import(
        self,
        plugin_type: str,
        ai_provider_type: Optional[AIProviderType] = None,
    ) -> Result[ImportResult]:
        """指定プラグインでインポートを実行する.

        Task 9.2: インポート実行機能

        Args:
            plugin_type: データソースプラグイン種別
            ai_provider_type: AIプロバイダー種別（未指定時はデフォルト）

        Returns:
            Result[ImportResult]: インポート結果

        Requirements: 4.1, 4.2, 4.3, 4.5
        """
        # プラグインを取得
        plugin = self._plugin_registry.get_plugin(plugin_type)
        if plugin is None:
            logger.error(f"プラグインが見つかりません: {plugin_type}")
            return Result.err(
                ImporterServiceError(
                    code="GS-301",
                    message=f"プラグイン '{plugin_type}' が見つかりません",
                )
            )

        # 結果を初期化
        total_fetched = 0
        total_imported = 0
        total_skipped = 0
        total_failed = 0
        imported_inquiry_ids: List[int] = []
        errors: List[ImportError] = []

        try:
            # プラグインに接続
            plugin.connect()

            # データを取得
            raw_data_list = plugin.fetch()
            total_fetched = len(raw_data_list)

            # 各データを処理
            for raw_data in raw_data_list:
                result = self._process_single_import(
                    plugin_type=plugin_type,
                    raw_data=raw_data,
                    ai_provider_type=ai_provider_type,
                )

                if result.is_ok:
                    inquiry_id = result.unwrap()
                    if inquiry_id is not None:
                        imported_inquiry_ids.append(inquiry_id)
                        total_imported += 1
                        # 処理済みとしてマーク
                        plugin.mark_as_processed(raw_data.source_id)
                        # 連続エラーカウントをリセット
                        self._consecutive_errors = 0
                    else:
                        # 重複によるスキップ
                        total_skipped += 1
                else:
                    error = result.unwrap_err()
                    total_failed += 1
                    errors.append(
                        ImportError(
                            source_id=raw_data.source_id,
                            error_code=error.code,
                            error_message=error.message,
                        )
                    )
                    # 連続エラー検出
                    self._check_consecutive_errors(plugin_type)

        except ConnectionError as e:
            logger.error(f"データソース接続に失敗しました: {e}")
            self._log_error(
                plugin_type=plugin_type,
                error_code="GS-303",
                error_message=f"データソース接続に失敗しました: {e}",
                source_id=None,
            )
            return Result.err(
                ImporterServiceError(
                    code="GS-303",
                    message=f"データソース接続に失敗しました: {e}",
                )
            )
        except RuntimeError as e:
            logger.error(f"データ取得に失敗しました: {e}")
            self._log_error(
                plugin_type=plugin_type,
                error_code="GS-306",
                error_message=f"データ取得に失敗しました: {e}",
                source_id=None,
            )
            return Result.err(
                ImporterServiceError(
                    code="GS-306",
                    message=f"データ取得に失敗しました: {e}",
                )
            )
        finally:
            # 切断
            try:
                plugin.disconnect()
            except Exception as e:
                logger.warning(f"プラグイン切断中にエラーが発生しました: {e}")

        return Result.ok(
            ImportResult(
                total_fetched=total_fetched,
                total_imported=total_imported,
                total_skipped=total_skipped,
                total_failed=total_failed,
                imported_inquiry_ids=imported_inquiry_ids,
                errors=errors,
            )
        )

    def _process_single_import(
        self,
        plugin_type: str,
        raw_data: RawImportData,
        ai_provider_type: Optional[AIProviderType] = None,
    ) -> Result[Optional[int]]:
        """単一のデータをインポートする.

        Args:
            plugin_type: データソースプラグイン種別
            raw_data: 生データ
            ai_provider_type: AIプロバイダー種別

        Returns:
            Result[Optional[int]]: インポートされた問い合わせID（スキップ時はNone）
        """
        # 重複チェック
        if self.check_duplicate(plugin_type, raw_data.source_id):
            logger.info(f"重複検出、スキップします: {raw_data.source_id}")
            return Result.ok(None)

        # AI解析
        analysis_result = self._analysis_service.analyze(
            raw_data=raw_data,
            provider_type=ai_provider_type,
        )

        if analysis_result.is_err:
            error = analysis_result.unwrap_err()
            self._log_error(
                plugin_type=plugin_type,
                error_code=error.code,
                error_message=error.message,
                source_id=raw_data.source_id,
            )
            return Result.err(error)

        analysis = analysis_result.unwrap()

        # 問い合わせを作成
        try:
            inquiry = self._create_inquiry(
                plugin_type=plugin_type,
                raw_data=raw_data,
                analysis=analysis,
            )
            return Result.ok(inquiry.id)
        except Exception as e:
            error_message = f"問い合わせ作成に失敗しました: {e}"
            logger.error(error_message)
            self._log_error(
                plugin_type=plugin_type,
                error_code="GS-305",
                error_message=error_message,
                source_id=raw_data.source_id,
            )
            return Result.err(
                ImporterServiceError(
                    code="GS-305",
                    message=error_message,
                )
            )

    def _create_inquiry(
        self,
        plugin_type: str,
        raw_data: RawImportData,
        analysis: Any,
    ) -> Any:
        """問い合わせを作成する.

        Requirements: 4.1, 4.2, 4.3

        Args:
            plugin_type: データソースプラグイン種別
            raw_data: 生データ
            analysis: AI解析結果

        Returns:
            InquiryModel: 作成された問い合わせ
        """
        # ImporterMetadataを構築
        importer_metadata = ImporterMetadata(
            source_type=plugin_type,
            source_id=raw_data.source_id,
            imported_at=datetime.now(UTC),
            confidence_score=analysis.confidence_score,
            needs_review=analysis.needs_review,
            original_subject=raw_data.subject,
            original_sender=raw_data.sender,
            ai_provider=analysis.provider_type,
            ai_model=analysis.model,
        )

        # 問い合わせ作成データを構築
        create_data = CreateInquiryData(
            user_id=f"importer:{plugin_type}",
            content=analysis.content,
            source_system=f"importer:{plugin_type}",
            timestamp=raw_data.received_at,
            status=InquiryStatus.RECEIVED,  # 要件4.3: ステータスは「received」
        )

        # 問い合わせを作成
        inquiry = self._inquiry_repository.create(create_data)

        # メタデータを更新
        inquiry.inquiry_metadata = {
            "importer": {
                "source_type": importer_metadata.source_type,
                "source_id": importer_metadata.source_id,
                "imported_at": importer_metadata.imported_at.isoformat(),
                "confidence_score": importer_metadata.confidence_score,
                "needs_review": importer_metadata.needs_review,
                "original_subject": importer_metadata.original_subject,
                "original_sender": importer_metadata.original_sender,
                "ai_provider": importer_metadata.ai_provider,
                "ai_model": importer_metadata.ai_model,
            }
        }
        self._session.commit()
        self._session.refresh(inquiry)

        return inquiry

    def check_duplicate(self, source_type: str, source_id: str) -> bool:
        """重複チェック（inquiry_metadataを検索）.

        Requirements: 4.5

        Args:
            source_type: データソース種別
            source_id: 外部システムのID

        Returns:
            bool: 重複がある場合True
        """
        from sqlalchemy import and_, text

        from models.database.inquiry import InquiryModel

        # JSONB のパス検索を使用
        # inquiry_metadata->'importer'->>'source_type' = source_type
        result = (
            self._session.query(InquiryModel)
            .filter(
                and_(
                    InquiryModel.inquiry_metadata.op("->")(text("'importer'")).op(
                        "->>"
                    )(text("'source_type'"))
                    == source_type,
                    InquiryModel.inquiry_metadata.op("->")(text("'importer'")).op(
                        "->>"
                    )(text("'source_id'"))
                    == source_id,
                )
            )
            .first()
        )
        return result is not None

    def _log_error(
        self,
        plugin_type: str,
        error_code: str,
        error_message: str,
        source_id: Optional[str],
    ) -> None:
        """エラーログを記録する.

        Requirements: 5.1

        Args:
            plugin_type: プラグイン種別
            error_code: エラーコード
            error_message: エラーメッセージ
            source_id: ソースID（オプション）
        """
        try:
            self._error_log_repository.create(
                CreateErrorLogData(
                    error_code=error_code,
                    plugin_type=plugin_type,
                    error_message=error_message,
                    source_id=source_id,
                )
            )
        except Exception as e:
            logger.error(f"エラーログの記録に失敗しました: {e}")

    def _check_consecutive_errors(self, plugin_type: str) -> None:
        """連続エラーを検出してアラートを発生させる.

        Requirements: 5.3

        Args:
            plugin_type: プラグイン種別
        """
        self._consecutive_errors += 1
        if self._consecutive_errors >= CONSECUTIVE_ERROR_THRESHOLD:
            logger.warning(
                f"連続エラー検出: プラグイン '{plugin_type}' で"
                f"{self._consecutive_errors}件の連続エラーが発生しました。"
                "プラグインの自動停止を検討してください。"
            )

    def get_error_stats(
        self,
        plugin_type: Optional[str] = None,
    ) -> List[ErrorStats]:
        """エラー統計を取得する.

        Requirements: 5.4

        Args:
            plugin_type: プラグイン種別でフィルタ（オプション）

        Returns:
            List[ErrorStats]: エラー統計のリスト
        """
        return self._error_log_repository.get_error_stats(
            plugin_type=plugin_type,
            unresolved_only=False,
        )

    def retry_failed(
        self,
        plugin_type: str,
        source_ids: List[str],
        ai_provider_type: Optional[AIProviderType] = None,
    ) -> Result[ImportResult]:
        """失敗したインポートをリトライする.

        Task 9.4: リトライ機能

        Requirements: 5.2

        Args:
            plugin_type: データソースプラグイン種別
            source_ids: リトライ対象のソースIDリスト
            ai_provider_type: AIプロバイダー種別（オプション）

        Returns:
            Result[ImportResult]: リトライ結果
        """
        # プラグインを取得
        plugin = self._plugin_registry.get_plugin(plugin_type)
        if plugin is None:
            logger.error(f"プラグインが見つかりません: {plugin_type}")
            return Result.err(
                ImporterServiceError(
                    code="GS-301",
                    message=f"プラグイン '{plugin_type}' が見つかりません",
                )
            )

        # 結果を初期化
        total_fetched = len(source_ids)
        total_imported = 0
        total_skipped = 0
        total_failed = 0
        imported_inquiry_ids: List[int] = []
        errors: List[ImportError] = []

        try:
            # プラグインに接続
            plugin.connect()

            # データを取得
            raw_data_list = plugin.fetch()

            # source_idsに含まれるデータのみを処理
            target_data_map: Dict[str, RawImportData] = {
                rd.source_id: rd for rd in raw_data_list if rd.source_id in source_ids
            }

            for source_id in source_ids:
                if source_id not in target_data_map:
                    logger.warning(f"リトライ対象データが見つかりません: {source_id}")
                    total_skipped += 1
                    continue

                raw_data = target_data_map[source_id]

                # 重複チェック（既にインポート済みの場合はスキップ）
                if self.check_duplicate(plugin_type, source_id):
                    logger.info(f"既にインポート済み、スキップします: {source_id}")
                    total_skipped += 1
                    # リトライ成功としてエラーログを解決済みにマーク
                    self._error_log_repository.mark_resolved_by_source(
                        plugin_type=plugin_type,
                        source_id=source_id,
                    )
                    continue

                result = self._process_single_import(
                    plugin_type=plugin_type,
                    raw_data=raw_data,
                    ai_provider_type=ai_provider_type,
                )

                if result.is_ok:
                    inquiry_id = result.unwrap()
                    if inquiry_id is not None:
                        imported_inquiry_ids.append(inquiry_id)
                        total_imported += 1
                        # 処理済みとしてマーク
                        plugin.mark_as_processed(source_id)
                        # リトライ成功としてエラーログを解決済みにマーク
                        self._error_log_repository.mark_resolved_by_source(
                            plugin_type=plugin_type,
                            source_id=source_id,
                        )
                    else:
                        # 重複によるスキップ
                        total_skipped += 1
                else:
                    error = result.unwrap_err()
                    total_failed += 1
                    errors.append(
                        ImportError(
                            source_id=source_id,
                            error_code=error.code,
                            error_message=error.message,
                        )
                    )
                    # リトライ失敗時もエラーログに記録する
                    self._log_error(
                        plugin_type=plugin_type,
                        source_id=source_id,
                        error=error,
                    )

        except ConnectionError as e:
            logger.error(f"データソース接続に失敗しました: {e}")
            return Result.err(
                ImporterServiceError(
                    code="GS-303",
                    message=f"データソース接続に失敗しました: {e}",
                )
            )
        except RuntimeError as e:
            logger.error(f"データ取得に失敗しました: {e}")
            return Result.err(
                ImporterServiceError(
                    code="GS-306",
                    message=f"データ取得に失敗しました: {e}",
                )
            )
        finally:
            # 切断
            try:
                plugin.disconnect()
            except Exception as e:
                logger.warning(f"プラグイン切断中にエラーが発生しました: {e}")

        return Result.ok(
            ImportResult(
                total_fetched=total_fetched,
                total_imported=total_imported,
                total_skipped=total_skipped,
                total_failed=total_failed,
                imported_inquiry_ids=imported_inquiry_ids,
                errors=errors,
            )
        )

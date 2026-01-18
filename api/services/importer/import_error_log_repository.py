"""ImportErrorLogRepository data access layer.

インポートエラーログのCRUD操作とクエリ実行を提供する。
"""
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from models.database.import_error_log import ImportErrorLogModel


@dataclass
class CreateErrorLogData:
    """エラーログ作成データ."""

    error_code: str
    plugin_type: str
    error_message: str
    source_id: Optional[str] = None


@dataclass
class ErrorLogFilter:
    """エラーログフィルタ条件."""

    error_code: Optional[str] = None
    plugin_type: Optional[str] = None
    resolved: Optional[bool] = None
    occurred_after: Optional[datetime] = None
    occurred_before: Optional[datetime] = None


@dataclass
class ErrorStats:
    """エラー統計.

    Requirements: 5.4
    """

    error_code: str
    count: int
    last_occurred: datetime


class ImportErrorLogRepository:
    """インポートエラーログリポジトリ.

    インポートエラーログのCRUD操作とクエリ実行を提供する。

    Requirements: 5.1, 5.4
    """

    def __init__(self, session: Session):
        """Initialize ImportErrorLogRepository.

        Args:
            session: SQLAlchemyセッション
        """
        self.session = session

    def create(self, data: CreateErrorLogData) -> ImportErrorLogModel:
        """エラーログを作成する（要件5.1）.

        Args:
            data: エラーログ作成データ

        Returns:
            ImportErrorLogModel: 作成されたエラーログエンティティ
        """
        error_log = ImportErrorLogModel(
            error_code=data.error_code,
            plugin_type=data.plugin_type,
            source_id=data.source_id,
            error_message=data.error_message,
            occurred_at=datetime.now(UTC),
            resolved=False,
        )
        self.session.add(error_log)
        self.session.commit()
        self.session.refresh(error_log)
        return error_log

    def find_by_id(self, log_id: int) -> Optional[ImportErrorLogModel]:
        """IDでエラーログを取得する.

        Args:
            log_id: エラーログID

        Returns:
            ImportErrorLogModel | None: エラーログエンティティ、存在しない場合はNone
        """
        return (
            self.session.query(ImportErrorLogModel)
            .filter(ImportErrorLogModel.id == log_id)
            .first()
        )

    def find_many(self, filter: ErrorLogFilter) -> list[ImportErrorLogModel]:
        """エラーログを検索する.

        Args:
            filter: フィルタ条件

        Returns:
            list[ImportErrorLogModel]: エラーログエンティティのリスト
        """
        query = self.session.query(ImportErrorLogModel)

        if filter.error_code is not None:
            query = query.filter(ImportErrorLogModel.error_code == filter.error_code)

        if filter.plugin_type is not None:
            query = query.filter(ImportErrorLogModel.plugin_type == filter.plugin_type)

        if filter.resolved is not None:
            query = query.filter(ImportErrorLogModel.resolved == filter.resolved)

        if filter.occurred_after is not None:
            query = query.filter(
                ImportErrorLogModel.occurred_at >= filter.occurred_after
            )

        if filter.occurred_before is not None:
            query = query.filter(
                ImportErrorLogModel.occurred_at <= filter.occurred_before
            )

        return query.order_by(desc(ImportErrorLogModel.occurred_at)).all()

    def mark_resolved(self, log_id: int) -> bool:
        """エラーログを解決済みにマークする.

        Args:
            log_id: エラーログID

        Returns:
            bool: 成功した場合True、存在しない場合False
        """
        log = self.find_by_id(log_id)
        if log is None:
            return False

        log.resolved = True
        self.session.commit()
        return True

    def mark_resolved_by_source(self, plugin_type: str, source_id: str) -> int:
        """source_typeとsource_idでエラーログを解決済みにマークする.

        リトライ成功時に使用する。

        Args:
            plugin_type: データソースプラグイン種別
            source_id: 外部システムのID

        Returns:
            int: 更新されたレコード数
        """
        result = (
            self.session.query(ImportErrorLogModel)
            .filter(
                ImportErrorLogModel.plugin_type == plugin_type,
                ImportErrorLogModel.source_id == source_id,
                ImportErrorLogModel.resolved == False,  # noqa: E712
            )
            .update({"resolved": True})
        )
        self.session.commit()
        return result

    def get_error_stats(
        self,
        plugin_type: Optional[str] = None,
        unresolved_only: bool = False,
    ) -> list[ErrorStats]:
        """エラー統計を取得する（要件5.4）.

        error_code別に集計し、発生件数と最終発生日時を返す。

        Args:
            plugin_type: プラグイン種別でフィルタ（オプション）
            unresolved_only: Trueの場合、未解決のエラーのみ集計。
                Falseの場合（デフォルト）、解決済み・未解決を区別せず全て集計

        Returns:
            list[ErrorStats]: エラー統計のリスト（件数の降順）
        """
        query = self.session.query(
            ImportErrorLogModel.error_code,
            func.count(ImportErrorLogModel.id).label("count"),
            func.max(ImportErrorLogModel.occurred_at).label("last_occurred"),
        )

        if plugin_type is not None:
            query = query.filter(ImportErrorLogModel.plugin_type == plugin_type)

        if unresolved_only:
            query = query.filter(ImportErrorLogModel.resolved == False)  # noqa: E712

        query = query.group_by(ImportErrorLogModel.error_code).order_by(desc("count"))

        results = query.all()

        return [
            ErrorStats(
                error_code=row.error_code,
                count=row.count,
                last_occurred=row.last_occurred,
            )
            for row in results
        ]

    def delete_old_logs(
        self,
        cutoff: datetime,
        resolved_only: bool = False,
    ) -> int:
        """古いエラーログを削除する.

        保持期間を超えたログをクリーンアップするために使用。
        設計: 90日保持。

        Args:
            cutoff: この日時より前のログを削除
            resolved_only: Trueの場合、解決済みログのみ削除

        Returns:
            int: 削除されたレコード数
        """
        query = self.session.query(ImportErrorLogModel).filter(
            ImportErrorLogModel.occurred_at < cutoff
        )

        if resolved_only:
            query = query.filter(ImportErrorLogModel.resolved == True)  # noqa: E712

        # 削除対象のIDを先に取得（count用）
        delete_count = query.count()

        # 削除実行
        query.delete()
        self.session.commit()

        return delete_count

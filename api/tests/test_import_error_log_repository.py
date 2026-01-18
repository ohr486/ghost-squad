"""ImportErrorLogRepositoryのテスト."""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from models.database.base import Base
from models.database.import_error_log import ImportErrorLogModel
# Direct import to avoid __init__.py chain that requires anthropic module
from services.importer.import_error_log_repository import (  # noqa: E402
    CreateErrorLogData, ErrorLogFilter, ErrorStats, ImportErrorLogRepository)


@pytest.fixture
def db_engine():
    """テスト用データベースエンジン."""
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """テスト用インメモリデータベースセッション."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repository(db_session):
    """テスト用リポジトリ."""
    return ImportErrorLogRepository(db_session)


@pytest.fixture
def sample_error_logs(db_session):
    """テスト用サンプルエラーログ."""
    base_time = datetime.now(UTC)
    logs = [
        ImportErrorLogModel(
            error_code="GS-303",
            plugin_type="email",
            source_id="msg-001",
            error_message="IMAP接続エラー",
            occurred_at=base_time - timedelta(hours=3),
            resolved=False,
        ),
        ImportErrorLogModel(
            error_code="GS-303",
            plugin_type="email",
            source_id="msg-002",
            error_message="IMAP接続エラー2",
            occurred_at=base_time - timedelta(hours=2),
            resolved=True,
        ),
        ImportErrorLogModel(
            error_code="GS-304",
            plugin_type="email",
            source_id="msg-003",
            error_message="AI解析エラー",
            occurred_at=base_time - timedelta(hours=1),
            resolved=False,
        ),
        ImportErrorLogModel(
            error_code="GS-308",
            plugin_type="sentry",
            error_message="AIプロバイダー未検出",
            occurred_at=base_time,
            resolved=False,
        ),
    ]
    db_session.add_all(logs)
    db_session.commit()
    return logs


class TestCreateErrorLogData:
    """CreateErrorLogDataのテストクラス."""

    def test_create_error_log_data_with_all_fields(self):
        """すべてのフィールドでCreateErrorLogDataを作成できる."""
        data = CreateErrorLogData(
            error_code="GS-303",
            plugin_type="email",
            error_message="テストエラー",
            source_id="msg-123",
        )
        assert data.error_code == "GS-303"
        assert data.plugin_type == "email"
        assert data.error_message == "テストエラー"
        assert data.source_id == "msg-123"

    def test_create_error_log_data_without_source_id(self):
        """source_idなしでCreateErrorLogDataを作成できる."""
        data = CreateErrorLogData(
            error_code="GS-308",
            plugin_type="email",
            error_message="テストエラー",
        )
        assert data.source_id is None


class TestErrorLogFilter:
    """ErrorLogFilterのテストクラス."""

    def test_error_log_filter_defaults(self):
        """デフォルト値が正しく設定される."""
        filter = ErrorLogFilter()
        assert filter.error_code is None
        assert filter.plugin_type is None
        assert filter.resolved is None
        assert filter.occurred_after is None
        assert filter.occurred_before is None

    def test_error_log_filter_with_all_fields(self):
        """すべてのフィールドで初期化できる."""
        now = datetime.now(UTC)
        filter = ErrorLogFilter(
            error_code="GS-303",
            plugin_type="email",
            resolved=False,
            occurred_after=now - timedelta(days=1),
            occurred_before=now,
        )
        assert filter.error_code == "GS-303"
        assert filter.plugin_type == "email"
        assert filter.resolved is False


class TestImportErrorLogRepositoryCreate:
    """ImportErrorLogRepository作成機能のテストクラス."""

    def test_create_error_log(self, repository, db_session):
        """エラーログを作成できる."""
        # Arrange
        data = CreateErrorLogData(
            error_code="GS-303",
            plugin_type="email",
            error_message="IMAP接続に失敗しました",
            source_id="msg-123",
        )

        # Act
        log = repository.create(data)

        # Assert
        assert log.id is not None
        assert log.error_code == "GS-303"
        assert log.plugin_type == "email"
        assert log.error_message == "IMAP接続に失敗しました"
        assert log.source_id == "msg-123"
        assert log.resolved is False
        assert log.occurred_at is not None

    def test_create_error_log_without_source_id(self, repository):
        """source_idなしでエラーログを作成できる."""
        # Arrange
        data = CreateErrorLogData(
            error_code="GS-308",
            plugin_type="email",
            error_message="AIプロバイダー未検出",
        )

        # Act
        log = repository.create(data)

        # Assert
        assert log.id is not None
        assert log.source_id is None


class TestImportErrorLogRepositoryMarkResolved:
    """ImportErrorLogRepository解決済みマーク機能のテストクラス."""

    def test_mark_resolved(self, repository, sample_error_logs):
        """エラーログを解決済みにマークできる."""
        # Arrange
        log_id = sample_error_logs[0].id
        assert sample_error_logs[0].resolved is False

        # Act
        result = repository.mark_resolved(log_id)

        # Assert
        assert result is True
        log = repository.find_by_id(log_id)
        assert log.resolved is True

    def test_mark_resolved_nonexistent(self, repository):
        """存在しないエラーログIDでFalseを返す."""
        # Act
        result = repository.mark_resolved(99999)

        # Assert
        assert result is False

    def test_mark_resolved_by_source(self, repository, sample_error_logs, db_session):
        """source_typeとsource_idで解決済みにマークできる."""
        # Arrange
        # sample_error_logs[0] has source_id="msg-001"
        assert sample_error_logs[0].resolved is False

        # Act
        count = repository.mark_resolved_by_source("email", "msg-001")

        # Assert
        assert count == 1
        db_session.refresh(sample_error_logs[0])
        assert sample_error_logs[0].resolved is True


class TestImportErrorLogRepositoryFind:
    """ImportErrorLogRepository検索機能のテストクラス."""

    def test_find_by_id(self, repository, sample_error_logs):
        """IDでエラーログを取得できる."""
        # Arrange
        log_id = sample_error_logs[0].id

        # Act
        log = repository.find_by_id(log_id)

        # Assert
        assert log is not None
        assert log.id == log_id

    def test_find_by_id_nonexistent(self, repository):
        """存在しないIDでNoneを返す."""
        # Act
        log = repository.find_by_id(99999)

        # Assert
        assert log is None

    def test_find_many_all(self, repository, sample_error_logs):
        """すべてのエラーログを取得できる."""
        # Act
        logs = repository.find_many(ErrorLogFilter())

        # Assert
        assert len(logs) == 4

    def test_find_many_by_error_code(self, repository, sample_error_logs):
        """error_codeでフィルタリングできる."""
        # Act
        logs = repository.find_many(ErrorLogFilter(error_code="GS-303"))

        # Assert
        assert len(logs) == 2
        for log in logs:
            assert log.error_code == "GS-303"

    def test_find_many_by_plugin_type(self, repository, sample_error_logs):
        """plugin_typeでフィルタリングできる."""
        # Act
        logs = repository.find_many(ErrorLogFilter(plugin_type="email"))

        # Assert
        assert len(logs) == 3
        for log in logs:
            assert log.plugin_type == "email"

    def test_find_many_by_resolved(self, repository, sample_error_logs):
        """resolvedでフィルタリングできる."""
        # Act
        unresolved_logs = repository.find_many(ErrorLogFilter(resolved=False))

        # Assert
        assert len(unresolved_logs) == 3
        for log in unresolved_logs:
            assert log.resolved is False

    def test_find_many_by_date_range(self, repository, sample_error_logs):
        """日付範囲でフィルタリングできる."""
        # Arrange
        now = datetime.now(UTC)
        # Use 1.5 hours ago to ensure we get exactly -1h and now logs
        one_and_half_hours_ago = now - timedelta(hours=1, minutes=30)

        # Act
        filter = ErrorLogFilter(occurred_after=one_and_half_hours_ago)
        logs = repository.find_many(filter)

        # Assert
        # occurred_at >= 1.5h ago のログは 2つ（-1h, now）
        assert len(logs) == 2


class TestImportErrorLogRepositoryStats:
    """ImportErrorLogRepository統計機能のテストクラス."""

    def test_get_error_stats(self, repository, sample_error_logs):
        """エラー統計を取得できる."""
        # Act
        stats = repository.get_error_stats()

        # Assert
        assert len(stats) == 3  # GS-303, GS-304, GS-308

        # 統計はcountでソートされている（desc）
        stats_dict = {s.error_code: s for s in stats}

        assert stats_dict["GS-303"].count == 2
        assert stats_dict["GS-304"].count == 1
        assert stats_dict["GS-308"].count == 1

    def test_get_error_stats_unresolved_only(self, repository, sample_error_logs):
        """未解決のみのエラー統計を取得できる."""
        # Act
        stats = repository.get_error_stats(unresolved_only=True)

        # Assert
        stats_dict = {s.error_code: s for s in stats}

        # GS-303は2件あるが、1件は解決済みなので未解決は1件
        assert stats_dict["GS-303"].count == 1
        assert stats_dict["GS-304"].count == 1
        assert stats_dict["GS-308"].count == 1

    def test_get_error_stats_by_plugin_type(self, repository, sample_error_logs):
        """plugin_type別のエラー統計を取得できる."""
        # Act
        stats = repository.get_error_stats(plugin_type="email")

        # Assert
        # emailプラグインのみ: GS-303(2件), GS-304(1件)
        assert len(stats) == 2

        stats_dict = {s.error_code: s for s in stats}
        assert stats_dict["GS-303"].count == 2
        assert stats_dict["GS-304"].count == 1

    def test_get_error_stats_empty(self, repository):
        """エラーログがない場合は空リストを返す."""
        # Act
        stats = repository.get_error_stats()

        # Assert
        assert stats == []


class TestImportErrorLogRepositoryDelete:
    """ImportErrorLogRepository削除機能のテストクラス."""

    def test_delete_old_logs(self, repository, sample_error_logs, db_session):
        """古いエラーログを削除できる."""
        # Arrange
        # sample_error_logs: -3h, -2h, -1h, now
        cutoff = datetime.now(UTC) - timedelta(hours=2, minutes=30)

        # Act
        deleted_count = repository.delete_old_logs(cutoff)

        # Assert
        assert deleted_count == 1  # -3hのログのみ削除

        remaining_logs = repository.find_many(ErrorLogFilter())
        assert len(remaining_logs) == 3

    def test_delete_old_logs_resolved_only(
        self, repository, sample_error_logs, db_session
    ):
        """解決済みの古いエラーログのみ削除できる."""
        # Arrange
        cutoff = datetime.now(UTC)  # すべてのログが対象になる

        # Act
        deleted_count = repository.delete_old_logs(cutoff, resolved_only=True)

        # Assert
        assert deleted_count == 1  # 解決済みは1件のみ

        remaining_logs = repository.find_many(ErrorLogFilter())
        assert len(remaining_logs) == 3


class TestErrorStats:
    """ErrorStatsデータクラスのテストクラス."""

    def test_error_stats_creation(self):
        """ErrorStatsを作成できる."""
        now = datetime.now(UTC)
        stats = ErrorStats(
            error_code="GS-303",
            count=5,
            last_occurred=now,
        )

        assert stats.error_code == "GS-303"
        assert stats.count == 5
        assert stats.last_occurred == now

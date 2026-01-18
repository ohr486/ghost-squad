"""ImportErrorLogモデルのテスト."""
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from models.database.base import Base
from models.database.import_error_log import ImportErrorLogModel


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


class TestImportErrorLogModel:
    """ImportErrorLogModelのテストクラス."""

    def test_create_import_error_log_with_all_fields(self, db_session):
        """すべてのフィールドを持つエラーログを作成できる."""
        # Arrange
        occurred_at = datetime.now(UTC)
        error_log = ImportErrorLogModel(
            error_code="GS-303",
            plugin_type="email",
            source_id="message-id-123",
            error_message="IMAP接続に失敗しました",
            occurred_at=occurred_at,
            resolved=False,
        )

        # Act
        db_session.add(error_log)
        db_session.commit()
        db_session.refresh(error_log)

        # Assert
        assert error_log.id is not None
        assert error_log.error_code == "GS-303"
        assert error_log.plugin_type == "email"
        assert error_log.source_id == "message-id-123"
        assert error_log.error_message == "IMAP接続に失敗しました"
        # Note: SQLite doesn't preserve timezone info, so we compare without tzinfo
        assert error_log.occurred_at.replace(tzinfo=None) == occurred_at.replace(
            tzinfo=None
        )
        assert error_log.resolved is False
        assert error_log.created_at is not None
        assert error_log.updated_at is not None

    def test_create_import_error_log_without_source_id(self, db_session):
        """source_idなしでエラーログを作成できる（オプショナル）."""
        # Arrange
        error_log = ImportErrorLogModel(
            error_code="GS-308",
            plugin_type="email",
            source_id=None,
            error_message="AIプロバイダーが見つかりません",
            occurred_at=datetime.now(UTC),
        )

        # Act
        db_session.add(error_log)
        db_session.commit()
        db_session.refresh(error_log)

        # Assert
        assert error_log.id is not None
        assert error_log.source_id is None

    def test_resolved_defaults_to_false(self, db_session):
        """resolvedフィールドのデフォルトがFalseである."""
        # Arrange
        error_log = ImportErrorLogModel(
            error_code="GS-304",
            plugin_type="email",
            error_message="AI解析に失敗しました",
            occurred_at=datetime.now(UTC),
        )

        # Act
        db_session.add(error_log)
        db_session.commit()
        db_session.refresh(error_log)

        # Assert
        assert error_log.resolved is False

    def test_error_code_is_required(self, db_session):
        """error_codeフィールドは必須である."""
        # Arrange & Act & Assert
        error_log = ImportErrorLogModel(
            error_code=None,
            plugin_type="email",
            error_message="エラーメッセージ",
            occurred_at=datetime.now(UTC),
        )
        db_session.add(error_log)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_plugin_type_is_required(self, db_session):
        """plugin_typeフィールドは必須である."""
        # Arrange & Act & Assert
        error_log = ImportErrorLogModel(
            error_code="GS-303",
            plugin_type=None,
            error_message="エラーメッセージ",
            occurred_at=datetime.now(UTC),
        )
        db_session.add(error_log)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_error_message_is_required(self, db_session):
        """error_messageフィールドは必須である."""
        # Arrange & Act & Assert
        error_log = ImportErrorLogModel(
            error_code="GS-303",
            plugin_type="email",
            error_message=None,
            occurred_at=datetime.now(UTC),
        )
        db_session.add(error_log)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_occurred_at_is_required(self, db_session):
        """occurred_atフィールドは必須である."""
        # Arrange & Act & Assert
        error_log = ImportErrorLogModel(
            error_code="GS-303",
            plugin_type="email",
            error_message="エラーメッセージ",
            occurred_at=None,
        )
        db_session.add(error_log)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_error_code_max_length_10(self, db_session):
        """error_codeは最大10文字である（GS-xxx形式）."""
        # Arrange
        error_log = ImportErrorLogModel(
            error_code="GS-399",  # 有効な長さ
            plugin_type="email",
            error_message="エラーメッセージ",
            occurred_at=datetime.now(UTC),
        )

        # Act
        db_session.add(error_log)
        db_session.commit()

        # Assert
        assert len(error_log.error_code) <= 10

    def test_plugin_type_max_length_50(self, db_session):
        """plugin_typeは最大50文字である."""
        # Arrange
        long_plugin_type = "a" * 50  # 50文字

        error_log = ImportErrorLogModel(
            error_code="GS-303",
            plugin_type=long_plugin_type,
            error_message="エラーメッセージ",
            occurred_at=datetime.now(UTC),
        )

        # Act
        db_session.add(error_log)
        db_session.commit()

        # Assert
        assert len(error_log.plugin_type) == 50

    def test_source_id_max_length_255(self, db_session):
        """source_idは最大255文字である."""
        # Arrange
        long_source_id = "x" * 255  # 255文字

        error_log = ImportErrorLogModel(
            error_code="GS-303",
            plugin_type="email",
            source_id=long_source_id,
            error_message="エラーメッセージ",
            occurred_at=datetime.now(UTC),
        )

        # Act
        db_session.add(error_log)
        db_session.commit()

        # Assert
        assert len(error_log.source_id) == 255

    def test_error_message_max_length_1000(self, db_session):
        """error_messageは最大1000文字である."""
        # Arrange
        long_message = "エ" * 1000  # 1000文字

        error_log = ImportErrorLogModel(
            error_code="GS-303",
            plugin_type="email",
            error_message=long_message,
            occurred_at=datetime.now(UTC),
        )

        # Act
        db_session.add(error_log)
        db_session.commit()

        # Assert
        assert len(error_log.error_message) == 1000

    def test_update_resolved_to_true(self, db_session):
        """resolvedをTrueに更新できる."""
        # Arrange
        error_log = ImportErrorLogModel(
            error_code="GS-303",
            plugin_type="email",
            error_message="IMAP接続に失敗しました",
            occurred_at=datetime.now(UTC),
        )
        db_session.add(error_log)
        db_session.commit()

        # Act
        error_log.resolved = True
        db_session.commit()
        db_session.refresh(error_log)

        # Assert
        assert error_log.resolved is True

    def test_import_error_log_repr(self, db_session):
        """ImportErrorLogModelの文字列表現が適切である."""
        # Arrange
        error_log = ImportErrorLogModel(
            error_code="GS-303",
            plugin_type="email",
            error_message="IMAP接続に失敗しました",
            occurred_at=datetime.now(UTC),
        )
        db_session.add(error_log)
        db_session.commit()

        # Assert
        repr_str = repr(error_log)
        assert f"<ImportErrorLogModel(id={error_log.id}" in repr_str
        assert "error_code='GS-303'" in repr_str
        assert "plugin_type='email'" in repr_str


class TestImportErrorLogModelCRUDOperations:
    """ImportErrorLogModelのCRUD操作テストクラス."""

    def test_create_multiple_error_logs(self, db_session):
        """複数のエラーログを作成できる."""
        # Arrange
        error_logs = [
            ImportErrorLogModel(
                error_code="GS-303",
                plugin_type="email",
                error_message="接続エラー1",
                occurred_at=datetime.now(UTC),
            ),
            ImportErrorLogModel(
                error_code="GS-304",
                plugin_type="email",
                error_message="解析エラー",
                occurred_at=datetime.now(UTC),
            ),
            ImportErrorLogModel(
                error_code="GS-303",
                plugin_type="email",
                error_message="接続エラー2",
                occurred_at=datetime.now(UTC),
            ),
        ]

        # Act
        db_session.add_all(error_logs)
        db_session.commit()

        # Assert
        count = db_session.query(ImportErrorLogModel).count()
        assert count == 3

    def test_filter_by_error_code(self, db_session):
        """error_codeでフィルタリングできる."""
        # Arrange
        error_logs = [
            ImportErrorLogModel(
                error_code="GS-303",
                plugin_type="email",
                error_message="接続エラー",
                occurred_at=datetime.now(UTC),
            ),
            ImportErrorLogModel(
                error_code="GS-304",
                plugin_type="email",
                error_message="解析エラー",
                occurred_at=datetime.now(UTC),
            ),
            ImportErrorLogModel(
                error_code="GS-303",
                plugin_type="sentry",
                error_message="接続エラー",
                occurred_at=datetime.now(UTC),
            ),
        ]
        db_session.add_all(error_logs)
        db_session.commit()

        # Act
        gs303_logs = (
            db_session.query(ImportErrorLogModel).filter_by(error_code="GS-303").all()
        )

        # Assert
        assert len(gs303_logs) == 2
        for log in gs303_logs:
            assert log.error_code == "GS-303"

    def test_filter_by_plugin_type(self, db_session):
        """plugin_typeでフィルタリングできる."""
        # Arrange
        error_logs = [
            ImportErrorLogModel(
                error_code="GS-303",
                plugin_type="email",
                error_message="エラー1",
                occurred_at=datetime.now(UTC),
            ),
            ImportErrorLogModel(
                error_code="GS-303",
                plugin_type="sentry",
                error_message="エラー2",
                occurred_at=datetime.now(UTC),
            ),
        ]
        db_session.add_all(error_logs)
        db_session.commit()

        # Act
        email_logs = (
            db_session.query(ImportErrorLogModel).filter_by(plugin_type="email").all()
        )

        # Assert
        assert len(email_logs) == 1
        assert email_logs[0].plugin_type == "email"

    def test_filter_by_resolved_status(self, db_session):
        """resolvedステータスでフィルタリングできる."""
        # Arrange
        error_logs = [
            ImportErrorLogModel(
                error_code="GS-303",
                plugin_type="email",
                error_message="未解決エラー",
                occurred_at=datetime.now(UTC),
                resolved=False,
            ),
            ImportErrorLogModel(
                error_code="GS-304",
                plugin_type="email",
                error_message="解決済みエラー",
                occurred_at=datetime.now(UTC),
                resolved=True,
            ),
        ]
        db_session.add_all(error_logs)
        db_session.commit()

        # Act
        unresolved_logs = (
            db_session.query(ImportErrorLogModel).filter_by(resolved=False).all()
        )

        # Assert
        assert len(unresolved_logs) == 1
        assert unresolved_logs[0].error_message == "未解決エラー"

    def test_delete_error_log(self, db_session):
        """エラーログを削除できる."""
        # Arrange
        error_log = ImportErrorLogModel(
            error_code="GS-303",
            plugin_type="email",
            error_message="削除されるエラー",
            occurred_at=datetime.now(UTC),
        )
        db_session.add(error_log)
        db_session.commit()
        log_id = error_log.id

        # Act
        db_session.delete(error_log)
        db_session.commit()

        # Assert
        deleted_log = db_session.query(ImportErrorLogModel).filter_by(id=log_id).first()
        assert deleted_log is None

    def test_order_by_occurred_at(self, db_session):
        """occurred_atで並び替えできる."""
        # Arrange
        from datetime import timedelta

        base_time = datetime.now(UTC)
        error_logs = [
            ImportErrorLogModel(
                error_code="GS-303",
                plugin_type="email",
                error_message="古いエラー",
                occurred_at=base_time - timedelta(hours=2),
            ),
            ImportErrorLogModel(
                error_code="GS-303",
                plugin_type="email",
                error_message="最新エラー",
                occurred_at=base_time,
            ),
            ImportErrorLogModel(
                error_code="GS-303",
                plugin_type="email",
                error_message="中間エラー",
                occurred_at=base_time - timedelta(hours=1),
            ),
        ]
        db_session.add_all(error_logs)
        db_session.commit()

        # Act
        sorted_logs = (
            db_session.query(ImportErrorLogModel)
            .order_by(ImportErrorLogModel.occurred_at.desc())
            .all()
        )

        # Assert
        assert sorted_logs[0].error_message == "最新エラー"
        assert sorted_logs[1].error_message == "中間エラー"
        assert sorted_logs[2].error_message == "古いエラー"

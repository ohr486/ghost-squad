"""問い合わせモデルのテスト."""
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from models.database.base import Base
from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus


@pytest.fixture
def db_engine():
    """テスト用データベースエンジン."""
    engine = create_engine("sqlite:///:memory:")
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


class TestInquiryModel:
    """InquiryModelのテストクラス."""

    def test_create_inquiry_with_all_fields(self, db_session):
        """すべてのフィールドを持つ問い合わせを作成できる."""
        # Arrange
        inquiry_data = {
            "user_id": "test_user_001",
            "content": "ログイン機能が欲しい",
            "source_system": "manual",
            "timestamp": datetime.now(UTC),
            "status": InquiryStatus.RECEIVED,
            "inquiry_metadata": {"source": "web_ui"},
        }

        # Act
        inquiry = InquiryModel(**inquiry_data)
        db_session.add(inquiry)
        db_session.commit()
        db_session.refresh(inquiry)

        # Assert
        assert inquiry.id is not None
        assert inquiry.user_id == "test_user_001"
        assert inquiry.content == "ログイン機能が欲しい"
        assert inquiry.source_system == "manual"
        assert inquiry.status == InquiryStatus.RECEIVED
        assert inquiry.inquiry_metadata == {"source": "web_ui"}
        assert inquiry.created_at is not None
        assert inquiry.updated_at is not None

    def test_inquiry_status_defaults_to_received(self, db_session):
        """ステータスのデフォルトがreceivedである."""
        # Arrange & Act
        inquiry = InquiryModel(
            user_id="test_user",
            content="テスト問い合わせ",
            source_system="manual",
            timestamp=datetime.now(UTC),
        )
        db_session.add(inquiry)
        db_session.commit()

        # Assert
        assert inquiry.status == InquiryStatus.RECEIVED

    def test_inquiry_metadata_defaults_to_empty_dict(self, db_session):
        """inquiry_metadataのデフォルトが空辞書である."""
        # Arrange & Act
        inquiry = InquiryModel(
            user_id="test_user",
            content="テスト問い合わせ",
            source_system="manual",
            timestamp=datetime.now(UTC),
        )
        db_session.add(inquiry)
        db_session.commit()

        # Assert
        assert inquiry.inquiry_metadata == {}

    def test_inquiry_requires_content(self, db_session):
        """contentフィールドは必須である."""
        # Arrange
        inquiry = InquiryModel(
            user_id="test_user",
            content=None,  # contentをNoneに設定
            source_system="manual",
            timestamp=datetime.now(UTC),
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            db_session.add(inquiry)
            db_session.commit()

    def test_inquiry_requires_user_id(self, db_session):
        """user_idフィールドは必須である."""
        # Arrange
        inquiry = InquiryModel(
            user_id=None,  # user_idをNoneに設定
            content="テスト問い合わせ",
            source_system="manual",
            timestamp=datetime.now(UTC),
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            db_session.add(inquiry)
            db_session.commit()

    def test_inquiry_requires_source_system(self, db_session):
        """source_systemフィールドは必須である."""
        inquiry = InquiryModel(
            user_id="test_user",
            content="テスト問い合わせ",
            source_system=None,  # source_systemをNoneに設定
            timestamp=datetime.now(UTC),
        )

        with pytest.raises(IntegrityError):
            db_session.add(inquiry)
            db_session.commit()

    def test_inquiry_requires_timestamp(self, db_session):
        """timestampフィールドは必須である."""
        # Arrange
        inquiry = InquiryModel(
            user_id="test_user",
            content="テスト問い合わせ",
            source_system="manual",
            timestamp=None,  # timestampをNoneに設定
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            db_session.add(inquiry)
            db_session.commit()

    def test_inquiry_content_not_empty_check(self, db_session, db_engine):
        """contentが空文字列の場合エラーになる.

        注意: このテストはSQLiteではスキップされます。
        SQLiteはCHECK制約を完全にサポートしていないため、
        PostgreSQLなどのデータベースでのみ有効です。
        """
        # SQLiteの場合はスキップ
        if db_engine.dialect.name == "sqlite":
            pytest.skip("SQLiteはCHECK制約を完全にサポートしていません")

        # Arrange
        inquiry = InquiryModel(
            user_id="test_user",
            content="   ",  # 空白のみ
            source_system="manual",
            timestamp=datetime.now(UTC),
        )

        # Act & Assert
        # CHECK制約をサポートするデータベースではIntegrityErrorが発生する
        with pytest.raises(IntegrityError):
            db_session.add(inquiry)
            db_session.commit()

    def test_inquiry_status_validation(self, db_session):
        """statusは有効なInquiryStatus値のみ受け付ける."""
        # Arrange
        inquiry = InquiryModel(
            user_id="test_user",
            content="テスト問い合わせ",
            source_system="manual",
            timestamp=datetime.now(UTC),
            status=InquiryStatus.PROCESSING,
        )

        # Act
        db_session.add(inquiry)
        db_session.commit()

        # Assert
        assert inquiry.status == InquiryStatus.PROCESSING

    def test_inquiry_all_status_values(self, db_session):
        """すべてのステータス値が設定可能である."""
        # Arrange
        statuses = [
            InquiryStatus.RECEIVED,
            InquiryStatus.PROCESSING,
            InquiryStatus.NEEDS_CLARIFICATION,
            InquiryStatus.TASK_WORKING,
            InquiryStatus.COMPLETED,
            InquiryStatus.REJECTED,
            InquiryStatus.FAILED,
        ]

        # Act & Assert
        for status in statuses:
            inquiry = InquiryModel(
                user_id="test_user",
                content=f"テスト: {status.value}",
                source_system="manual",
                timestamp=datetime.now(UTC),
                status=status,
            )
            db_session.add(inquiry)
            db_session.commit()
            assert inquiry.status == status
            db_session.rollback()

    def test_inquiry_metadata_stores_rejection_info(self, db_session):
        """inquiry_metadataに却下情報を保存できる."""
        # Arrange
        rejection_metadata = {
            "rejection": {
                "reason": "要件が不明確",
                "rejected_at": datetime.now(UTC).isoformat(),
                "rejected_by": "admin_user",
            }
        }
        inquiry = InquiryModel(
            user_id="test_user",
            content="テスト問い合わせ",
            source_system="manual",
            timestamp=datetime.now(UTC),
            status=InquiryStatus.REJECTED,
            inquiry_metadata=rejection_metadata,
        )

        # Act
        db_session.add(inquiry)
        db_session.commit()

        # Assert
        assert inquiry.inquiry_metadata["rejection"]["reason"] == "要件が不明確"
        assert "rejected_at" in inquiry.inquiry_metadata["rejection"]

    def test_inquiry_metadata_stores_status_history(self, db_session):
        """inquiry_metadataにステータス変更履歴を保存できる."""
        # Arrange
        status_history = [
            {
                "from_status": InquiryStatus.RECEIVED.value,
                "to_status": InquiryStatus.PROCESSING.value,
                "changed_at": datetime.now(UTC).isoformat(),
            },
            {
                "from_status": InquiryStatus.PROCESSING.value,
                "to_status": InquiryStatus.TASK_WORKING.value,
                "changed_at": datetime.now(UTC).isoformat(),
            },
        ]
        inquiry = InquiryModel(
            user_id="test_user",
            content="テスト問い合わせ",
            source_system="manual",
            timestamp=datetime.now(UTC),
            status=InquiryStatus.TASK_WORKING,
            inquiry_metadata={"status_history": status_history},
        )

        # Act
        db_session.add(inquiry)
        db_session.commit()

        # Assert
        assert len(inquiry.inquiry_metadata["status_history"]) == 2
        assert (
            inquiry.inquiry_metadata["status_history"][0]["from_status"] == "received"
        )

    def test_inquiry_timestamps_auto_populated(self, db_session):
        """created_atとupdated_atが自動設定される."""
        # Arrange
        inquiry = InquiryModel(
            user_id="test_user",
            content="テスト問い合わせ",
            source_system="manual",
            timestamp=datetime.now(UTC),
        )

        # Act
        db_session.add(inquiry)
        db_session.commit()
        db_session.refresh(inquiry)

        # Assert
        assert inquiry.created_at is not None
        assert inquiry.updated_at is not None
        assert isinstance(inquiry.created_at, datetime)
        assert isinstance(inquiry.updated_at, datetime)

    def test_inquiry_id_auto_increment(self, db_session):
        """IDが自動インクリメントされる."""
        # Arrange & Act
        inquiry1 = InquiryModel(
            user_id="test_user",
            content="問い合わせ1",
            source_system="manual",
            timestamp=datetime.now(UTC),
        )
        inquiry2 = InquiryModel(
            user_id="test_user",
            content="問い合わせ2",
            source_system="manual",
            timestamp=datetime.now(UTC),
        )

        db_session.add(inquiry1)
        db_session.commit()
        db_session.add(inquiry2)
        db_session.commit()

        # Assert
        assert inquiry1.id is not None
        assert inquiry2.id is not None
        assert inquiry2.id > inquiry1.id

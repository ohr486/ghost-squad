"""InquiryQueryService unit tests.

問い合わせクエリサービスのユニットテストを提供する。
"""
from datetime import datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.database.base import BaseModel
from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus
from services.inquiry_query_service import (InquiryNotFoundError,
                                            InquiryQueryService,
                                            InvalidPaginationError,
                                            ListInquiriesRequest)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    BaseModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestListInquiries:
    """listInquiries method tests."""

    def test_list_inquiries_with_default_pagination(self, db_session: Session):
        """デフォルトページネーション設定でリストを取得できることをテストする."""
        # Arrange - 25件の問い合わせを作成
        for i in range(25):
            inquiry = InquiryModel(
                user_id=f"user_{i}",
                content=f"Test inquiry {i}",
                source_system="manual",
                timestamp=datetime.now(timezone.utc),
                status=InquiryStatus.RECEIVED,
            )
            db_session.add(inquiry)
        db_session.commit()

        service = InquiryQueryService(db_session)
        request = ListInquiriesRequest()

        # Act
        result = service.list_inquiries(request)

        # Assert
        assert len(result["data"]) == 20  # デフォルトlimit
        assert result["meta"]["page"] == 1
        assert result["meta"]["limit"] == 20
        assert result["meta"]["total"] == 25
        assert result["meta"]["has_next"] is True

    def test_list_inquiries_with_custom_pagination(self, db_session: Session):
        """カスタムページネーション設定でリストを取得できることをテストする."""
        # Arrange - 15件の問い合わせを作成
        for i in range(15):
            inquiry = InquiryModel(
                user_id=f"user_{i}",
                content=f"Test inquiry {i}",
                source_system="manual",
                timestamp=datetime.now(timezone.utc),
                status=InquiryStatus.RECEIVED,
            )
            db_session.add(inquiry)
        db_session.commit()

        service = InquiryQueryService(db_session)
        request = ListInquiriesRequest(page=2, limit=5)

        # Act
        result = service.list_inquiries(request)

        # Assert
        assert len(result["data"]) == 5
        assert result["meta"]["page"] == 2
        assert result["meta"]["limit"] == 5
        assert result["meta"]["total"] == 15
        assert result["meta"]["has_next"] is True

    def test_list_inquiries_last_page(self, db_session: Session):
        """最終ページでhas_nextがFalseになることをテストする."""
        # Arrange - 10件の問い合わせを作成
        for i in range(10):
            inquiry = InquiryModel(
                user_id=f"user_{i}",
                content=f"Test inquiry {i}",
                source_system="manual",
                timestamp=datetime.now(timezone.utc),
                status=InquiryStatus.RECEIVED,
            )
            db_session.add(inquiry)
        db_session.commit()

        service = InquiryQueryService(db_session)
        request = ListInquiriesRequest(page=1, limit=20)

        # Act
        result = service.list_inquiries(request)

        # Assert
        assert len(result["data"]) == 10
        assert result["meta"]["has_next"] is False

    def test_list_inquiries_sorted_by_created_at_desc_default(
        self, db_session: Session
    ):
        """デフォルトでcreated_at降順でソートされることをテストする."""
        # Arrange - 3件の問い合わせを順番に作成
        inquiry1 = InquiryModel(
            user_id="user_1",
            content="First inquiry",
            source_system="manual",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        db_session.add(inquiry1)
        db_session.commit()
        db_session.refresh(inquiry1)

        inquiry2 = InquiryModel(
            user_id="user_2",
            content="Second inquiry",
            source_system="manual",
            timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        db_session.add(inquiry2)
        db_session.commit()
        db_session.refresh(inquiry2)

        inquiry3 = InquiryModel(
            user_id="user_3",
            content="Third inquiry",
            source_system="manual",
            timestamp=datetime(2024, 1, 3, tzinfo=timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        db_session.add(inquiry3)
        db_session.commit()
        db_session.refresh(inquiry3)

        service = InquiryQueryService(db_session)
        request = ListInquiriesRequest()

        # Act
        result = service.list_inquiries(request)

        # Assert - created_at降順で並ぶ（後から作成されたものが先）
        # inquiry3が最新、inquiry1が最古
        assert len(result["data"]) == 3
        assert result["data"][0].created_at >= result["data"][1].created_at
        assert result["data"][1].created_at >= result["data"][2].created_at

    def test_list_inquiries_sorted_by_updated_at_asc(self, db_session: Session):
        """updated_at昇順でソートできることをテストする."""
        # Arrange
        inquiry1 = InquiryModel(
            user_id="user_1",
            content="First inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        db_session.add(inquiry1)
        db_session.commit()

        inquiry2 = InquiryModel(
            user_id="user_2",
            content="Second inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        db_session.add(inquiry2)
        db_session.commit()

        service = InquiryQueryService(db_session)
        request = ListInquiriesRequest(sort_by="updated_at", sort_order="asc")

        # Act
        result = service.list_inquiries(request)

        # Assert - 古いものが最初
        assert result["data"][0].id == inquiry1.id
        assert result["data"][1].id == inquiry2.id

    def test_list_inquiries_filter_by_status_single(self, db_session: Session):
        """単一ステータスでフィルタリングできることをテストする."""
        # Arrange
        inquiry1 = InquiryModel(
            user_id="user_1",
            content="Received inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry2 = InquiryModel(
            user_id="user_2",
            content="Completed inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.COMPLETED,
        )
        db_session.add_all([inquiry1, inquiry2])
        db_session.commit()

        service = InquiryQueryService(db_session)
        request = ListInquiriesRequest(status=InquiryStatus.RECEIVED)

        # Act
        result = service.list_inquiries(request)

        # Assert
        assert len(result["data"]) == 1
        assert result["data"][0].status == InquiryStatus.RECEIVED

    def test_list_inquiries_filter_by_status_multiple(self, db_session: Session):
        """複数ステータスでフィルタリングできることをテストする."""
        # Arrange
        inquiry1 = InquiryModel(
            user_id="user_1",
            content="Received inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry2 = InquiryModel(
            user_id="user_2",
            content="Completed inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.COMPLETED,
        )
        inquiry3 = InquiryModel(
            user_id="user_3",
            content="Failed inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.FAILED,
        )
        db_session.add_all([inquiry1, inquiry2, inquiry3])
        db_session.commit()

        service = InquiryQueryService(db_session)
        request = ListInquiriesRequest(
            status=[InquiryStatus.RECEIVED, InquiryStatus.COMPLETED]
        )

        # Act
        result = service.list_inquiries(request)

        # Assert
        assert len(result["data"]) == 2
        assert result["meta"]["total"] == 2

    def test_list_inquiries_filter_by_user_id(self, db_session: Session):
        """user_idでフィルタリングできることをテストする."""
        # Arrange
        inquiry1 = InquiryModel(
            user_id="alice",
            content="Alice's inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry2 = InquiryModel(
            user_id="bob",
            content="Bob's inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry3 = InquiryModel(
            user_id="alice",
            content="Alice's another inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        db_session.add_all([inquiry1, inquiry2, inquiry3])
        db_session.commit()

        service = InquiryQueryService(db_session)
        request = ListInquiriesRequest(user_id="alice")

        # Act
        result = service.list_inquiries(request)

        # Assert
        assert len(result["data"]) == 2
        assert all(inq.user_id == "alice" for inq in result["data"])

    def test_list_inquiries_with_limit_validation(self, db_session: Session):
        """limit範囲外の値がクランプされることをテストする."""
        # Arrange
        for i in range(5):
            inquiry = InquiryModel(
                user_id=f"user_{i}",
                content=f"Test inquiry {i}",
                source_system="manual",
                timestamp=datetime.now(timezone.utc),
                status=InquiryStatus.RECEIVED,
            )
            db_session.add(inquiry)
        db_session.commit()

        service = InquiryQueryService(db_session)

        # Act - limit=0はエラー
        with pytest.raises(InvalidPaginationError) as exc_info:
            service.list_inquiries(ListInquiriesRequest(limit=0))
        assert "limit" in str(exc_info.value).lower()

        # Act - limit=150は100にクランプ
        result = service.list_inquiries(ListInquiriesRequest(limit=150))

        # Assert
        assert result["meta"]["limit"] == 100

    def test_list_inquiries_empty_result(self, db_session: Session):
        """問い合わせが存在しない場合に空のリストを返すことをテストする."""
        # Arrange
        service = InquiryQueryService(db_session)
        request = ListInquiriesRequest()

        # Act
        result = service.list_inquiries(request)

        # Assert
        assert len(result["data"]) == 0
        assert result["meta"]["total"] == 0
        assert result["meta"]["has_next"] is False


class TestGetInquiry:
    """getInquiry method tests."""

    def test_get_inquiry_success(self, db_session: Session):
        """存在する問い合わせを取得できることをテストする."""
        # Arrange
        inquiry = InquiryModel(
            user_id="test_user",
            content="Test inquiry",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        db_session.add(inquiry)
        db_session.commit()

        service = InquiryQueryService(db_session)

        # Act
        result = service.get_inquiry(inquiry.id)

        # Assert
        assert result.id == inquiry.id
        assert result.user_id == "test_user"
        assert result.content == "Test inquiry"

    def test_get_inquiry_not_found(self, db_session: Session):
        """存在しない問い合わせIDでInquiryNotFoundErrorを発生させることをテストする."""
        # Arrange
        service = InquiryQueryService(db_session)

        # Act & Assert
        with pytest.raises(InquiryNotFoundError) as exc_info:
            service.get_inquiry(99999)
        assert "99999" in str(exc_info.value)

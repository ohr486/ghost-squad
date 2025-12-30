"""InquiryRepository unit tests.

TDD implementation for data access layer.
Tests cover CRUD operations, filtering, sorting, and pagination.
"""
from datetime import datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.database.base import BaseModel
from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus
from services.inquiry_repository import (
    CreateInquiryData,
    FindManyOptions,
    InquiryFilter,
    InquiryRepository,
    PaginationOption,
    SortOption,
    UpdateInquiryData,
)


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


@pytest.fixture
def repository(db_session: Session) -> InquiryRepository:
    """Create InquiryRepository instance."""
    return InquiryRepository(db_session)


class TestInquiryRepositoryCreate:
    """Tests for create operation (要件1.1)."""

    def test_create_inquiry_success(
        self, repository: InquiryRepository, db_session: Session
    ) -> None:
        """Test successful inquiry creation."""
        # Arrange
        now = datetime.now(timezone.utc)
        data = CreateInquiryData(
            user_id="test_user",
            content="ログイン機能が欲しい",
            source_system="manual",
            timestamp=now,
            status=InquiryStatus.RECEIVED,
        )

        # Act
        inquiry = repository.create(data)

        # Assert
        assert inquiry.id is not None
        assert inquiry.user_id == "test_user"
        assert inquiry.content == "ログイン機能が欲しい"
        assert inquiry.source_system == "manual"
        # SQLite doesn't preserve timezone, so compare without timezone
        assert inquiry.timestamp.replace(tzinfo=None) == now.replace(tzinfo=None)
        assert inquiry.status == InquiryStatus.RECEIVED
        assert inquiry.created_at is not None
        assert inquiry.updated_at is not None

        # Verify persistence
        db_session.refresh(inquiry)
        assert db_session.query(InquiryModel).count() == 1

    def test_create_inquiry_with_metadata(self, repository: InquiryRepository) -> None:
        """Test inquiry creation with empty metadata."""
        # Arrange
        data = CreateInquiryData(
            user_id="test_user",
            content="テスト内容",
            source_system="email",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )

        # Act
        inquiry = repository.create(data)

        # Assert
        assert inquiry.inquiry_metadata == {}


class TestInquiryRepositoryFindById:
    """Tests for findById operation (要件2.5)."""

    def test_find_by_id_success(self, repository: InquiryRepository) -> None:
        """Test finding inquiry by ID."""
        # Arrange
        data = CreateInquiryData(
            user_id="test_user",
            content="テスト内容",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        created = repository.create(data)

        # Act
        found = repository.find_by_id(created.id)

        # Assert
        assert found is not None
        assert found.id == created.id
        assert found.user_id == "test_user"

    def test_find_by_id_not_found(self, repository: InquiryRepository) -> None:
        """Test finding non-existent inquiry returns None (要件2.6)."""
        # Act
        result = repository.find_by_id(99999)

        # Assert
        assert result is None


class TestInquiryRepositoryFindMany:
    """Tests for findMany operation with filtering, sorting, pagination (要件2.1-2.3)."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, repository: InquiryRepository) -> None:
        """Create test data for each test."""
        # Create 5 inquiries with different statuses and timestamps
        for i in range(5):
            status = (
                InquiryStatus.RECEIVED if i % 2 == 0 else InquiryStatus.TASK_WORKING
            )
            data = CreateInquiryData(
                user_id=f"user_{i}",
                content=f"テスト内容 {i}",
                source_system="manual",
                timestamp=datetime.now(timezone.utc),
                status=status,
            )
            repository.create(data)

    def test_find_many_default_sort(self, repository: InquiryRepository) -> None:
        """Test default sorting by created_at DESC (要件2.3)."""
        # Act
        inquiries = repository.find_many(FindManyOptions())

        # Assert
        assert len(inquiries) == 5
        # Verify descending order by created_at
        for i in range(len(inquiries) - 1):
            assert inquiries[i].created_at >= inquiries[i + 1].created_at

    def test_find_many_with_status_filter(self, repository: InquiryRepository) -> None:
        """Test filtering by single status."""
        # Act
        options = FindManyOptions(filter=InquiryFilter(status=InquiryStatus.RECEIVED))
        inquiries = repository.find_many(options)

        # Assert
        assert len(inquiries) == 3
        for inquiry in inquiries:
            assert inquiry.status == InquiryStatus.RECEIVED

    def test_find_many_with_multiple_statuses(
        self, repository: InquiryRepository
    ) -> None:
        """Test filtering by multiple statuses."""
        # Act
        options = FindManyOptions(
            filter=InquiryFilter(
                status=[InquiryStatus.RECEIVED, InquiryStatus.TASK_WORKING]
            )
        )
        inquiries = repository.find_many(options)

        # Assert
        assert len(inquiries) == 5

    def test_find_many_with_user_id_filter(self, repository: InquiryRepository) -> None:
        """Test filtering by user_id."""
        # Act
        options = FindManyOptions(filter=InquiryFilter(user_id="user_0"))
        inquiries = repository.find_many(options)

        # Assert
        assert len(inquiries) == 1
        assert inquiries[0].user_id == "user_0"

    def test_find_many_with_pagination(self, repository: InquiryRepository) -> None:
        """Test pagination (要件2.1, 2.2)."""
        # Act - Get first page
        options = FindManyOptions(pagination=PaginationOption(page=1, limit=2))
        page1 = repository.find_many(options)

        # Act - Get second page
        options = FindManyOptions(pagination=PaginationOption(page=2, limit=2))
        page2 = repository.find_many(options)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        # Ensure different results
        assert page1[0].id != page2[0].id

    def test_find_many_with_custom_sort(self, repository: InquiryRepository) -> None:
        """Test custom sorting."""
        # Act
        options = FindManyOptions(
            sort=[SortOption(field="created_at", direction="asc")]
        )
        inquiries = repository.find_many(options)

        # Assert
        assert len(inquiries) == 5
        # Verify ascending order
        for i in range(len(inquiries) - 1):
            assert inquiries[i].created_at <= inquiries[i + 1].created_at

    def test_find_many_pagination_limit_validation(
        self, repository: InquiryRepository
    ) -> None:
        """Test pagination limit is clamped to 1-100 range."""
        # Act - Limit above max
        options = FindManyOptions(pagination=PaginationOption(page=1, limit=200))
        inquiries = repository.find_many(options)

        # Assert - Should be clamped to 100 (but we only have 5 items)
        assert len(inquiries) == 5

    def test_find_many_invalid_sort_field(self, repository: InquiryRepository) -> None:
        """Test that invalid sort field raises ValueError."""
        # Act & Assert
        options = FindManyOptions(sort=[SortOption(field="invalid_field")])
        with pytest.raises(ValueError, match="Invalid sort field: invalid_field"):
            repository.find_many(options)

    def test_find_many_pagination_invalid_page_zero(
        self, repository: InquiryRepository
    ) -> None:
        """Test that page=0 is clamped to page=1."""
        # Act
        options = FindManyOptions(pagination=PaginationOption(page=0, limit=2))
        inquiries = repository.find_many(options)

        # Assert - Should behave like page=1
        assert len(inquiries) == 2

    def test_find_many_pagination_invalid_page_negative(
        self, repository: InquiryRepository
    ) -> None:
        """Test that negative page is clamped to page=1."""
        # Act
        options = FindManyOptions(pagination=PaginationOption(page=-1, limit=2))
        inquiries = repository.find_many(options)

        # Assert - Should behave like page=1
        assert len(inquiries) == 2


class TestInquiryRepositoryCount:
    """Tests for count operation."""

    def test_count_all(self, repository: InquiryRepository) -> None:
        """Test counting all inquiries."""
        # Arrange
        for i in range(3):
            data = CreateInquiryData(
                user_id=f"user_{i}",
                content=f"テスト {i}",
                source_system="manual",
                timestamp=datetime.now(timezone.utc),
                status=InquiryStatus.RECEIVED,
            )
            repository.create(data)

        # Act
        count = repository.count(InquiryFilter())

        # Assert
        assert count == 3

    def test_count_with_filter(self, repository: InquiryRepository) -> None:
        """Test counting with filter."""
        # Arrange
        for i in range(3):
            status = InquiryStatus.RECEIVED if i < 2 else InquiryStatus.TASK_WORKING
            data = CreateInquiryData(
                user_id=f"user_{i}",
                content=f"テスト {i}",
                source_system="manual",
                timestamp=datetime.now(timezone.utc),
                status=status,
            )
            repository.create(data)

        # Act
        count = repository.count(InquiryFilter(status=InquiryStatus.RECEIVED))

        # Assert
        assert count == 2


class TestInquiryRepositoryUpdate:
    """Tests for update operation (要件2.8, 2.9)."""

    def test_update_inquiry_content(self, repository: InquiryRepository) -> None:
        """Test updating inquiry content."""
        # Arrange
        data = CreateInquiryData(
            user_id="test_user",
            content="元の内容",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry = repository.create(data)
        original_updated_at = inquiry.updated_at

        # Act
        update_data = UpdateInquiryData(content="更新された内容")
        updated = repository.update(inquiry.id, update_data)

        # Assert
        assert updated.content == "更新された内容"
        assert updated.source_system == "manual"  # Unchanged
        assert updated.updated_at > original_updated_at  # 要件2.9

    def test_update_inquiry_source_system(self, repository: InquiryRepository) -> None:
        """Test updating source_system."""
        # Arrange
        data = CreateInquiryData(
            user_id="test_user",
            content="テスト内容",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry = repository.create(data)

        # Act
        update_data = UpdateInquiryData(source_system="email")
        updated = repository.update(inquiry.id, update_data)

        # Assert
        assert updated.source_system == "email"
        assert updated.content == "テスト内容"  # Unchanged

    def test_update_both_fields(self, repository: InquiryRepository) -> None:
        """Test updating both content and source_system."""
        # Arrange
        data = CreateInquiryData(
            user_id="test_user",
            content="元の内容",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry = repository.create(data)

        # Act
        update_data = UpdateInquiryData(content="新しい内容", source_system="chat")
        updated = repository.update(inquiry.id, update_data)

        # Assert
        assert updated.content == "新しい内容"
        assert updated.source_system == "chat"

    def test_update_inquiry_not_found(self, repository: InquiryRepository) -> None:
        """Test that updating non-existent inquiry raises ValueError."""
        # Arrange
        update_data = UpdateInquiryData(content="新しい内容")

        # Act & Assert
        with pytest.raises(ValueError, match="Inquiry with id 99999 not found"):
            repository.update(99999, update_data)

    def test_update_inquiry_no_fields(self, repository: InquiryRepository) -> None:
        """Test updating with no fields (both None) still updates updated_at."""
        # Arrange
        data = CreateInquiryData(
            user_id="test_user",
            content="元の内容",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry = repository.create(data)
        original_updated_at = inquiry.updated_at
        original_content = inquiry.content
        original_source = inquiry.source_system

        # Act
        update_data = UpdateInquiryData()  # Both fields are None
        updated = repository.update(inquiry.id, update_data)

        # Assert
        assert updated.content == original_content  # Unchanged
        assert updated.source_system == original_source  # Unchanged
        assert updated.updated_at > original_updated_at  # updated_at is still updated


class TestInquiryRepositoryUpdateStatus:
    """Tests for updateStatus operation (要件3.1, 3.2)."""

    def test_update_status(self, repository: InquiryRepository) -> None:
        """Test updating inquiry status."""
        # Arrange
        data = CreateInquiryData(
            user_id="test_user",
            content="テスト内容",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry = repository.create(data)
        original_updated_at = inquiry.updated_at

        # Act
        updated = repository.update_status(inquiry.id, InquiryStatus.TASK_WORKING)

        # Assert
        assert updated.status == InquiryStatus.TASK_WORKING
        assert updated.updated_at > original_updated_at  # 要件3.2

    def test_update_status_not_found(self, repository: InquiryRepository) -> None:
        """Test that updating status of non-existent inquiry raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Inquiry with id 99999 not found"):
            repository.update_status(99999, InquiryStatus.TASK_WORKING)

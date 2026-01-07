"""StoryRepository unit tests.

TDD implementation for story data access layer.
Tests cover CRUD operations, filtering, sorting, and pagination.
"""
import time
from datetime import datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from models.database.base import BaseModel
from models.database.inquiry import InquiryModel
from models.database.story import StoryModel
from models.enums.inquiry_status import InquiryStatus
from models.enums.priority import Priority
from models.enums.story_status import StoryStatus
from services.story_repository import (CreateStoryData, FindManyOptions,
                                       PaginationOption, SortOption,
                                       StoryFilter, StoryRepository,
                                       UpdateStoryData)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    BaseModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def repository(db_session: Session) -> StoryRepository:
    """Create StoryRepository instance."""
    return StoryRepository(db_session)


@pytest.fixture
def sample_inquiry(db_session: Session) -> InquiryModel:
    """Create sample inquiry for testing."""
    inquiry = InquiryModel(
        user_id="test_user",
        content="ログイン機能が欲しい",
        source_system="manual",
        timestamp=datetime.now(timezone.utc),
        status=InquiryStatus.TASK_WORKING,
        inquiry_metadata={},
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return inquiry


class TestStoryRepositoryCreate:
    """Tests for create operation (要件2.1, 4.1, 4.2)."""

    def test_create_story_success(
        self,
        repository: StoryRepository,
        db_session: Session,
        sample_inquiry: InquiryModel,
    ) -> None:
        """Test successful story creation."""
        # Arrange
        data = CreateStoryData(
            inquiry_id=sample_inquiry.id,
            title="ユーザー認証機能の実装",
            description="ユーザーがログインできる機能を実装する",
            priority=Priority.HIGH,
            estimated_effort=5.0,
        )

        # Act
        story = repository.create(data)

        # Assert
        assert story.id is not None
        assert story.inquiry_id == sample_inquiry.id
        assert story.title == "ユーザー認証機能の実装"
        assert story.description == "ユーザーがログインできる機能を実装する"
        assert story.priority == Priority.HIGH
        assert story.status == StoryStatus.WAITING_REVIEW
        assert story.estimated_effort == 5.0
        assert story.created_at is not None
        assert story.updated_at is not None

        # Verify persistence
        db_session.refresh(story)
        assert db_session.query(StoryModel).count() == 1

    def test_create_story_with_optional_fields(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test story creation with optional fields."""
        # Arrange
        deadline = datetime.now(timezone.utc)
        data = CreateStoryData(
            inquiry_id=sample_inquiry.id,
            title="API開発",
            description="REST API を実装する",
            priority=Priority.MEDIUM,
            estimated_effort=3.0,
            deadline=deadline,
            assignee="developer1",
        )

        # Act
        story = repository.create(data)

        # Assert
        assert story.deadline is not None
        assert story.assignee == "developer1"

    def test_create_story_with_default_status(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test story creation has default status waiting_review."""
        # Arrange
        data = CreateStoryData(
            inquiry_id=sample_inquiry.id,
            title="テストタイトル",
            description="テスト説明",
            priority=Priority.LOW,
        )

        # Act
        story = repository.create(data)

        # Assert
        assert story.status == StoryStatus.WAITING_REVIEW

    def test_create_story_invalid_inquiry_id(
        self, repository: StoryRepository, db_session: Session
    ) -> None:
        """Test story creation with invalid inquiry_id raises error."""
        # Arrange
        data = CreateStoryData(
            inquiry_id=99999,  # Non-existent inquiry
            title="テスト",
            description="テスト説明",
            priority=Priority.LOW,
        )

        # Act & Assert
        # Note: SQLite with foreign_keys=ON will raise IntegrityError
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            repository.create(data)
            db_session.flush()  # Force constraint check


class TestStoryRepositoryFindById:
    """Tests for findById operation (要件2.5)."""

    def test_find_by_id_success(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test finding story by ID."""
        # Arrange
        data = CreateStoryData(
            inquiry_id=sample_inquiry.id,
            title="テストストーリー",
            description="テスト説明",
            priority=Priority.MEDIUM,
        )
        story = repository.create(data)

        # Act
        found = repository.find_by_id(story.id)

        # Assert
        assert found is not None
        assert found.id == story.id
        assert found.title == "テストストーリー"

    def test_find_by_id_not_found(self, repository: StoryRepository) -> None:
        """Test finding non-existent story returns None."""
        # Act
        found = repository.find_by_id(99999)

        # Assert
        assert found is None


class TestStoryRepositoryFindMany:
    """Tests for findMany operation with filtering, sorting, pagination."""

    def test_find_many_no_filters(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test finding all stories without filters."""
        # Arrange
        for i in range(3):
            data = CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title=f"ストーリー {i}",
                description=f"説明 {i}",
                priority=Priority.MEDIUM,
            )
            repository.create(data)

        # Act
        stories = repository.find_many(FindManyOptions())

        # Assert
        assert len(stories) == 3

    def test_find_many_filter_by_status(
        self,
        repository: StoryRepository,
        sample_inquiry: InquiryModel,
        db_session: Session,
    ) -> None:
        """Test filtering stories by status."""
        # Arrange
        story1 = repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="ストーリー1",
                description="説明1",
                priority=Priority.HIGH,
            )
        )
        story2 = repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="ストーリー2",
                description="説明2",
                priority=Priority.LOW,
            )
        )

        # Update story2 to approved
        story2.status = StoryStatus.APPROVED
        db_session.commit()

        # Act
        waiting_stories = repository.find_many(
            FindManyOptions(filter=StoryFilter(status=StoryStatus.WAITING_REVIEW))
        )

        # Assert
        assert len(waiting_stories) == 1
        assert waiting_stories[0].id == story1.id

    def test_find_many_filter_by_priority(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test filtering stories by priority."""
        # Arrange
        repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="高優先度",
                description="説明",
                priority=Priority.HIGH,
            )
        )
        repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="低優先度",
                description="説明",
                priority=Priority.LOW,
            )
        )

        # Act
        high_priority = repository.find_many(
            FindManyOptions(filter=StoryFilter(priority=Priority.HIGH))
        )

        # Assert
        assert len(high_priority) == 1
        assert high_priority[0].priority == Priority.HIGH

    def test_find_many_filter_by_inquiry_id(
        self, repository: StoryRepository, db_session: Session
    ) -> None:
        """Test filtering stories by inquiry_id."""
        # Arrange
        inquiry1 = InquiryModel(
            user_id="user1",
            content="問い合わせ1",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
            inquiry_metadata={},
        )
        inquiry2 = InquiryModel(
            user_id="user2",
            content="問い合わせ2",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
            inquiry_metadata={},
        )
        db_session.add_all([inquiry1, inquiry2])
        db_session.commit()

        repository.create(
            CreateStoryData(
                inquiry_id=inquiry1.id,
                title="ストーリー1",
                description="説明1",
                priority=Priority.MEDIUM,
            )
        )
        repository.create(
            CreateStoryData(
                inquiry_id=inquiry2.id,
                title="ストーリー2",
                description="説明2",
                priority=Priority.MEDIUM,
            )
        )

        # Act
        inquiry1_stories = repository.find_many(
            FindManyOptions(filter=StoryFilter(inquiry_id=inquiry1.id))
        )

        # Assert
        assert len(inquiry1_stories) == 1
        assert inquiry1_stories[0].inquiry_id == inquiry1.id

    def test_find_many_sort_by_created_at(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test sorting stories by created_at."""
        # Arrange
        repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="古いストーリー",
                description="説明",
                priority=Priority.MEDIUM,
            )
        )
        # Sufficient delay to ensure different timestamps
        time.sleep(0.1)
        repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="新しいストーリー",
                description="説明",
                priority=Priority.MEDIUM,
            )
        )

        # Act - Descending order (default)
        stories_desc = repository.find_many(
            FindManyOptions(sort=[SortOption(field="created_at", direction="desc")])
        )

        # Assert - Most recent first
        assert len(stories_desc) == 2
        assert stories_desc[0].created_at >= stories_desc[1].created_at

        # Act - Ascending order
        stories_asc = repository.find_many(
            FindManyOptions(sort=[SortOption(field="created_at", direction="asc")])
        )

        # Assert - Oldest first
        assert len(stories_asc) == 2
        assert stories_asc[0].created_at <= stories_asc[1].created_at

    def test_find_many_pagination(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test pagination."""
        # Arrange
        for i in range(5):
            repository.create(
                CreateStoryData(
                    inquiry_id=sample_inquiry.id,
                    title=f"ストーリー {i}",
                    description=f"説明 {i}",
                    priority=Priority.MEDIUM,
                )
            )

        # Act - Page 1
        page1 = repository.find_many(
            FindManyOptions(pagination=PaginationOption(page=1, limit=2))
        )

        # Assert
        assert len(page1) == 2

        # Act - Page 2
        page2 = repository.find_many(
            FindManyOptions(pagination=PaginationOption(page=2, limit=2))
        )

        # Assert
        assert len(page2) == 2
        assert page1[0].id != page2[0].id


class TestStoryRepositoryCount:
    """Tests for count operation."""

    def test_count_all_stories(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test counting all stories."""
        # Arrange
        for i in range(3):
            repository.create(
                CreateStoryData(
                    inquiry_id=sample_inquiry.id,
                    title=f"ストーリー {i}",
                    description=f"説明 {i}",
                    priority=Priority.MEDIUM,
                )
            )

        # Act
        count = repository.count(StoryFilter())

        # Assert
        assert count == 3

    def test_count_filtered_stories(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test counting filtered stories."""
        # Arrange
        repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="高優先度",
                description="説明",
                priority=Priority.HIGH,
            )
        )
        repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="低優先度",
                description="説明",
                priority=Priority.LOW,
            )
        )

        # Act
        count = repository.count(StoryFilter(priority=Priority.HIGH))

        # Assert
        assert count == 1


class TestStoryRepositoryUpdate:
    """Tests for update operation (要件2.6, 2.7, 2.8)."""

    def test_update_story_success(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test updating story."""
        # Arrange
        story = repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="元のタイトル",
                description="元の説明",
                priority=Priority.LOW,
            )
        )
        original_updated_at = story.updated_at

        # Act
        updated = repository.update(
            story.id,
            UpdateStoryData(
                title="新しいタイトル",
                description="新しい説明",
                priority=Priority.HIGH,
            ),
        )

        # Assert
        assert updated.id == story.id
        assert updated.title == "新しいタイトル"
        assert updated.description == "新しい説明"
        assert updated.priority == Priority.HIGH
        assert updated.updated_at > original_updated_at

    def test_update_story_partial(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test partial update."""
        # Arrange
        story = repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="元のタイトル",
                description="元の説明",
                priority=Priority.LOW,
            )
        )

        # Act
        updated = repository.update(story.id, UpdateStoryData(title="新しいタイトル"))

        # Assert
        assert updated.title == "新しいタイトル"
        assert updated.description == "元の説明"

    def test_update_story_not_found(self, repository: StoryRepository) -> None:
        """Test updating non-existent story raises error."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            repository.update(99999, UpdateStoryData(title="新しいタイトル"))

        assert "Story with id 99999 not found" in str(exc_info.value)


class TestStoryRepositoryDelete:
    """Tests for delete operation (要件2.15, 2.17)."""

    def test_delete_story_success(
        self, repository: StoryRepository, sample_inquiry: InquiryModel
    ) -> None:
        """Test deleting story."""
        # Arrange
        story = repository.create(
            CreateStoryData(
                inquiry_id=sample_inquiry.id,
                title="削除するストーリー",
                description="説明",
                priority=Priority.MEDIUM,
            )
        )

        # Act
        repository.delete(story.id)

        # Assert
        assert repository.find_by_id(story.id) is None

    def test_delete_story_not_found(self, repository: StoryRepository) -> None:
        """Test deleting non-existent story raises error."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            repository.delete(99999)

        assert "Story with id 99999 not found" in str(exc_info.value)


class TestStoryRepositoryForeignKeyConstraint:
    """Tests for foreign key constraint (要件4.4)."""

    def test_cascade_delete_on_inquiry_deletion(
        self, repository: StoryRepository, db_session: Session
    ) -> None:
        """Test cascade delete when inquiry is deleted."""
        # Arrange
        inquiry = InquiryModel(
            user_id="test_user",
            content="テスト問い合わせ",
            source_system="manual",
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.TASK_WORKING,
            inquiry_metadata={},
        )
        db_session.add(inquiry)
        db_session.commit()
        db_session.refresh(inquiry)

        story = repository.create(
            CreateStoryData(
                inquiry_id=inquiry.id,
                title="関連ストーリー",
                description="説明",
                priority=Priority.MEDIUM,
            )
        )
        story_id = story.id

        # Act - Delete inquiry
        db_session.delete(inquiry)
        db_session.commit()
        db_session.expire_all()  # Clear session cache

        # Assert - Story should be cascade deleted
        # Use fresh query to avoid ObjectDeletedError
        deleted_story = (
            db_session.query(StoryModel).filter(StoryModel.id == story_id).first()
        )
        assert deleted_story is None

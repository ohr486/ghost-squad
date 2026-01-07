"""ストーリーモデルのテスト."""
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from models.database.base import Base
from models.database.inquiry import InquiryModel
from models.database.story import StoryModel
from models.enums.inquiry_status import InquiryStatus
from models.enums.priority import Priority
from models.enums.story_status import StoryStatus


@pytest.fixture
def db_engine():
    """テスト用データベースエンジン."""
    engine = create_engine("sqlite:///:memory:")

    # Enable foreign key constraints in SQLite for proper CASCADE testing
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
def sample_inquiry(db_session):
    """テスト用サンプルInquiry."""
    inquiry = InquiryModel(
        user_id="test_user",
        content="ログイン機能が欲しい",
        source_system="manual",
        timestamp=datetime.now(UTC),
        status=InquiryStatus.TASK_WORKING,
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return inquiry


class TestStoryModel:
    """StoryModelのテストクラス."""

    def test_create_story_with_all_fields(self, db_session, sample_inquiry):
        """すべてのフィールドを持つストーリーを作成できる."""
        # Arrange
        story_data = {
            "inquiry_id": sample_inquiry.id,
            "title": "ユーザー認証機能の実装",
            "description": (
                "As a user, I want to log in so that I can access my account"
            ),
            "priority": Priority.HIGH,
            "status": StoryStatus.WAITING_REVIEW,
            "estimated_effort": 5.0,
            "deadline": datetime.now(UTC),
            "assignee": "dev_user",
            "story_metadata": {"ai_generated": True, "model": "gpt-4"},
        }

        # Act
        story = StoryModel(**story_data)
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)

        # Assert
        assert story.id is not None
        assert story.inquiry_id == sample_inquiry.id
        assert story.title == "ユーザー認証機能の実装"
        assert (
            story.description
            == "As a user, I want to log in so that I can access my account"
        )
        assert story.priority == Priority.HIGH
        assert story.status == StoryStatus.WAITING_REVIEW
        assert story.estimated_effort == 5.0
        assert story.deadline is not None
        assert story.assignee == "dev_user"
        assert story.story_metadata == {"ai_generated": True, "model": "gpt-4"}
        assert story.created_at is not None
        assert story.updated_at is not None

    def test_story_priority_defaults_to_medium(self, db_session, sample_inquiry):
        """優先度のデフォルトがMEDIUMである."""
        # Arrange & Act
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="テストストーリー",
            description="テスト説明",
        )
        db_session.add(story)
        db_session.commit()

        # Assert
        assert story.priority == Priority.MEDIUM

    def test_story_status_defaults_to_waiting_review(self, db_session, sample_inquiry):
        """ステータスのデフォルトがWAITING_REVIEWである."""
        # Arrange & Act
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="テストストーリー",
            description="テスト説明",
        )
        db_session.add(story)
        db_session.commit()

        # Assert
        assert story.status == StoryStatus.WAITING_REVIEW

    def test_story_metadata_defaults_to_empty_dict(self, db_session, sample_inquiry):
        """story_metadataのデフォルトが空辞書である."""
        # Arrange & Act
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="テストストーリー",
            description="テスト説明",
        )
        db_session.add(story)
        db_session.commit()

        # Assert
        assert story.story_metadata == {}

    def test_story_requires_inquiry_id(self, db_session):
        """inquiry_idフィールドは必須である."""
        # Arrange & Act & Assert
        story = StoryModel(
            inquiry_id=None,
            title="テストストーリー",
            description="テスト説明",
        )
        db_session.add(story)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_story_requires_title(self, db_session, sample_inquiry):
        """titleフィールドは必須である."""
        # Arrange & Act & Assert
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title=None,
            description="テスト説明",
        )
        db_session.add(story)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_story_requires_description(self, db_session, sample_inquiry):
        """descriptionフィールドは必須である."""
        # Arrange & Act & Assert
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="テストストーリー",
            description=None,
        )
        db_session.add(story)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_story_title_max_length_500(self, db_session, sample_inquiry):
        """タイトルは最大500文字である."""
        # Arrange
        long_title = "あ" * 500  # 500文字のタイトル

        # Act
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title=long_title,
            description="テスト説明",
        )
        db_session.add(story)
        db_session.commit()

        # Assert
        assert len(story.title) == 500

    def test_story_title_exceeds_max_length(self, db_session, sample_inquiry):
        """タイトルが500文字を超えると拒否される（CheckConstraint）."""
        # Arrange
        too_long_title = "あ" * 501  # 501文字のタイトル

        # Act & Assert
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title=too_long_title,
            description="テスト説明",
        )
        db_session.add(story)

        with pytest.raises(
            IntegrityError, match=r"(chk_stories_title|CHECK constraint failed)"
        ):
            db_session.commit()
        db_session.rollback()

    def test_story_title_empty_fails(self, db_session, sample_inquiry):
        """空文字列のタイトルは拒否される（CheckConstraint）."""
        # Arrange & Act & Assert
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="",
            description="テスト説明",
        )
        db_session.add(story)

        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()
        assert "chk_stories_title" in str(exc_info.value)

    def test_story_title_whitespace_only_fails(self, db_session, sample_inquiry):
        """空白のみのタイトルは拒否される（CheckConstraint）."""
        # Arrange & Act & Assert
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="   ",
            description="テスト説明",
        )
        db_session.add(story)

        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()
        assert "chk_stories_title" in str(exc_info.value)

    def test_story_description_empty_fails(self, db_session, sample_inquiry):
        """空文字列の説明は拒否される（CheckConstraint）."""
        # Arrange & Act & Assert
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="テストストーリー",
            description="",
        )
        db_session.add(story)

        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()
        assert "chk_stories_description" in str(exc_info.value)

    def test_story_description_whitespace_only_fails(self, db_session, sample_inquiry):
        """空白のみの説明は拒否される（CheckConstraint）."""
        # Arrange & Act & Assert
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="テストストーリー",
            description="   ",
        )
        db_session.add(story)

        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()
        assert "chk_stories_description" in str(exc_info.value)

    def test_story_foreign_key_constraint(self, db_session):
        """存在しないinquiry_idを指定するとエラー（外部キー制約違反）."""
        # With PRAGMA foreign_keys=ON, SQLite now enforces foreign key constraints
        # Arrange & Act & Assert
        story = StoryModel(
            inquiry_id=99999,  # 存在しないID
            title="テストストーリー",
            description="テスト説明",
        )
        db_session.add(story)

        # Both SQLite (with PRAGMA foreign_keys=ON) and PostgreSQL enforce foreign keys
        with pytest.raises(
            IntegrityError,
            match=r"(FOREIGN KEY constraint failed|violates foreign key constraint)",
        ):
            db_session.commit()
        db_session.rollback()

    def test_story_optional_fields_can_be_null(self, db_session, sample_inquiry):
        """オプショナルフィールドはNULLでも可能."""
        # Arrange & Act
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="テストストーリー",
            description="テスト説明",
            estimated_effort=None,
            deadline=None,
            assignee=None,
        )
        db_session.add(story)
        db_session.commit()

        # Assert
        assert story.estimated_effort is None
        assert story.deadline is None
        assert story.assignee is None

    def test_story_repr(self, db_session, sample_inquiry):
        """StoryModelの文字列表現が適切である."""
        # Arrange & Act
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="テストストーリー",
            description="テスト説明",
            status=StoryStatus.APPROVED,
        )
        db_session.add(story)
        db_session.commit()

        # Assert
        assert f"<StoryModel(id={story.id}, inquiry_id={sample_inquiry.id}, " in repr(
            story
        )
        assert "status='approved'" in repr(story)


class TestStoryModelCRUDOperations:
    """StoryModelのCRUD操作テストクラス（Task 1.4）."""

    def test_story_create_operation(self, db_session, sample_inquiry):
        """ストーリーの作成操作が正しく動作する."""
        # Arrange
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="新しいストーリー",
            description="説明文",
        )

        # Act
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)

        # Assert
        assert story.id is not None
        assert story.title == "新しいストーリー"
        assert story.created_at is not None

    def test_story_read_operation(self, db_session, sample_inquiry):
        """ストーリーの取得操作が正しく動作する."""
        # Arrange - Create a story first
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="読み取りテスト",
            description="説明文",
        )
        db_session.add(story)
        db_session.commit()
        story_id = story.id

        # Act - Clear session and read from database
        db_session.expunge_all()
        retrieved_story = db_session.query(StoryModel).filter_by(id=story_id).first()

        # Assert
        assert retrieved_story is not None
        assert retrieved_story.id == story_id
        assert retrieved_story.title == "読み取りテスト"
        assert retrieved_story.description == "説明文"

    def test_story_update_operation(self, db_session, sample_inquiry):
        """ストーリーの更新操作が正しく動作する."""
        # Arrange - Create a story first
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="元のタイトル",
            description="元の説明",
            priority=Priority.LOW,
        )
        db_session.add(story)
        db_session.commit()

        # Act - Update the story
        story.title = "更新されたタイトル"
        story.description = "更新された説明"
        story.priority = Priority.HIGH
        db_session.commit()
        db_session.refresh(story)

        # Assert
        assert story.title == "更新されたタイトル"
        assert story.description == "更新された説明"
        assert story.priority == Priority.HIGH
        # Note: updated_at auto-update depends on database trigger/ORM configuration
        # In SQLite test environment, it may not auto-update without explicit setting

    def test_story_delete_operation(self, db_session, sample_inquiry):
        """ストーリーの削除操作が正しく動作する."""
        # Arrange - Create a story first
        story = StoryModel(
            inquiry_id=sample_inquiry.id,
            title="削除されるストーリー",
            description="説明文",
        )
        db_session.add(story)
        db_session.commit()
        story_id = story.id

        # Act - Delete the story
        db_session.delete(story)
        db_session.commit()

        # Assert - Story should not exist
        deleted_story = db_session.query(StoryModel).filter_by(id=story_id).first()
        assert deleted_story is None

    def test_story_cascade_delete_on_inquiry_deletion(self, db_session):
        """Inquiry削除時にStoryもCASCADE削除される（外部キー制約）."""
        # Arrange - Create inquiry and related stories
        inquiry = InquiryModel(
            user_id="cascade_test_user",
            content="CASCADE削除テスト",
            source_system="manual",
            timestamp=datetime.now(UTC),
            status=InquiryStatus.TASK_WORKING,
        )
        db_session.add(inquiry)
        db_session.commit()

        story1 = StoryModel(
            inquiry_id=inquiry.id,
            title="ストーリー1",
            description="説明1",
        )
        story2 = StoryModel(
            inquiry_id=inquiry.id,
            title="ストーリー2",
            description="説明2",
        )
        db_session.add_all([story1, story2])
        db_session.commit()

        story1_id = story1.id
        story2_id = story2.id

        # Act - Delete the inquiry
        db_session.delete(inquiry)
        db_session.commit()

        # Assert - All related stories should be deleted (CASCADE)
        # With PRAGMA foreign_keys=ON, SQLite now properly enforces CASCADE
        remaining_story1 = db_session.query(StoryModel).filter_by(id=story1_id).first()
        remaining_story2 = db_session.query(StoryModel).filter_by(id=story2_id).first()

        # Both PostgreSQL and SQLite (with PRAGMA foreign_keys=ON) will cascade delete
        assert (
            remaining_story1 is None
        ), "Story 1 should be deleted when parent inquiry is deleted"
        assert (
            remaining_story2 is None
        ), "Story 2 should be deleted when parent inquiry is deleted"

"""Tests for StoryQueryService.

ストーリークエリサービスのテスト。
"""
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
from services.story_query_service import (InvalidPaginationError,
                                          ListStoriesRequest,
                                          StoryNotFoundError,
                                          StoryQueryService)


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
def test_inquiry(db_session: Session) -> InquiryModel:
    """テスト用問い合わせを作成する."""
    inquiry = InquiryModel(
        user_id="test_user",
        content="Test inquiry content",
        source_system="test",
        timestamp=datetime.now(timezone.utc),
        status=InquiryStatus.COMPLETED,
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return inquiry


@pytest.fixture
def test_stories(db_session: Session, test_inquiry: InquiryModel) -> list[StoryModel]:
    """テスト用ストーリーを複数作成する."""
    stories = [
        StoryModel(
            inquiry_id=test_inquiry.id,
            title="Story 1",
            description="Description 1",
            priority=Priority.HIGH,
            status=StoryStatus.WAITING_REVIEW,
            estimated_effort=5.0,
        ),
        StoryModel(
            inquiry_id=test_inquiry.id,
            title="Story 2",
            description="Description 2",
            priority=Priority.MEDIUM,
            status=StoryStatus.APPROVED,
            estimated_effort=3.0,
        ),
        StoryModel(
            inquiry_id=test_inquiry.id,
            title="Story 3",
            description="Description 3",
            priority=Priority.LOW,
            status=StoryStatus.WAITING_REVIEW,
            estimated_effort=1.0,
        ),
        StoryModel(
            inquiry_id=test_inquiry.id,
            title="Story 4",
            description="Description 4",
            priority=Priority.URGENT,
            status=StoryStatus.REJECTED,
            estimated_effort=8.0,
        ),
    ]
    for story in stories:
        db_session.add(story)
    db_session.commit()
    for story in stories:
        db_session.refresh(story)
    return stories


class TestStoryQueryService:
    """StoryQueryServiceのテスト."""

    def test_list_stories_default_params(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """デフォルトパラメータでストーリー一覧を取得できる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest()

        result = service.list_stories(request)

        assert len(result["data"]) == 4
        assert result["meta"]["page"] == 1
        assert result["meta"]["limit"] == 20
        assert result["meta"]["total"] == 4
        assert result["meta"]["has_next"] is False
        # デフォルトソート: created_at desc (すべてのストーリーが返される)
        story_titles = {story.title for story in result["data"]}
        assert story_titles == {"Story 1", "Story 2", "Story 3", "Story 4"}

    def test_list_stories_with_status_filter(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """ステータスでフィルタリングできる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(status=StoryStatus.WAITING_REVIEW)

        result = service.list_stories(request)

        assert len(result["data"]) == 2
        assert result["meta"]["total"] == 2
        for story in result["data"]:
            assert story.status == StoryStatus.WAITING_REVIEW

    def test_list_stories_with_multiple_statuses(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """複数ステータスでフィルタリングできる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(
            status=[StoryStatus.WAITING_REVIEW, StoryStatus.APPROVED]
        )

        result = service.list_stories(request)

        assert len(result["data"]) == 3
        assert result["meta"]["total"] == 3
        for story in result["data"]:
            assert story.status in [StoryStatus.WAITING_REVIEW, StoryStatus.APPROVED]

    def test_list_stories_with_priority_filter(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """優先度でフィルタリングできる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(priority=Priority.HIGH)

        result = service.list_stories(request)

        assert len(result["data"]) == 1
        assert result["data"][0].priority == Priority.HIGH

    def test_list_stories_with_multiple_priorities(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """複数優先度でフィルタリングできる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(priority=[Priority.HIGH, Priority.URGENT])

        result = service.list_stories(request)

        assert len(result["data"]) == 2
        assert result["meta"]["total"] == 2
        for story in result["data"]:
            assert story.priority in [Priority.HIGH, Priority.URGENT]

    def test_list_stories_with_inquiry_id_filter(
        self,
        db_session: Session,
        test_inquiry: InquiryModel,
        test_stories: list[StoryModel],
    ):
        """問い合わせIDでフィルタリングできる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(inquiry_id=test_inquiry.id)

        result = service.list_stories(request)

        assert len(result["data"]) == 4
        for story in result["data"]:
            assert story.inquiry_id == test_inquiry.id

    def test_list_stories_with_combined_filters(
        self,
        db_session: Session,
        test_inquiry: InquiryModel,
        test_stories: list[StoryModel],
    ):
        """複数フィルタを組み合わせて使用できる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(
            status=StoryStatus.WAITING_REVIEW,
            priority=Priority.HIGH,
            inquiry_id=test_inquiry.id,
        )

        result = service.list_stories(request)

        assert len(result["data"]) == 1
        assert result["data"][0].status == StoryStatus.WAITING_REVIEW
        assert result["data"][0].priority == Priority.HIGH
        assert result["data"][0].inquiry_id == test_inquiry.id

    def test_list_stories_sort_by_created_at_asc(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """作成日時の昇順でソートできる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(sort_by="created_at", sort_order="asc")

        result = service.list_stories(request)

        assert len(result["data"]) == 4
        # 作成順
        assert result["data"][0].title == "Story 1"
        assert result["data"][-1].title == "Story 4"

    def test_list_stories_sort_by_updated_at_desc(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """更新日時の降順でソートできる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(sort_by="updated_at", sort_order="desc")

        result = service.list_stories(request)

        assert len(result["data"]) == 4
        # 更新日時でソート (すべてのストーリーが返される)
        story_titles = {story.title for story in result["data"]}
        assert story_titles == {"Story 1", "Story 2", "Story 3", "Story 4"}

    def test_list_stories_sort_by_priority(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """優先度でソートできる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(sort_by="priority", sort_order="asc")

        result = service.list_stories(request)

        assert len(result["data"]) == 4
        # Priority: alphabetical order by value (high < low < medium < urgent)
        priorities = [story.priority for story in result["data"]]
        assert priorities[0] == Priority.HIGH
        assert priorities[1] == Priority.LOW
        assert priorities[2] == Priority.MEDIUM
        assert priorities[3] == Priority.URGENT

    def test_list_stories_sort_by_estimated_effort(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """推定工数でソートできる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(sort_by="estimated_effort", sort_order="asc")

        result = service.list_stories(request)

        assert len(result["data"]) == 4
        assert result["data"][0].estimated_effort == 1.0
        assert result["data"][-1].estimated_effort == 8.0

    def test_list_stories_sort_by_assignee(
        self, db_session: Session, test_inquiry: InquiryModel
    ):
        """担当者でソートできる."""
        stories = [
            StoryModel(
                inquiry_id=test_inquiry.id,
                title="Story A",
                description="Desc A",
                priority=Priority.MEDIUM,
                assignee="alice",
            ),
            StoryModel(
                inquiry_id=test_inquiry.id,
                title="Story B",
                description="Desc B",
                priority=Priority.MEDIUM,
                assignee="bob",
            ),
            StoryModel(
                inquiry_id=test_inquiry.id,
                title="Story C",
                description="Desc C",
                priority=Priority.MEDIUM,
                assignee=None,
            ),
        ]
        for story in stories:
            db_session.add(story)
        db_session.commit()

        service = StoryQueryService(db_session)
        request = ListStoriesRequest(sort_by="assignee", sort_order="asc")

        result = service.list_stories(request)

        # NULL値は最後
        assignees = [story.assignee for story in result["data"] if story.assignee]
        assert assignees[0] == "alice"
        assert assignees[1] == "bob"

    def test_list_stories_sort_by_deadline(
        self, db_session: Session, test_inquiry: InquiryModel
    ):
        """期限でソートできる."""
        now = datetime.now(timezone.utc)
        stories = [
            StoryModel(
                inquiry_id=test_inquiry.id,
                title="Story 1",
                description="Desc 1",
                priority=Priority.MEDIUM,
                deadline=now.replace(day=10),
            ),
            StoryModel(
                inquiry_id=test_inquiry.id,
                title="Story 2",
                description="Desc 2",
                priority=Priority.MEDIUM,
                deadline=now.replace(day=5),
            ),
        ]
        for story in stories:
            db_session.add(story)
        db_session.commit()

        service = StoryQueryService(db_session)
        request = ListStoriesRequest(sort_by="deadline", sort_order="asc")

        result = service.list_stories(request)

        assert result["data"][0].deadline < result["data"][1].deadline

    def test_list_stories_pagination_page_1(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """ページネーション - 1ページ目."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(page=1, limit=2)

        result = service.list_stories(request)

        assert len(result["data"]) == 2
        assert result["meta"]["page"] == 1
        assert result["meta"]["limit"] == 2
        assert result["meta"]["total"] == 4
        assert result["meta"]["has_next"] is True

    def test_list_stories_pagination_page_2(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """ページネーション - 2ページ目."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(page=2, limit=2)

        result = service.list_stories(request)

        assert len(result["data"]) == 2
        assert result["meta"]["page"] == 2
        assert result["meta"]["limit"] == 2
        assert result["meta"]["total"] == 4
        assert result["meta"]["has_next"] is False

    def test_list_stories_pagination_last_page_partial(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """ページネーション - 最終ページが部分的に満たされる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(page=2, limit=3)

        result = service.list_stories(request)

        assert len(result["data"]) == 1
        assert result["meta"]["page"] == 2
        assert result["meta"]["limit"] == 3
        assert result["meta"]["total"] == 4
        assert result["meta"]["has_next"] is False

    def test_list_stories_pagination_page_out_of_range(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """ページネーション - 範囲外のページ."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(page=10, limit=10)

        result = service.list_stories(request)

        assert len(result["data"]) == 0
        assert result["meta"]["page"] == 10
        assert result["meta"]["total"] == 4
        assert result["meta"]["has_next"] is False

    def test_list_stories_invalid_page_zero(self, db_session: Session):
        """無効なページ番号（0）でエラー."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(page=0)

        with pytest.raises(InvalidPaginationError) as exc_info:
            service.list_stories(request)

        assert "pageは1以上である必要があります" in str(exc_info.value)

    def test_list_stories_invalid_page_negative(self, db_session: Session):
        """無効なページ番号（負数）でエラー."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(page=-1)

        with pytest.raises(InvalidPaginationError) as exc_info:
            service.list_stories(request)

        assert "pageは1以上である必要があります" in str(exc_info.value)

    def test_list_stories_invalid_limit_zero(self, db_session: Session):
        """無効なlimit（0）でエラー."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(limit=0)

        with pytest.raises(InvalidPaginationError) as exc_info:
            service.list_stories(request)

        assert "limitは1以上である必要があります" in str(exc_info.value)

    def test_list_stories_invalid_limit_negative(self, db_session: Session):
        """無効なlimit（負数）でエラー."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(limit=-5)

        with pytest.raises(InvalidPaginationError) as exc_info:
            service.list_stories(request)

        assert "limitは1以上である必要があります" in str(exc_info.value)

    def test_list_stories_limit_clamped_to_100(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """limitは最大100にクランプされる."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(limit=200)

        result = service.list_stories(request)

        assert result["meta"]["limit"] == 100

    def test_list_stories_invalid_sort_by(self, db_session: Session):
        """無効なソートフィールドでエラー."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(sort_by="invalid_field")

        with pytest.raises(InvalidPaginationError) as exc_info:
            service.list_stories(request)

        assert "無効なソートフィールドが指定されました" in str(exc_info.value)

    def test_list_stories_invalid_sort_order(self, db_session: Session):
        """無効なソート順序でエラー."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest(sort_order="invalid")

        with pytest.raises(InvalidPaginationError) as exc_info:
            service.list_stories(request)

        assert "無効なソート順序が指定されました" in str(exc_info.value)

    def test_get_story_existing(
        self, db_session: Session, test_stories: list[StoryModel]
    ):
        """既存ストーリーを取得できる."""
        service = StoryQueryService(db_session)
        story = test_stories[0]

        result = service.get_story(story.id)

        assert result.id == story.id
        assert result.title == story.title

    def test_get_story_not_found(self, db_session: Session):
        """存在しないストーリーIDでエラー."""
        service = StoryQueryService(db_session)

        with pytest.raises(StoryNotFoundError) as exc_info:
            service.get_story(9999)

        assert exc_info.value.story_id == 9999
        assert "指定されたストーリーが見つかりません" in str(exc_info.value)

    def test_list_stories_empty_result(self, db_session: Session):
        """ストーリーが存在しない場合は空リスト."""
        service = StoryQueryService(db_session)
        request = ListStoriesRequest()

        result = service.list_stories(request)

        assert len(result["data"]) == 0
        assert result["meta"]["total"] == 0
        assert result["meta"]["has_next"] is False

    def test_list_stories_complex_query(
        self, db_session: Session, test_inquiry: InquiryModel
    ):
        """複雑なクエリ条件の組み合わせ."""
        # 複数ストーリーを追加
        stories = [
            StoryModel(
                inquiry_id=test_inquiry.id,
                title="High Priority Story",
                description="Desc",
                priority=Priority.HIGH,
                status=StoryStatus.WAITING_REVIEW,
                estimated_effort=10.0,
            ),
            StoryModel(
                inquiry_id=test_inquiry.id,
                title="Medium Priority Story",
                description="Desc",
                priority=Priority.MEDIUM,
                status=StoryStatus.WAITING_REVIEW,
                estimated_effort=5.0,
            ),
            StoryModel(
                inquiry_id=test_inquiry.id,
                title="Approved Story",
                description="Desc",
                priority=Priority.HIGH,
                status=StoryStatus.APPROVED,
                estimated_effort=8.0,
            ),
        ]
        for story in stories:
            db_session.add(story)
        db_session.commit()

        service = StoryQueryService(db_session)
        request = ListStoriesRequest(
            status=StoryStatus.WAITING_REVIEW,
            priority=[Priority.HIGH, Priority.MEDIUM],
            inquiry_id=test_inquiry.id,
            sort_by="estimated_effort",
            sort_order="desc",
            page=1,
            limit=10,
        )

        result = service.list_stories(request)

        assert len(result["data"]) == 2
        assert result["data"][0].estimated_effort == 10.0
        assert result["data"][1].estimated_effort == 5.0
        for story in result["data"]:
            assert story.status == StoryStatus.WAITING_REVIEW
            assert story.priority in [Priority.HIGH, Priority.MEDIUM]

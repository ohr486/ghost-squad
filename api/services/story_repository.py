"""StoryRepository data access layer.

ストーリーのCRUD操作とクエリ実行を提供する。
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from models.database.story import StoryModel
from models.enums.priority import Priority
from models.enums.story_status import StoryStatus


class CreateStoryData:
    """ストーリー作成データ."""

    def __init__(
        self,
        inquiry_id: int,
        title: str,
        description: str,
        priority: Priority,
        estimated_effort: Optional[float] = None,
        deadline: Optional[datetime] = None,
        assignee: Optional[str] = None,
    ):
        """Initialize CreateStoryData.

        Args:
            inquiry_id: 問い合わせID（必須）
            title: タイトル（必須、最大500文字）
            description: 説明（必須）
            priority: 優先度
            estimated_effort: 推定工数（オプショナル）
            deadline: 期限（オプショナル）
            assignee: 担当者（オプショナル）
        """
        self.inquiry_id = inquiry_id
        self.title = title
        self.description = description
        self.priority = priority
        self.estimated_effort = estimated_effort
        self.deadline = deadline
        self.assignee = assignee


class UpdateStoryData:
    """ストーリー更新データ."""

    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        estimated_effort: Optional[float] = None,
        deadline: Optional[datetime] = None,
        assignee: Optional[str] = None,
    ):
        """Initialize UpdateStoryData.

        Args:
            title: タイトル（オプショナル）
            description: 説明（オプショナル）
            priority: 優先度（オプショナル）
            estimated_effort: 推定工数（オプショナル）
            deadline: 期限（オプショナル）
            assignee: 担当者（オプショナル）
        """
        self.title = title
        self.description = description
        self.priority = priority
        self.estimated_effort = estimated_effort
        self.deadline = deadline
        self.assignee = assignee


class StoryFilter:
    """ストーリーフィルタ条件."""

    def __init__(
        self,
        status: Optional[StoryStatus | list[StoryStatus]] = None,
        priority: Optional[Priority | list[Priority]] = None,
        inquiry_id: Optional[int] = None,
    ):
        """Initialize StoryFilter.

        Args:
            status: ステータスフィルタ（単一または複数）
            priority: 優先度フィルタ（単一または複数）
            inquiry_id: 問い合わせIDフィルタ
        """
        self.status = status
        self.priority = priority
        self.inquiry_id = inquiry_id


class SortOption:
    """ソートオプション."""

    def __init__(
        self,
        field: str,
        direction: str = "desc",
    ):
        """Initialize SortOption.

        Args:
            field: ソートフィールド（created_at, updated_at, priority,
                   estimated_effort, assignee, deadline）
            direction: ソート方向（asc, desc）
        """
        self.field = field
        self.direction = direction


class PaginationOption:
    """ページネーションオプション."""

    def __init__(
        self,
        page: int = 1,
        limit: int = 20,
    ):
        """Initialize PaginationOption.

        Args:
            page: ページ番号（1-indexed）
            limit: 1ページあたりの件数（1-100）
        """
        self.page = max(page, 1)  # ページ番号は最低1
        self.limit = min(max(limit, 1), 100)  # 1-100の範囲に制限


class FindManyOptions:
    """ストーリー検索オプション."""

    def __init__(
        self,
        filter: Optional[StoryFilter] = None,
        sort: Optional[list[SortOption]] = None,
        pagination: Optional[PaginationOption] = None,
    ):
        """Initialize FindManyOptions.

        Args:
            filter: フィルタ条件
            sort: ソートオプション
            pagination: ページネーションオプション
        """
        self.filter = filter or StoryFilter()
        self.sort = sort or [SortOption(field="created_at", direction="desc")]
        self.pagination = pagination


class StoryRepository:
    """ストーリーリポジトリ.

    ストーリーのCRUD操作とクエリ実行を提供する。
    """

    def __init__(self, session: Session):
        """Initialize StoryRepository.

        Args:
            session: SQLAlchemyセッション
        """
        self.session = session

    def create(self, data: CreateStoryData) -> StoryModel:
        """ストーリーを作成する（要件2.1, 4.1, 4.2）.

        Args:
            data: ストーリー作成データ

        Returns:
            StoryModel: 作成されたストーリーエンティティ

        Raises:
            IntegrityError: 外部キー制約違反（inquiry_id不存在）
        """
        story = StoryModel(
            inquiry_id=data.inquiry_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            status=StoryStatus.WAITING_REVIEW,
            estimated_effort=data.estimated_effort,
            deadline=data.deadline,
            assignee=data.assignee,
            story_metadata={},
        )
        self.session.add(story)
        self.session.commit()
        self.session.refresh(story)
        return story

    def find_by_id(self, story_id: int) -> Optional[StoryModel]:
        """IDでストーリーを取得する（要件2.5）.

        Args:
            story_id: ストーリーID

        Returns:
            StoryModel | None: ストーリーエンティティ、存在しない場合はNone
        """
        return self.session.query(StoryModel).filter(StoryModel.id == story_id).first()

    def find_many(self, options: FindManyOptions) -> list[StoryModel]:
        """ストーリーを検索する（要件2.1-2.4）.

        Args:
            options: 検索オプション

        Returns:
            list[StoryModel]: ストーリーエンティティのリスト
        """
        query = self.session.query(StoryModel)

        # フィルタ適用
        if options.filter:
            if options.filter.status is not None:
                if isinstance(options.filter.status, list):
                    query = query.filter(StoryModel.status.in_(options.filter.status))
                else:
                    query = query.filter(StoryModel.status == options.filter.status)

            if options.filter.priority is not None:
                if isinstance(options.filter.priority, list):
                    query = query.filter(
                        StoryModel.priority.in_(options.filter.priority)
                    )
                else:
                    query = query.filter(StoryModel.priority == options.filter.priority)

            if options.filter.inquiry_id is not None:
                query = query.filter(StoryModel.inquiry_id == options.filter.inquiry_id)

        # ソート適用（要件2.4: デフォルトはcreated_at DESC）
        for sort_option in options.sort:
            try:
                field = getattr(StoryModel, sort_option.field)
            except AttributeError as exc:
                raise ValueError(f"Invalid sort field: {sort_option.field}") from exc
            if sort_option.direction == "asc":
                query = query.order_by(asc(field))
            else:
                query = query.order_by(desc(field))

        # ページネーション適用（要件2.2）
        if options.pagination:
            offset = (options.pagination.page - 1) * options.pagination.limit
            query = query.offset(offset).limit(options.pagination.limit)

        return query.all()

    def count(self, filter: StoryFilter) -> int:
        """ストーリー数をカウントする.

        Args:
            filter: フィルタ条件

        Returns:
            int: ストーリー数
        """
        query = self.session.query(func.count(StoryModel.id))

        # フィルタ適用
        if filter.status is not None:
            if isinstance(filter.status, list):
                query = query.filter(StoryModel.status.in_(filter.status))
            else:
                query = query.filter(StoryModel.status == filter.status)

        if filter.priority is not None:
            if isinstance(filter.priority, list):
                query = query.filter(StoryModel.priority.in_(filter.priority))
            else:
                query = query.filter(StoryModel.priority == filter.priority)

        if filter.inquiry_id is not None:
            query = query.filter(StoryModel.inquiry_id == filter.inquiry_id)

        result: int = query.scalar()
        return result

    def update(self, story_id: int, data: UpdateStoryData) -> StoryModel:
        """ストーリーを更新する（要件2.6, 2.7, 2.8）.

        Args:
            story_id: ストーリーID
            data: 更新データ

        Returns:
            StoryModel: 更新されたストーリーエンティティ

        Raises:
            ValueError: ストーリーが存在しない場合

        Note:
            すべてのフィールドがNoneの場合でも、updated_atは更新される（要件2.9）。
        """
        story = self.find_by_id(story_id)
        if story is None:
            raise ValueError(f"Story with id {story_id} not found")

        # 更新データを適用
        if data.title is not None:
            story.title = data.title

        if data.description is not None:
            story.description = data.description

        if data.priority is not None:
            story.priority = data.priority

        if data.estimated_effort is not None:
            story.estimated_effort = data.estimated_effort

        if data.deadline is not None:
            story.deadline = data.deadline

        if data.assignee is not None:
            story.assignee = data.assignee

        # updated_atを自動更新（要件2.9）
        story.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(story)
        return story

    def delete(self, story_id: int) -> None:
        """ストーリーを削除する（要件2.15, 2.17）.

        Args:
            story_id: ストーリーID

        Raises:
            ValueError: ストーリーが存在しない場合
        """
        story = self.find_by_id(story_id)
        if story is None:
            raise ValueError(f"Story with id {story_id} not found")

        self.session.delete(story)
        self.session.commit()

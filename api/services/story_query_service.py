"""StoryQueryService - ストーリー検索とページネーション.

ストーリーの検索、フィルタリング、ソート、ページネーション機能を提供する。
"""

from typing import Any, Dict, List, Optional, Union

from sqlalchemy import asc, desc, nullslast
from sqlalchemy.orm import Session

from models.database.story import StoryModel
from models.enums.priority import Priority
from models.enums.story_status import StoryStatus


class StoryNotFoundError(Exception):
    """ストーリーが見つからないエラー."""

    def __init__(self, story_id: int):
        """Initialize StoryNotFoundError.

        Args:
            story_id: 存在しないストーリーID
        """
        super().__init__(f"指定されたストーリーが見つかりません: {story_id}")
        self.story_id = story_id


class InvalidPaginationError(Exception):
    """無効なページネーションパラメータエラー.

    ページ番号やページサイズなどのページネーション用パラメータが
    許容範囲外または不正な場合に発生する。
    """

    def __init__(self, message: str = "無効なページネーションパラメータです。"):
        """Initialize InvalidPaginationError.

        Args:
            message: エラーの詳細メッセージ
        """
        super().__init__(message)
        self.message = message


class ListStoriesRequest:
    """ストーリー一覧取得リクエスト."""

    def __init__(
        self,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        status: Optional[Union[StoryStatus, List[StoryStatus]]] = None,
        priority: Optional[Union[Priority, List[Priority]]] = None,
        inquiry_id: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ):
        """Initialize ListStoriesRequest.

        Args:
            page: ページ番号（デフォルト: 1）
            limit: ページサイズ（デフォルト: 20、範囲: 1-100）
            status: フィルタリングするステータス（単一または複数）
            priority: フィルタリングする優先度（単一または複数）
            inquiry_id: フィルタリングする問い合わせID
            sort_by: ソートフィールド（created_at、updated_at、priority、
                     estimated_effort、assignee、deadline）
            sort_order: ソート順序（asc または desc、デフォルト: desc）
        """
        self.page = page if page is not None else 1
        self.limit = limit if limit is not None else 20
        self.status = status
        self.priority = priority
        self.inquiry_id = inquiry_id
        self.sort_by = sort_by if sort_by is not None else "created_at"
        self.sort_order = sort_order if sort_order is not None else "desc"


class StoryQueryService:
    """ストーリークエリサービス."""

    def __init__(self, session: Session):
        """Initialize StoryQueryService.

        Args:
            session: SQLAlchemyセッション
        """
        self.session = session

    def list_stories(self, request: ListStoriesRequest) -> Dict[str, Any]:
        """ストーリー一覧を取得する.

        Args:
            request: 一覧取得リクエスト

        Returns:
            ページネーション付きストーリーリスト

        Raises:
            InvalidPaginationError: ページネーションパラメータが不正な場合
        """
        # Validate page parameter
        if request.page < 1:
            raise InvalidPaginationError("pageは1以上である必要があります")

        # Validate limit parameter
        if request.limit < 1:
            raise InvalidPaginationError("limitは1以上である必要があります")

        # Clamp limit to maximum 100
        limit = min(request.limit, 100)

        # Validate sort_by parameter
        allowed_sort_fields = {
            "created_at",
            "updated_at",
            "priority",
            "estimated_effort",
            "assignee",
            "deadline",
        }
        if request.sort_by not in allowed_sort_fields:
            raise InvalidPaginationError(
                f"無効なソートフィールドが指定されました: {request.sort_by}. "
                f"有効な値: {', '.join(sorted(allowed_sort_fields))}"
            )

        # Validate sort_order parameter
        allowed_sort_orders = {"asc", "desc"}
        if request.sort_order not in allowed_sort_orders:
            raise InvalidPaginationError(
                f"無効なソート順序が指定されました: {request.sort_order}. "
                f"有効な値: {', '.join(sorted(allowed_sort_orders))}"
            )

        # Build query with filters
        query = self.session.query(StoryModel)

        # Filter by status
        if request.status is not None:
            if isinstance(request.status, list):
                query = query.filter(StoryModel.status.in_(request.status))
            else:
                query = query.filter(StoryModel.status == request.status)

        # Filter by priority
        if request.priority is not None:
            if isinstance(request.priority, list):
                query = query.filter(StoryModel.priority.in_(request.priority))
            else:
                query = query.filter(StoryModel.priority == request.priority)

        # Filter by inquiry_id
        if request.inquiry_id is not None:
            query = query.filter(StoryModel.inquiry_id == request.inquiry_id)

        # Get total count
        total = query.count()

        # Apply sorting
        sort_field = getattr(StoryModel, request.sort_by)
        if request.sort_order == "asc":
            # NULLs last for ascending order
            query = query.order_by(nullslast(asc(sort_field)))
        else:
            # NULLs last for descending order
            query = query.order_by(nullslast(desc(sort_field)))

        # Apply pagination
        offset = (request.page - 1) * limit
        data = query.offset(offset).limit(limit).all()

        # Calculate has_next
        has_next = (offset + len(data)) < total

        return {
            "data": data,
            "meta": {
                "page": request.page,
                "limit": limit,
                "total": total,
                "has_next": has_next,
            },
        }

    def get_story(self, story_id: int) -> StoryModel:
        """ストーリー詳細を取得する.

        Args:
            story_id: ストーリーID

        Returns:
            ストーリーエンティティ

        Raises:
            StoryNotFoundError: ストーリーが存在しない場合
        """
        story = self.session.query(StoryModel).filter(StoryModel.id == story_id).first()

        if story is None:
            raise StoryNotFoundError(story_id)

        return story

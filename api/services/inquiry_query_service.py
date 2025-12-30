"""InquiryQueryService - 問い合わせ検索とページネーション.

問い合わせの検索、フィルタリング、ソート、ページネーション機能を提供する。
"""

from typing import Any, Dict, List, Optional, Union

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus


class InquiryNotFoundError(Exception):
    """問い合わせが見つからないエラー."""

    def __init__(self, inquiry_id: int):
        """Initialize InquiryNotFoundError.

        Args:
            inquiry_id: 存在しない問い合わせID
        """
        super().__init__(f"指定された問い合わせが見つかりません: {inquiry_id}")
        self.inquiry_id = inquiry_id


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


class ListInquiriesRequest:
    """問い合わせ一覧取得リクエスト."""

    def __init__(
        self,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        status: Optional[Union[InquiryStatus, List[InquiryStatus]]] = None,
        user_id: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ):
        """Initialize ListInquiriesRequest.

        Args:
            page: ページ番号（デフォルト: 1）
            limit: ページサイズ（デフォルト: 20、範囲: 1-100）
            status: フィルタリングするステータス（単一または複数）
            user_id: フィルタリングするユーザーID
            sort_by: ソートフィールド（created_at または updated_at）
            sort_order: ソート順序（asc または desc、デフォルト: desc）
        """
        self.page = page if page is not None else 1
        self.limit = limit if limit is not None else 20
        self.status = status
        self.user_id = user_id
        self.sort_by = sort_by if sort_by is not None else "created_at"
        self.sort_order = sort_order if sort_order is not None else "desc"


class InquiryQueryService:
    """問い合わせクエリサービス."""

    def __init__(self, session: Session):
        """Initialize InquiryQueryService.

        Args:
            session: SQLAlchemyセッション
        """
        self.session = session

    def list_inquiries(self, request: ListInquiriesRequest) -> Dict[str, Any]:
        """問い合わせ一覧を取得する.

        Args:
            request: 一覧取得リクエスト

        Returns:
            ページネーション付き問い合わせリスト

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
        allowed_sort_fields = {"created_at", "updated_at"}
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
        query = self.session.query(InquiryModel)

        # Filter by status
        if request.status is not None:
            if isinstance(request.status, list):
                query = query.filter(InquiryModel.status.in_(request.status))
            else:
                query = query.filter(InquiryModel.status == request.status)

        # Filter by user_id
        if request.user_id is not None:
            query = query.filter(InquiryModel.user_id == request.user_id)

        # Get total count
        total = query.count()

        # Apply sorting
        sort_field = getattr(InquiryModel, request.sort_by)
        if request.sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))

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

    def get_inquiry(self, inquiry_id: int) -> InquiryModel:
        """問い合わせ詳細を取得する.

        Args:
            inquiry_id: 問い合わせID

        Returns:
            問い合わせエンティティ

        Raises:
            InquiryNotFoundError: 問い合わせが存在しない場合
        """
        inquiry = (
            self.session.query(InquiryModel)
            .filter(InquiryModel.id == inquiry_id)
            .first()
        )

        if inquiry is None:
            raise InquiryNotFoundError(inquiry_id)

        return inquiry

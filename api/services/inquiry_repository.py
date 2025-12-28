"""InquiryRepository data access layer.

問い合わせのCRUD操作とクエリ実行を提供する。
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus


class CreateInquiryData:
    """問い合わせ作成データ."""

    def __init__(
        self,
        user_id: str,
        content: str,
        source_system: str,
        timestamp: datetime,
        status: InquiryStatus,
    ):
        """Initialize CreateInquiryData.

        Args:
            user_id: ユーザーID
            content: 問い合わせ内容
            source_system: 送信元システム
            timestamp: タイムスタンプ
            status: 問い合わせステータス
        """
        self.user_id = user_id
        self.content = content
        self.source_system = source_system
        self.timestamp = timestamp
        self.status = status


class UpdateInquiryData:
    """問い合わせ更新データ."""

    def __init__(
        self,
        content: Optional[str] = None,
        source_system: Optional[str] = None,
    ):
        """Initialize UpdateInquiryData.

        Args:
            content: 問い合わせ内容（オプショナル）
            source_system: 送信元システム（オプショナル）
        """
        self.content = content
        self.source_system = source_system


class InquiryFilter:
    """問い合わせフィルタ条件."""

    def __init__(
        self,
        status: Optional[InquiryStatus | list[InquiryStatus]] = None,
        user_id: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ):
        """Initialize InquiryFilter.

        Args:
            status: ステータスフィルタ（単一または複数）
            user_id: ユーザーIDフィルタ
            created_after: 作成日時フィルタ（以降）
            created_before: 作成日時フィルタ（以前）
        """
        self.status = status
        self.user_id = user_id
        self.created_after = created_after
        self.created_before = created_before


class SortOption:
    """ソートオプション."""

    def __init__(
        self,
        field: str,
        direction: str = "desc",
    ):
        """Initialize SortOption.

        Args:
            field: ソートフィールド（created_at, updated_at, status）
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
        self.page = page
        self.limit = min(max(limit, 1), 100)  # 1-100の範囲に制限


class FindManyOptions:
    """問い合わせ検索オプション."""

    def __init__(
        self,
        filter: Optional[InquiryFilter] = None,
        sort: Optional[list[SortOption]] = None,
        pagination: Optional[PaginationOption] = None,
    ):
        """Initialize FindManyOptions.

        Args:
            filter: フィルタ条件
            sort: ソートオプション
            pagination: ページネーションオプション
        """
        self.filter = filter or InquiryFilter()
        self.sort = sort or [SortOption(field="created_at", direction="desc")]
        self.pagination = pagination


class InquiryRepository:
    """問い合わせリポジトリ.

    問い合わせのCRUD操作とクエリ実行を提供する。
    """

    def __init__(self, session: Session):
        """Initialize InquiryRepository.

        Args:
            session: SQLAlchemyセッション
        """
        self.session = session

    def create(self, data: CreateInquiryData) -> InquiryModel:
        """問い合わせを作成する（要件1.1）.

        Args:
            data: 問い合わせ作成データ

        Returns:
            InquiryModel: 作成された問い合わせエンティティ
        """
        inquiry = InquiryModel(
            user_id=data.user_id,
            content=data.content,
            source_system=data.source_system,
            timestamp=data.timestamp,
            status=data.status,
            inquiry_metadata={},
        )
        self.session.add(inquiry)
        self.session.commit()
        self.session.refresh(inquiry)
        return inquiry

    def find_by_id(self, inquiry_id: int) -> Optional[InquiryModel]:
        """IDで問い合わせを取得する（要件2.5）.

        Args:
            inquiry_id: 問い合わせID

        Returns:
            InquiryModel | None: 問い合わせエンティティ、存在しない場合はNone（要件2.6）
        """
        return (
            self.session.query(InquiryModel)
            .filter(InquiryModel.id == inquiry_id)
            .first()
        )

    def find_many(self, options: FindManyOptions) -> list[InquiryModel]:
        """問い合わせを検索する（要件2.1-2.3）.

        Args:
            options: 検索オプション

        Returns:
            list[InquiryModel]: 問い合わせエンティティのリスト
        """
        query = self.session.query(InquiryModel)

        # フィルタ適用
        if options.filter:
            if options.filter.status is not None:
                if isinstance(options.filter.status, list):
                    query = query.filter(InquiryModel.status.in_(options.filter.status))
                else:
                    query = query.filter(InquiryModel.status == options.filter.status)

            if options.filter.user_id is not None:
                query = query.filter(InquiryModel.user_id == options.filter.user_id)

            if options.filter.created_after is not None:
                query = query.filter(
                    InquiryModel.created_at >= options.filter.created_after
                )

            if options.filter.created_before is not None:
                query = query.filter(
                    InquiryModel.created_at <= options.filter.created_before
                )

        # ソート適用（要件2.3: デフォルトはcreated_at DESC）
        for sort_option in options.sort:
            field = getattr(InquiryModel, sort_option.field)
            if sort_option.direction == "asc":
                query = query.order_by(asc(field))
            else:
                query = query.order_by(desc(field))

        # ページネーション適用（要件2.1, 2.2）
        if options.pagination:
            offset = (options.pagination.page - 1) * options.pagination.limit
            query = query.offset(offset).limit(options.pagination.limit)

        return query.all()

    def count(self, filter: InquiryFilter) -> int:
        """問い合わせ数をカウントする.

        Args:
            filter: フィルタ条件

        Returns:
            int: 問い合わせ数
        """
        query = self.session.query(func.count(InquiryModel.id))

        # フィルタ適用
        if filter.status is not None:
            if isinstance(filter.status, list):
                query = query.filter(InquiryModel.status.in_(filter.status))
            else:
                query = query.filter(InquiryModel.status == filter.status)

        if filter.user_id is not None:
            query = query.filter(InquiryModel.user_id == filter.user_id)

        if filter.created_after is not None:
            query = query.filter(InquiryModel.created_at >= filter.created_after)

        if filter.created_before is not None:
            query = query.filter(InquiryModel.created_at <= filter.created_before)

        result: int = query.scalar()
        return result

    def update(self, inquiry_id: int, data: UpdateInquiryData) -> InquiryModel:
        """問い合わせを更新する（要件2.8）.

        Args:
            inquiry_id: 問い合わせID
            data: 更新データ

        Returns:
            InquiryModel: 更新された問い合わせエンティティ

        Raises:
            ValueError: 問い合わせが存在しない場合
        """
        inquiry = self.find_by_id(inquiry_id)
        if inquiry is None:
            raise ValueError(f"Inquiry with id {inquiry_id} not found")

        # 更新データを適用
        if data.content is not None:
            inquiry.content = data.content

        if data.source_system is not None:
            inquiry.source_system = data.source_system

        # updated_atを自動更新（要件2.9）
        inquiry.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(inquiry)
        return inquiry

    def update_status(self, inquiry_id: int, status: InquiryStatus) -> InquiryModel:
        """問い合わせステータスを更新する（要件3.1）.

        Args:
            inquiry_id: 問い合わせID
            status: 新しいステータス

        Returns:
            InquiryModel: 更新された問い合わせエンティティ

        Raises:
            ValueError: 問い合わせが存在しない場合
        """
        inquiry = self.find_by_id(inquiry_id)
        if inquiry is None:
            raise ValueError(f"Inquiry with id {inquiry_id} not found")

        inquiry.status = status
        # updated_atを自動更新（要件3.2）
        inquiry.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(inquiry)
        return inquiry

    def delete(self, inquiry_id: int) -> None:
        """問い合わせを削除する（将来実装）.

        Args:
            inquiry_id: 問い合わせID

        Raises:
            ValueError: 問い合わせが存在しない場合
        """
        inquiry = self.find_by_id(inquiry_id)
        if inquiry is None:
            raise ValueError(f"Inquiry with id {inquiry_id} not found")

        self.session.delete(inquiry)
        self.session.commit()

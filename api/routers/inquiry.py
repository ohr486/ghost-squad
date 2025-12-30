"""問い合わせAPI - CRUD and Workflow endpoints.

問い合わせの作成、取得、更新、承認、却下のエンドポイントを提供する。
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.enums.inquiry_status import InquiryStatus
from models.schemas.inquiry import (CreateInquiryRequest, ErrorResponse,
                                    InquiryResponse, UpdateInquiryRequest,
                                    ValidationErrorDetail)
from services.inquiry_query_service import (InquiryNotFoundError,
                                            InquiryQueryService,
                                            InvalidPaginationError,
                                            ListInquiriesRequest)
from services.inquiry_repository import (CreateInquiryData, InquiryRepository,
                                         UpdateInquiryData)
from services.inquiry_workflow_service import (InquiryWorkflowService,
                                               InvalidStateTransitionError)

router = APIRouter(prefix="/api/inquiries", tags=["inquiries"])


# Enums for query parameters
class SortField(str, Enum):
    """ソート可能なフィールド."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortOrder(str, Enum):
    """ソート順序."""

    ASC = "asc"
    DESC = "desc"


# Response models for pagination
class PaginationMeta(BaseModel):
    """ページネーションメタデータ."""

    page: int = Field(..., description="現在のページ番号")
    limit: int = Field(..., description="ページサイズ")
    total: int = Field(..., description="総件数")
    has_next: bool = Field(..., description="次ページの有無")


class PaginatedInquiriesResponse(BaseModel):
    """ページネーション付き問い合わせリストレスポンス."""

    data: List[InquiryResponse] = Field(..., description="問い合わせリスト")
    meta: PaginationMeta = Field(..., description="ページネーションメタデータ")
    timestamp: str = Field(..., description="レスポンスタイムスタンプ")


# Helper function to create error response
def _create_error_response(
    code: str, message: str, field: Optional[str] = None
) -> ErrorResponse:
    """エラーレスポンスを作成する.

    Args:
        code: エラーコード（GS-xxx形式）
        message: エラーメッセージ（日本語）
        field: エラーが発生したフィールド名（オプション）

    Returns:
        ErrorResponse: 統一フォーマットのエラーレスポンス
    """
    return ErrorResponse(
        errors=[ValidationErrorDetail(code=code, message=message, field=field)],
        timestamp=datetime.now(timezone.utc),
    )


# POST /api/inquiries - 問い合わせ作成
@router.post(
    "",
    response_model=InquiryResponse,
    status_code=http_status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "バリデーションエラー"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def create_inquiry(
    request: CreateInquiryRequest,
    db: Session = Depends(get_db),
) -> InquiryResponse:
    """問い合わせを作成する.

    要件1.1-1.6: 問い合わせの作成

    Args:
        request: 問い合わせ作成リクエスト
        db: データベースセッション

    Returns:
        InquiryResponse: 作成された問い合わせ

    Raises:
        HTTPException: バリデーションエラーまたはサーバーエラー
    """
    try:
        # Pydanticでバリデーション済みなので、追加のバリデーションは不要
        # リポジトリ経由で作成
        repository = InquiryRepository(db)
        create_data = CreateInquiryData(
            user_id=request.user_id,
            content=request.content,
            source_system=request.source_system,
            timestamp=datetime.now(timezone.utc),
            status=InquiryStatus.RECEIVED,
        )
        inquiry = repository.create(create_data)

        return InquiryResponse.model_validate(inquiry)
    except HTTPException:
        raise
    except Exception as e:
        error_response = _create_error_response(
            "GS-010", f"データベース操作に失敗しました: {str(e)}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


# GET /api/inquiries - 問い合わせ一覧取得
@router.get(
    "",
    response_model=PaginatedInquiriesResponse,
    responses={
        400: {"model": ErrorResponse, "description": "バリデーションエラー"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def list_inquiries(
    page: int = Query(default=1, ge=1, description="ページ番号（1以上）"),
    limit: int = Query(default=20, ge=1, le=100, description="ページサイズ（1-100）"),
    status: Optional[str] = Query(
        default=None, description="ステータスフィルタ（カンマ区切りで複数指定可能）"
    ),
    user_id: Optional[str] = Query(default=None, description="ユーザーIDフィルタ"),
    sort_by: SortField = Query(
        default=SortField.CREATED_AT,
        description="ソートフィールド（created_at, updated_at）",
    ),
    sort_order: SortOrder = Query(
        default=SortOrder.DESC, description="ソート順序（asc, desc）"
    ),
    db: Session = Depends(get_db),
) -> PaginatedInquiriesResponse:
    """問い合わせ一覧を取得する.

    要件2.1-2.4: 問い合わせの一覧表示、検索

    Args:
        page: ページ番号
        limit: ページサイズ
        status: ステータスフィルタ（カンマ区切りで複数可）
        user_id: ユーザーIDフィルタ
        sort_by: ソートフィールド
        sort_order: ソート順序
        db: データベースセッション

    Returns:
        PaginatedInquiriesResponse: ページネーション付き問い合わせリスト

    Raises:
        HTTPException: パラメータエラーまたはサーバーエラー
    """
    try:
        # ステータスフィルタのパース
        status_filter: Optional[List[InquiryStatus]] = None
        if status:
            try:
                status_filter = [InquiryStatus(s.strip()) for s in status.split(",")]
            except ValueError as e:
                error_response = _create_error_response(
                    "GS-011", f"無効なステータス値です: {str(e)}", "status"
                )
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=error_response.model_dump(),
                )

        # クエリサービス経由で取得
        query_service = InquiryQueryService(db)
        list_request = ListInquiriesRequest(
            page=page,
            limit=limit,
            status=status_filter,
            user_id=user_id,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
        )
        result = query_service.list_inquiries(list_request)

        # レスポンス変換
        return PaginatedInquiriesResponse(
            data=[InquiryResponse.model_validate(inq) for inq in result["data"]],
            meta=PaginationMeta(**result["meta"]),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except InvalidPaginationError as e:
        error_response = _create_error_response("GS-011", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=error_response.model_dump(),
        )
    except HTTPException:
        raise
    except Exception as e:
        error_response = _create_error_response(
            "GS-010", f"データベース操作に失敗しました: {str(e)}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


# GET /api/inquiries/{id} - 問い合わせ詳細取得
@router.get(
    "/{inquiry_id}",
    response_model=InquiryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "問い合わせが見つかりません"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def get_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
) -> InquiryResponse:
    """問い合わせ詳細を取得する.

    要件2.5-2.6: 問い合わせ詳細取得

    Args:
        inquiry_id: 問い合わせID
        db: データベースセッション

    Returns:
        InquiryResponse: 問い合わせ詳細

    Raises:
        HTTPException: 問い合わせが見つからない、またはサーバーエラー
    """
    try:
        query_service = InquiryQueryService(db)
        inquiry = query_service.get_inquiry(inquiry_id)
        return InquiryResponse.model_validate(inquiry)
    except InquiryNotFoundError as e:
        error_response = _create_error_response("GS-005", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=error_response.model_dump(),
        )
    except Exception as e:
        error_response = _create_error_response(
            "GS-010", f"データベース操作に失敗しました: {str(e)}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


# PUT /api/inquiries/{id} - 問い合わせ更新
@router.put(
    "/{inquiry_id}",
    response_model=InquiryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "バリデーションエラー"},
        404: {"model": ErrorResponse, "description": "問い合わせが見つかりません"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def update_inquiry(
    inquiry_id: int,
    request: UpdateInquiryRequest,
    db: Session = Depends(get_db),
) -> InquiryResponse:
    """問い合わせを更新する.

    要件2.8-2.9: 問い合わせ編集

    Args:
        inquiry_id: 問い合わせID
        request: 問い合わせ更新リクエスト
        db: データベースセッション

    Returns:
        InquiryResponse: 更新された問い合わせ

    Raises:
        HTTPException: バリデーションエラー、問い合わせが見つからない、またはサーバーエラー
    """
    try:
        # Pydanticでバリデーション済みなので、追加のバリデーションは不要
        # リポジトリ経由で更新
        repository = InquiryRepository(db)

        # 問い合わせの存在確認
        existing = repository.find_by_id(inquiry_id)
        if not existing:
            error_response = _create_error_response(
                "GS-005", f"指定された問い合わせが見つかりません: {inquiry_id}"
            )
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=error_response.model_dump(),
            )

        update_data = UpdateInquiryData(
            content=request.content,
            source_system=request.source_system,
        )
        inquiry = repository.update(inquiry_id, update_data)

        return InquiryResponse.model_validate(inquiry)
    except HTTPException:
        raise
    except Exception as e:
        error_response = _create_error_response(
            "GS-010", f"データベース操作に失敗しました: {str(e)}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


# POST /api/inquiries/{id}/approve - 問い合わせ承認
@router.post(
    "/{inquiry_id}/approve",
    response_model=InquiryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "問い合わせが見つかりません"},
        409: {
            "model": ErrorResponse,
            "description": "無効なステータス遷移（承認済みまたは却下済み）",
        },
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def approve_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
) -> InquiryResponse:
    """問い合わせを承認する.

    要件3.1-3.3: 問い合わせの承認

    Args:
        inquiry_id: 問い合わせID
        db: データベースセッション

    Returns:
        InquiryResponse: 承認された問い合わせ

    Raises:
        HTTPException: 問い合わせが見つからない、無効なステータス遷移、またはサーバーエラー
    """
    try:
        repository = InquiryRepository(db)
        workflow_service = InquiryWorkflowService(repository)
        inquiry = workflow_service.approve_inquiry(inquiry_id)
        # Repository already commits internally, no need for explicit commit
        return InquiryResponse.model_validate(inquiry)
    except ValueError as e:
        error_response = _create_error_response("GS-005", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=error_response.model_dump(),
        )
    except InvalidStateTransitionError as e:
        error_response = _create_error_response("GS-007", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=error_response.model_dump(),
        )
    except Exception as e:
        error_response = _create_error_response(
            "GS-010", f"データベース操作に失敗しました: {str(e)}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


# POST /api/inquiries/{id}/reject - 問い合わせ却下
class RejectInquiryRequest(BaseModel):
    """問い合わせ却下リクエスト."""

    reason: Optional[str] = Field(
        None,
        max_length=1000,
        description="却下理由（任意、最大1,000文字）",
    )


@router.post(
    "/{inquiry_id}/reject",
    response_model=InquiryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "問い合わせが見つかりません"},
        409: {
            "model": ErrorResponse,
            "description": "無効なステータス遷移（承認済みまたは却下済み）",
        },
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def reject_inquiry(
    inquiry_id: int,
    request: RejectInquiryRequest = Body(default=RejectInquiryRequest(reason=None)),
    db: Session = Depends(get_db),
) -> InquiryResponse:
    """問い合わせを却下する.

    要件3.4-3.9: 問い合わせの却下

    Args:
        inquiry_id: 問い合わせID
        request: 却下リクエスト（却下理由を含む、オプション）
        db: データベースセッション

    Returns:
        InquiryResponse: 却下された問い合わせ

    Raises:
        HTTPException: 問い合わせが見つからない、無効なステータス遷移、またはサーバーエラー
    """
    try:
        repository = InquiryRepository(db)
        workflow_service = InquiryWorkflowService(repository)
        reason = request.reason
        inquiry = workflow_service.reject_inquiry(inquiry_id, reason)
        # Repository already commits internally, no need for explicit commit
        return InquiryResponse.model_validate(inquiry)
    except ValueError as e:
        error_response = _create_error_response("GS-005", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=error_response.model_dump(),
        )
    except InvalidStateTransitionError as e:
        error_response = _create_error_response("GS-007", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=error_response.model_dump(),
        )
    except Exception as e:
        error_response = _create_error_response(
            "GS-010", f"データベース操作に失敗しました: {str(e)}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )

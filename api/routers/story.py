"""ストーリーAPI - CRUD and Workflow endpoints.

ストーリーの作成、取得、更新、削除、承認、却下のエンドポイントを提供する。

タスク 7.1-7.4: Story API層の実装
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.enums.priority import Priority
from models.enums.story_status import StoryStatus
from models.schemas.inquiry import ErrorResponse, ValidationErrorDetail
from models.schemas.story import (CreateStoryRequest, StoryResponse,
                                  UpdateStoryRequest)
from services.inquiry_repository import InquiryRepository
from services.story_generation_service import (AIGenerationError,
                                               InquiryNotFoundError,
                                               InvalidInquiryStatusError,
                                               StoryGenerationService)
from services.story_query_service import (InvalidPaginationError,
                                          ListStoriesRequest,
                                          StoryNotFoundError,
                                          StoryQueryService)
from services.story_repository import (CreateStoryData, StoryRepository,
                                       UpdateStoryData)
from services.story_validator import StoryValidator
from services.story_workflow_service import (InvalidStatusTransitionError,
                                             StoryWorkflowService)

router = APIRouter(prefix="/api", tags=["stories"])


# Enums for query parameters
class SortField(str, Enum):
    """ソート可能なフィールド."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    PRIORITY = "priority"
    ESTIMATED_EFFORT = "estimated_effort"
    ASSIGNEE = "assignee"
    DEADLINE = "deadline"


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


class PaginatedStoriesResponse(BaseModel):
    """ページネーション付きストーリーリストレスポンス."""

    data: List[StoryResponse] = Field(..., description="ストーリーリスト")
    meta: PaginationMeta = Field(..., description="ページネーションメタデータ")
    timestamp: str = Field(..., description="レスポンスタイムスタンプ")


class ApproveStoryRequest(BaseModel):
    """ストーリー承認リクエスト."""

    approver: str = Field(..., min_length=1, description="承認者ID")


class RejectStoryRequest(BaseModel):
    """ストーリー却下リクエスト."""

    rejector: str = Field(..., min_length=1, description="却下者ID")
    reason: str = Field(..., min_length=1, description="却下理由（必須）")


class BatchApproveRequest(BaseModel):
    """一括承認リクエスト."""

    story_ids: List[int] = Field(..., min_length=1, description="承認するストーリーIDのリスト")
    approver: str = Field(..., min_length=1, description="承認者ID")


class BatchApproveResult(BaseModel):
    """一括承認結果."""

    id: int = Field(..., description="ストーリーID")
    success: bool = Field(..., description="成功/失敗")
    error: Optional[str] = Field(None, description="エラーメッセージ（失敗時）")


class BatchApproveResponse(BaseModel):
    """一括承認レスポンス."""

    results: List[BatchApproveResult] = Field(..., description="各ストーリーの処理結果")


class DeleteStoryResponse(BaseModel):
    """ストーリー削除レスポンス."""

    success: bool = Field(..., description="削除成功")


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


# POST /api/inquiries/{inquiry_id}/stories - ストーリー生成（AI or 手動）
@router.post(
    "/inquiries/{inquiry_id}/stories",
    response_model=StoryResponse,
    status_code=http_status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "バリデーションエラー"},
        404: {"model": ErrorResponse, "description": "問い合わせが見つからない"},
        422: {"model": ErrorResponse, "description": "ステータス不正"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def create_story(
    inquiry_id: int,
    db: Session = Depends(get_db),
    request: Optional[CreateStoryRequest] = Body(None, embed=False),
) -> StoryResponse:
    """ストーリーを作成する（AI自動生成 or 手動作成）.

    要件1.1-1.6: AI変換（空ボディ）
    要件2.11-2.14: 手動作成（ボディあり）

    Args:
        inquiry_id: 問い合わせID
        request: ストーリー作成リクエスト（Noneの場合はAI自動生成）
        db: データベースセッション

    Returns:
        StoryResponse: 作成されたストーリー

    Raises:
        HTTPException: エラー発生時
    """
    try:
        # None または 空ボディ（{}）の場合はAI自動生成
        if request is None:
            # AI自動生成フロー
            generation_service = StoryGenerationService(db)
            story = generation_service.generate_story(inquiry_id)
        else:
            # 手動作成フロー
            # バリデーション
            validator = StoryValidator()
            validation_result = validator.validate_create_request(request)
            if not validation_result.valid:
                first_error = validation_result.errors[0]
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=_create_error_response(
                        code=first_error.code,
                        message=first_error.message,
                        field=first_error.field,
                    ).model_dump(),
                )

            # ストーリー作成
            repository = StoryRepository(db)
            create_data = CreateStoryData(
                inquiry_id=inquiry_id,
                title=request.title,
                description=request.description,
                priority=request.priority,
                estimated_effort=request.estimated_effort,
                deadline=request.deadline,
                assignee=request.assignee,
            )
            story = repository.create(create_data)

        # レスポンス作成
        return StoryResponse.model_validate(story)

    except HTTPException:
        # HTTPExceptions are already handled, re-raise
        raise
    except InquiryNotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=_create_error_response(
                code="GS-204",
                message=f"問い合わせID={inquiry_id}が見つかりません",
            ).model_dump(),
        )
    except InvalidInquiryStatusError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_create_error_response(
                code="GS-205",
                message=str(e),
            ).model_dump(),
        )
    except AIGenerationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_create_error_response(
                code="GS-206",
                message=f"AI生成に失敗しました: {str(e)}",
            ).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_create_error_response(
                code="GS-999",
                message=f"サーバーエラー: {str(e)}",
            ).model_dump(),
        )


# GET /api/stories - 全ストーリー一覧
@router.get(
    "/stories",
    response_model=PaginatedStoriesResponse,
    responses={
        400: {"model": ErrorResponse, "description": "パラメータ不正"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def list_all_stories(
    status: Optional[StoryStatus] = Query(None, description="ステータスフィルター"),
    priority: Optional[Priority] = Query(None, description="優先度フィルター"),
    inquiry_id: Optional[int] = Query(None, description="問い合わせIDフィルター"),
    sort_by: SortField = Query(SortField.CREATED_AT, description="ソートフィールド"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="ソート順"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(20, ge=1, le=100, description="ページサイズ"),
    db: Session = Depends(get_db),
) -> PaginatedStoriesResponse:
    """全ストーリー一覧を取得する.

    要件2.1-2.4: ストーリー一覧提供、ページネーション、フィルタリング、ソート

    Args:
        status: ステータスフィルター
        priority: 優先度フィルター
        inquiry_id: 問い合わせIDフィルター
        sort_by: ソートフィールド
        sort_order: ソート順
        page: ページ番号
        limit: ページサイズ
        db: データベースセッション

    Returns:
        PaginatedStoriesResponse: ページネーション付きストーリーリスト
    """
    try:
        query_service = StoryQueryService(db)
        list_request = ListStoriesRequest(
            status=status,
            priority=priority,
            inquiry_id=inquiry_id,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
            page=page,
            limit=limit,
        )
        result = query_service.list_stories(list_request)
        stories = result["data"]
        meta = result["meta"]

        return PaginatedStoriesResponse(
            data=[StoryResponse.model_validate(s) for s in stories],
            meta=PaginationMeta(
                page=meta["page"],
                limit=meta["limit"],
                total=meta["total"],
                has_next=meta["has_next"],
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except InvalidPaginationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=_create_error_response(code="GS-301", message=str(e)).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_create_error_response(
                code="GS-999", message=f"サーバーエラー: {str(e)}"
            ).model_dump(),
        )


# GET /api/inquiries/{inquiry_id}/stories - 問い合わせ配下のストーリー一覧
@router.get(
    "/inquiries/{inquiry_id}/stories",
    response_model=PaginatedStoriesResponse,
    responses={
        404: {"model": ErrorResponse, "description": "問い合わせが見つからない"},
        400: {"model": ErrorResponse, "description": "パラメータ不正"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def list_inquiry_stories(
    inquiry_id: int,
    status: Optional[StoryStatus] = Query(None, description="ステータスフィルター"),
    priority: Optional[Priority] = Query(None, description="優先度フィルター"),
    sort_by: SortField = Query(SortField.CREATED_AT, description="ソートフィールド"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="ソート順"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(20, ge=1, le=100, description="ページサイズ"),
    db: Session = Depends(get_db),
) -> PaginatedStoriesResponse:
    """問い合わせ配下のストーリー一覧を取得する.

    要件2.1-2.4: ストーリー一覧提供、ページネーション、フィルタリング、ソート

    Args:
        inquiry_id: 問い合わせID
        status: ステータスフィルター
        priority: 優先度フィルター
        sort_by: ソートフィールド
        sort_order: ソート順
        page: ページ番号
        limit: ページサイズ
        db: データベースセッション

    Returns:
        PaginatedStoriesResponse: ページネーション付きストーリーリスト
    """
    # 問い合わせID存在確認
    inquiry_repo = InquiryRepository(db)
    inquiry = inquiry_repo.find_by_id(inquiry_id)
    if not inquiry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=_create_error_response(
                code="GS-204",
                message=f"問い合わせID={inquiry_id}が見つかりません",
            ).model_dump(),
        )

    # inquiry_idでフィルタリング
    return await list_all_stories(
        status=status,
        priority=priority,
        inquiry_id=inquiry_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
        db=db,
    )


# GET /api/stories/{id} - ストーリー詳細
@router.get(
    "/stories/{id}",
    response_model=StoryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "ストーリーが見つからない"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def get_story(
    id: int,
    db: Session = Depends(get_db),
) -> StoryResponse:
    """ストーリー詳細を取得する.

    要件2.5: ストーリー詳細表示

    Args:
        id: ストーリーID
        db: データベースセッション

    Returns:
        StoryResponse: ストーリー詳細
    """
    try:
        repository = StoryRepository(db)
        story = repository.find_by_id(id)
        if not story:
            raise StoryNotFoundError(id)

        return StoryResponse.model_validate(story)
    except StoryNotFoundError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=_create_error_response(code="GS-302", message=str(e)).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_create_error_response(
                code="GS-999", message=f"サーバーエラー: {str(e)}"
            ).model_dump(),
        )


# PUT /api/stories/{id} - ストーリー更新
@router.put(
    "/stories/{id}",
    response_model=StoryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "バリデーションエラー"},
        404: {"model": ErrorResponse, "description": "ストーリーが見つからない"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def update_story(
    id: int,
    request: UpdateStoryRequest,
    db: Session = Depends(get_db),
) -> StoryResponse:
    """ストーリーを更新する.

    要件2.6-2.9: ストーリー編集、バリデーション、変更内容保存、更新日時自動記録

    Args:
        id: ストーリーID
        request: 更新リクエスト
        db: データベースセッション

    Returns:
        StoryResponse: 更新されたストーリー
    """
    try:
        # バリデーション
        validator = StoryValidator()
        validation_result = validator.validate_update_request(request)
        if not validation_result.valid:
            first_error = validation_result.errors[0]
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=_create_error_response(
                    code=first_error.code,
                    message=first_error.message,
                    field=first_error.field,
                ).model_dump(),
            )

        # 更新
        repository = StoryRepository(db)
        update_data = UpdateStoryData(
            title=request.title,
            description=request.description,
            priority=request.priority,
            estimated_effort=request.estimated_effort,
            deadline=request.deadline,
            assignee=request.assignee,
        )
        story = repository.update(id, update_data)
        if not story:
            raise StoryNotFoundError(id)

        return StoryResponse.model_validate(story)
    except StoryNotFoundError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=_create_error_response(code="GS-302", message=str(e)).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_create_error_response(
                code="GS-999", message=f"サーバーエラー: {str(e)}"
            ).model_dump(),
        )


# DELETE /api/stories/{id} - ストーリー削除
@router.delete(
    "/stories/{id}",
    response_model=DeleteStoryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "ストーリーが見つからない"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def delete_story(
    id: int,
    db: Session = Depends(get_db),
) -> DeleteStoryResponse:
    """ストーリーを削除する.

    要件2.15-2.17: ストーリー削除

    Args:
        id: ストーリーID
        db: データベースセッション

    Returns:
        DeleteStoryResponse: 削除成功
    """
    try:
        repository = StoryRepository(db)
        # Check if story exists before deleting
        story = repository.find_by_id(id)
        if not story:
            raise StoryNotFoundError(id)

        repository.delete(id)
        return DeleteStoryResponse(success=True)
    except StoryNotFoundError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=_create_error_response(code="GS-302", message=str(e)).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_create_error_response(
                code="GS-999", message=f"サーバーエラー: {str(e)}"
            ).model_dump(),
        )


# POST /api/stories/{id}/approve - ストーリー承認
@router.post(
    "/stories/{id}/approve",
    response_model=StoryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "バリデーションエラー"},
        404: {"model": ErrorResponse, "description": "ストーリーが見つからない"},
        422: {"model": ErrorResponse, "description": "ステータス遷移不正"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def approve_story(
    id: int,
    request: ApproveStoryRequest,
    db: Session = Depends(get_db),
) -> StoryResponse:
    """ストーリーを承認する.

    要件3.1-3.3: 承認時のステータス検証、ステータス変更、承認日時と承認者の記録

    Args:
        id: ストーリーID
        request: 承認リクエスト
        db: データベースセッション

    Returns:
        StoryResponse: 承認されたストーリー
    """
    try:
        repository = StoryRepository(db)
        workflow_service = StoryWorkflowService(repository)
        story = workflow_service.approve_story(id, request.approver)
        return StoryResponse.model_validate(story)
    except StoryNotFoundError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=_create_error_response(code="GS-302", message=str(e)).model_dump(),
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_create_error_response(code="GS-203", message=str(e)).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_create_error_response(
                code="GS-999", message=f"サーバーエラー: {str(e)}"
            ).model_dump(),
        )


# POST /api/stories/{id}/reject - ストーリー却下
@router.post(
    "/stories/{id}/reject",
    response_model=StoryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "却下理由未入力"},
        404: {"model": ErrorResponse, "description": "ストーリーが見つからない"},
        422: {"model": ErrorResponse, "description": "ステータス遷移不正"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def reject_story(
    id: int,
    request: RejectStoryRequest,
    db: Session = Depends(get_db),
) -> StoryResponse:
    """ストーリーを却下する.

    要件3.4-3.7: 却下時のステータス検証、理由必須、ステータス変更、却下情報記録

    Args:
        id: ストーリーID
        request: 却下リクエスト
        db: データベースセッション

    Returns:
        StoryResponse: 却下されたストーリー
    """
    try:
        repository = StoryRepository(db)
        workflow_service = StoryWorkflowService(repository)
        story = workflow_service.reject_story(id, request.rejector, request.reason)
        return StoryResponse.model_validate(story)
    except StoryNotFoundError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=_create_error_response(code="GS-302", message=str(e)).model_dump(),
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_create_error_response(code="GS-203", message=str(e)).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_create_error_response(
                code="GS-999", message=f"サーバーエラー: {str(e)}"
            ).model_dump(),
        )


# POST /api/stories/batch-approve - 一括承認
@router.post(
    "/stories/batch-approve",
    response_model=BatchApproveResponse,
    responses={
        400: {"model": ErrorResponse, "description": "パラメータ不正"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def batch_approve_stories(
    request: BatchApproveRequest,
    db: Session = Depends(get_db),
) -> BatchApproveResponse:
    """複数ストーリーを一括承認する.

    要件3.10-3.11: 一括承認機能、個別検証

    Args:
        request: 一括承認リクエスト
        db: データベースセッション

    Returns:
        BatchApproveResponse: 各ストーリーの処理結果
    """
    try:
        repository = StoryRepository(db)
        workflow_service = StoryWorkflowService(repository)
        results = workflow_service.batch_approve(request.story_ids, request.approver)

        return BatchApproveResponse(
            results=[
                BatchApproveResult(id=story_id, success=success, error=error)
                for story_id, success, error in results
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_create_error_response(
                code="GS-999", message=f"サーバーエラー: {str(e)}"
            ).model_dump(),
        )

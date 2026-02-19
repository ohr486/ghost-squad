"""プロンプト管理API - CRUD、テスト実行、編集ロックエンドポイント.

Task 6.1: プロンプト一覧・詳細・更新
Task 6.2: テスト実行・リセット・編集ロック

Requirements: 1.1, 1.2, 1.3, 2.2, 2.5, 3.1, 3.2, 3.4, 4.4, 4.5
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session

from database import get_db
from models.enums.prompt_category import PromptCategory
from models.schemas.inquiry import ErrorResponse, ValidationErrorDetail
from models.schemas.prompt import (AcquireLockApiRequest, LockResponse,
                                   PromptListResponse, PromptResponse,
                                   TestPromptApiRequest, TestPromptApiResult,
                                   UpdatePromptApiRequest)
from services.prompt_service import (PromptEditLockError, PromptNotFoundError,
                                     PromptService, PromptTestError,
                                     PromptTestTimeoutError,
                                     PromptValidationError, TestPromptRequest,
                                     UpdatePromptRequest)

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


def _create_error_response(
    code: str, message: str, field: Optional[str] = None
) -> ErrorResponse:
    """エラーレスポンスを作成する."""
    return ErrorResponse(
        errors=[ValidationErrorDetail(code=code, message=message, field=field)],
        timestamp=datetime.now(timezone.utc),
    )


def _get_prompt_service(db: Session) -> PromptService:
    """PromptServiceインスタンスを取得する."""
    return PromptService(session=db)


# GET /api/prompts - プロンプト一覧取得
@router.get(
    "",
    response_model=PromptListResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "無効なカテゴリ",
        },
    },
)
async def list_prompts(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
) -> PromptListResponse:
    """プロンプト一覧を取得する.

    Args:
        category: カテゴリフィルタ（オプション）
        db: データベースセッション
    """
    try:
        service = _get_prompt_service(db)

        # カテゴリの変換
        cat_filter = None
        if category is not None:
            try:
                cat_filter = PromptCategory(category)
            except ValueError:
                error = _create_error_response(
                    "GS-403",
                    f"無効なカテゴリです: {category}",
                    "category",
                )
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=error.model_dump(),
                )

        prompts = service.list_prompts(category=cat_filter)

        return PromptListResponse(
            data=[_prompt_data_to_response(p) for p in prompts],
            total=len(prompts),
        )
    except HTTPException:
        raise
    except Exception as e:
        error = _create_error_response(
            "GS-010",
            f"サーバーエラー: {e}",
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump(),
        )


# GET /api/prompts/{key} - プロンプト詳細取得
@router.get(
    "/{key}",
    response_model=PromptResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "プロンプトが見つからない",
        },
    },
)
async def get_prompt(
    key: str,
    db: Session = Depends(get_db),
) -> PromptResponse:
    """プロンプト詳細を取得する.

    Args:
        key: プロンプトキー
        db: データベースセッション
    """
    try:
        service = _get_prompt_service(db)
        prompt = service.get_prompt(key)
        return _prompt_data_to_response(prompt)
    except PromptNotFoundError as e:
        error = _create_error_response("GS-404", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=error.model_dump(),
        )
    except Exception as e:
        error = _create_error_response(
            "GS-010",
            f"サーバーエラー: {e}",
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump(),
        )


# PUT /api/prompts/{key} - プロンプト更新
@router.put(
    "/{key}",
    response_model=PromptResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "バリデーションエラー",
        },
        404: {
            "model": ErrorResponse,
            "description": "プロンプトが見つからない",
        },
        409: {
            "model": ErrorResponse,
            "description": "編集ロック競合",
        },
    },
)
async def update_prompt(
    key: str,
    request: UpdatePromptApiRequest,
    db: Session = Depends(get_db),
) -> PromptResponse:
    """プロンプトを更新する.

    Args:
        key: プロンプトキー
        request: 更新リクエスト
        db: データベースセッション
    """
    try:
        service = _get_prompt_service(db)
        svc_request = UpdatePromptRequest(
            content=request.content,
            description=request.description,
        )
        prompt = service.update_prompt(key, svc_request)
        return _prompt_data_to_response(prompt)
    except PromptNotFoundError as e:
        error = _create_error_response("GS-404", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=error.model_dump(),
        )
    except PromptValidationError as e:
        error = _create_error_response("GS-401", str(e), "content")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=error.model_dump(),
        )
    except PromptEditLockError as e:
        error = _create_error_response("GS-405", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=error.model_dump(),
        )
    except Exception as e:
        error = _create_error_response(
            "GS-010",
            f"サーバーエラー: {e}",
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump(),
        )


# POST /api/prompts/{key}/reset - デフォルトリセット
@router.post(
    "/{key}/reset",
    response_model=PromptResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "プロンプトが見つからない",
        },
    },
)
async def reset_prompt(
    key: str,
    db: Session = Depends(get_db),
) -> PromptResponse:
    """プロンプトをデフォルト値にリセットする.

    Args:
        key: プロンプトキー
        db: データベースセッション
    """
    try:
        service = _get_prompt_service(db)
        prompt = service.reset_to_default(key)
        return _prompt_data_to_response(prompt)
    except PromptNotFoundError as e:
        error = _create_error_response("GS-404", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=error.model_dump(),
        )
    except Exception as e:
        error = _create_error_response(
            "GS-010",
            f"サーバーエラー: {e}",
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump(),
        )


# POST /api/prompts/{key}/lock - 編集ロック取得
@router.post(
    "/{key}/lock",
    response_model=LockResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "プロンプトが見つからない",
        },
        409: {
            "model": ErrorResponse,
            "description": "編集ロック競合",
        },
    },
)
async def acquire_lock(
    key: str,
    request: AcquireLockApiRequest,
    db: Session = Depends(get_db),
) -> LockResponse:
    """編集ロックを取得する.

    Args:
        key: プロンプトキー
        request: ロック取得リクエスト
        db: データベースセッション
    """
    try:
        service = _get_prompt_service(db)
        result = service.acquire_edit_lock(key, request.user_id)

        if not result.acquired:
            error = _create_error_response(
                result.error_code or "GS-405",
                result.error_message or "他のユーザーが編集中です",
            )
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=error.model_dump(),
            )

        return LockResponse(
            acquired=True,
            locked_by=result.locked_by,
            locked_since=result.locked_since,
        )
    except PromptNotFoundError as e:
        error = _create_error_response("GS-404", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=error.model_dump(),
        )
    except HTTPException:
        raise
    except Exception as e:
        error = _create_error_response(
            "GS-010",
            f"サーバーエラー: {e}",
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump(),
        )


# DELETE /api/prompts/{key}/lock - 編集ロック解放
@router.delete(
    "/{key}/lock",
    status_code=http_status.HTTP_204_NO_CONTENT,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "プロンプトが見つからない",
        },
    },
)
async def release_lock(
    key: str,
    db: Session = Depends(get_db),
) -> None:
    """編集ロックを解放する.

    Args:
        key: プロンプトキー
        db: データベースセッション
    """
    try:
        service = _get_prompt_service(db)
        service.release_edit_lock(key, "")
    except PromptNotFoundError as e:
        error = _create_error_response("GS-404", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=error.model_dump(),
        )
    except Exception as e:
        error = _create_error_response(
            "GS-010",
            f"サーバーエラー: {e}",
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump(),
        )


# POST /api/prompts/test - テスト実行
@router.post(
    "/test",
    response_model=TestPromptApiResult,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "バリデーションエラー",
        },
        504: {
            "model": ErrorResponse,
            "description": "テスト実行タイムアウト",
        },
    },
)
async def test_prompt(
    request: TestPromptApiRequest,
    db: Session = Depends(get_db),
) -> TestPromptApiResult:
    """プロンプトをテスト実行する.

    Args:
        request: テスト実行リクエスト
        db: データベースセッション
    """
    try:
        service = PromptService(session=db)
        svc_request = TestPromptRequest(
            content=request.content,
            variables=request.variables,
            provider=request.provider,
        )
        result = service.test_prompt(svc_request)

        return TestPromptApiResult(
            output=result.output,
            provider=result.provider,
            model=result.model,
            elapsed_ms=result.elapsed_ms,
        )
    except PromptTestTimeoutError as e:
        error = _create_error_response("GS-406", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_504_GATEWAY_TIMEOUT,
            detail=error.model_dump(),
        )
    except PromptTestError as e:
        error = _create_error_response("GS-407", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump(),
        )
    except Exception as e:
        error = _create_error_response(
            "GS-010",
            f"サーバーエラー: {e}",
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump(),
        )


def _prompt_data_to_response(prompt_data) -> PromptResponse:
    """PromptDataをPromptResponseに変換する."""
    return PromptResponse(
        id=prompt_data.id,
        key=prompt_data.key,
        name=prompt_data.name,
        description=prompt_data.description,
        category=prompt_data.category,
        content=prompt_data.content,
        default_content=prompt_data.default_content,
        variables=prompt_data.variables,
        is_modified=prompt_data.is_modified,
        editing_by=prompt_data.editing_by,
        editing_since=prompt_data.editing_since,
        created_at=prompt_data.created_at,
        updated_at=prompt_data.updated_at,
    )

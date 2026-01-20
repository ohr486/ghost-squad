"""Importer API - プラグイン管理、AIプロバイダー管理、インポート実行.

タスク10.1: プラグイン管理APIの実装
- GET /api/plugins - プラグイン一覧取得
- POST /api/plugins/{type}/enable - プラグイン有効化
- POST /api/plugins/{type}/disable - プラグイン無効化

タスク10.2: AIプロバイダー管理APIの実装
- GET /api/ai-providers - プロバイダー一覧取得
- POST /api/ai-providers/{type}/set-default - デフォルト設定

タスク10.3: インポート実行APIの実装
- POST /api/importers/execute - インポート実行
- POST /api/importers/retry - リトライ実行

Requirements: 1.1, 1.2, 2.1-2.6, 3.1-3.6, 4.1-4.5, 5.2
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session

from database import get_db
from models.schemas.importer import (AIProviderListResponse,
                                     AIProviderStatusResponse, ErrorResponse,
                                     ExecuteImportRequest, ImportErrorResponse,
                                     ImportResultResponse, PluginListResponse,
                                     PluginStatusResponse, RetryImportRequest,
                                     ValidationErrorDetail)
from services.importer.ai_provider_base import AIProviderType
from services.importer.ai_provider_registry import AIProviderRegistryService
from services.importer.analysis_service import ImporterAnalysisService
from services.importer.importer_service import ImporterService, ImportResult
from services.importer.plugin_registry import PluginRegistryService

router = APIRouter(prefix="/api", tags=["importer"])

# グローバルなPluginRegistryServiceインスタンス
# （アプリケーション起動時に初期化される）
_plugin_registry: Optional[PluginRegistryService] = None


def get_plugin_registry() -> PluginRegistryService:
    """PluginRegistryServiceインスタンスを取得する.

    Returns:
        PluginRegistryService: プラグイン管理サービスインスタンス
    """
    global _plugin_registry
    if _plugin_registry is None:
        _plugin_registry = PluginRegistryService()
    return _plugin_registry


def set_plugin_registry(registry: PluginRegistryService) -> None:
    """PluginRegistryServiceインスタンスを設定する.

    テスト用にサービスインスタンスを差し替える際に使用。

    Args:
        registry: 設定するPluginRegistryServiceインスタンス
    """
    global _plugin_registry
    _plugin_registry = registry


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


# =============================================================================
# プラグイン管理API（タスク10.1）
# =============================================================================


@router.get(
    "/plugins",
    response_model=PluginListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def list_plugins() -> PluginListResponse:
    """登録済みプラグイン一覧を取得する.

    要件1.1: プラグイン登録・解除

    Returns:
        PluginListResponse: プラグイン一覧

    Raises:
        HTTPException: サーバーエラー
    """
    try:
        registry = get_plugin_registry()
        plugins = registry.list_plugins()

        return PluginListResponse(
            data=[
                PluginStatusResponse(
                    plugin_type=p.plugin_type,
                    enabled=p.enabled,
                    initialized=p.initialized,
                    error_message=p.error_message,
                )
                for p in plugins
            ],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        error_response = _create_error_response(
            "GS-310", f"プラグイン一覧の取得に失敗しました: {str(e)}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


@router.post(
    "/plugins/{plugin_type}/enable",
    response_model=PluginStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "プラグインが見つかりません"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def enable_plugin(plugin_type: str) -> PluginStatusResponse:
    """プラグインを有効化する.

    要件1.2: 有効/無効切り替え

    Args:
        plugin_type: プラグイン種別（例: email, sentry）

    Returns:
        PluginStatusResponse: 有効化後のプラグインステータス

    Raises:
        HTTPException: プラグインが見つからない、またはサーバーエラー
    """
    try:
        registry = get_plugin_registry()
        result = registry.enable(plugin_type)

        if result.is_err:
            error = result.unwrap_err()
            error_response = _create_error_response(error.code, error.message)
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=error_response.model_dump(),
            )

        plugin_status = result.unwrap()
        return PluginStatusResponse(
            plugin_type=plugin_status.plugin_type,
            enabled=plugin_status.enabled,
            initialized=plugin_status.initialized,
            error_message=plugin_status.error_message,
        )
    except HTTPException:
        raise
    except Exception as e:
        error_response = _create_error_response("GS-302", f"プラグイン有効化に失敗しました: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


@router.post(
    "/plugins/{plugin_type}/disable",
    response_model=PluginStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "プラグインが見つかりません"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def disable_plugin(plugin_type: str) -> PluginStatusResponse:
    """プラグインを無効化する.

    要件1.2: 有効/無効切り替え

    Args:
        plugin_type: プラグイン種別（例: email, sentry）

    Returns:
        PluginStatusResponse: 無効化後のプラグインステータス

    Raises:
        HTTPException: プラグインが見つからない、またはサーバーエラー
    """
    try:
        registry = get_plugin_registry()
        result = registry.disable(plugin_type)

        if result.is_err:
            error = result.unwrap_err()
            error_response = _create_error_response(error.code, error.message)
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=error_response.model_dump(),
            )

        plugin_status = result.unwrap()
        return PluginStatusResponse(
            plugin_type=plugin_status.plugin_type,
            enabled=plugin_status.enabled,
            initialized=plugin_status.initialized,
            error_message=plugin_status.error_message,
        )
    except HTTPException:
        raise
    except Exception as e:
        error_response = _create_error_response("GS-310", f"プラグイン無効化に失敗しました: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


# =============================================================================
# AIプロバイダー管理API（タスク10.2）
# =============================================================================

# グローバルなAIProviderRegistryServiceインスタンス
_ai_provider_registry: Optional[AIProviderRegistryService] = None


def get_ai_provider_registry() -> AIProviderRegistryService:
    """AIProviderRegistryServiceインスタンスを取得する.

    Returns:
        AIProviderRegistryService: AIプロバイダー管理サービスインスタンス
    """
    global _ai_provider_registry
    if _ai_provider_registry is None:
        _ai_provider_registry = AIProviderRegistryService()
    return _ai_provider_registry


def set_ai_provider_registry(registry: AIProviderRegistryService) -> None:
    """AIProviderRegistryServiceインスタンスを設定する.

    テスト用にサービスインスタンスを差し替える際に使用。

    Args:
        registry: 設定するAIProviderRegistryServiceインスタンス
    """
    global _ai_provider_registry
    _ai_provider_registry = registry


def _parse_provider_type(provider_type_str: str) -> Optional[AIProviderType]:
    """文字列からAIProviderTypeを解析する.

    Args:
        provider_type_str: プロバイダー種別文字列（例: openai, anthropic）

    Returns:
        Optional[AIProviderType]: 解析結果（無効な場合はNone）
    """
    try:
        return AIProviderType(provider_type_str.lower())
    except ValueError:
        return None


@router.get(
    "/ai-providers",
    response_model=AIProviderListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def list_ai_providers() -> AIProviderListResponse:
    """登録済みAIプロバイダー一覧を取得する.

    要件3.1: カテゴリ判定

    Returns:
        AIProviderListResponse: AIプロバイダー一覧

    Raises:
        HTTPException: サーバーエラー
    """
    try:
        registry = get_ai_provider_registry()
        providers = registry.list_providers()

        return AIProviderListResponse(
            data=[
                AIProviderStatusResponse(
                    provider_type=p.provider_type.value,
                    enabled=p.enabled,
                    initialized=p.initialized,
                    is_default=p.is_default,
                    model=p.model,
                    error_message=p.error_message,
                )
                for p in providers
            ],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        error_response = _create_error_response(
            "GS-309", f"AIプロバイダー一覧の取得に失敗しました: {str(e)}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


@router.post(
    "/ai-providers/{provider_type}/set-default",
    response_model=AIProviderStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "AIプロバイダーが見つかりません"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def set_default_ai_provider(provider_type: str) -> AIProviderStatusResponse:
    """デフォルトAIプロバイダーを設定する.

    要件3.1: カテゴリ判定

    Args:
        provider_type: プロバイダー種別（例: openai, anthropic）

    Returns:
        AIProviderStatusResponse: 設定後のプロバイダーステータス

    Raises:
        HTTPException: プロバイダーが見つからない、またはサーバーエラー
    """
    try:
        registry = get_ai_provider_registry()

        # 文字列からAIProviderTypeを解析
        parsed_type = _parse_provider_type(provider_type)
        if parsed_type is None:
            error_response = _create_error_response(
                "GS-308", f"AIプロバイダー '{provider_type}' が見つかりません"
            )
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=error_response.model_dump(),
            )

        result = registry.set_default(parsed_type)

        if result.is_err:
            error = result.unwrap_err()
            error_response = _create_error_response(error.code, error.message)
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=error_response.model_dump(),
            )

        provider_status = result.unwrap()
        return AIProviderStatusResponse(
            provider_type=provider_status.provider_type.value,
            enabled=provider_status.enabled,
            initialized=provider_status.initialized,
            is_default=provider_status.is_default,
            model=provider_status.model,
            error_message=provider_status.error_message,
        )
    except HTTPException:
        raise
    except Exception as e:
        error_response = _create_error_response(
            "GS-309", f"デフォルトAIプロバイダー設定に失敗しました: {str(e)}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


# =============================================================================
# ImporterService管理（タスク10.3用）
# =============================================================================

_importer_service: Optional[ImporterService] = None


def get_importer_service(db: Session = Depends(get_db)) -> ImporterService:
    """ImporterServiceインスタンスを取得する.

    依存関係注入で使用。テスト時はset_importer_serviceで差し替え可能。

    Args:
        db: データベースセッション

    Returns:
        ImporterService: インポートサービスインスタンス
    """
    global _importer_service
    if _importer_service is not None:
        return _importer_service

    plugin_registry = get_plugin_registry()
    ai_provider_registry = get_ai_provider_registry()
    analysis_service = ImporterAnalysisService(ai_provider_registry)
    return ImporterService(
        session=db,
        plugin_registry=plugin_registry,
        analysis_service=analysis_service,
    )


def set_importer_service(service: Optional[ImporterService]) -> None:
    """ImporterServiceインスタンスを設定する.

    テスト用にサービスインスタンスを差し替える際に使用。

    Args:
        service: 設定するImporterServiceインスタンス（Noneでリセット）
    """
    global _importer_service
    _importer_service = service


def _determine_error_status_code(error_code: str) -> int:
    """エラーコードから適切なHTTPステータスコードを決定する.

    Args:
        error_code: エラーコード（GS-xxx形式）

    Returns:
        int: HTTPステータスコード
    """
    # 404系: プラグイン/プロバイダーが見つからない
    if error_code in ("GS-301", "GS-308"):
        return http_status.HTTP_404_NOT_FOUND
    # 500系: 接続エラー、データ取得エラー等
    return http_status.HTTP_500_INTERNAL_SERVER_ERROR


def _validate_ai_provider(provider_type_str: Optional[str]) -> Optional[AIProviderType]:
    """AIプロバイダー種別を検証し、パースする.

    Args:
        provider_type_str: プロバイダー種別文字列（指定時のみ）

    Returns:
        Optional[AIProviderType]: パース済みのプロバイダー種別

    Raises:
        HTTPException: 無効なプロバイダー種別が指定された場合
    """
    if not provider_type_str:
        return None

    ai_provider_type = _parse_provider_type(provider_type_str)
    if ai_provider_type is None:
        error_response = _create_error_response(
            "GS-308",
            f"AIプロバイダー '{provider_type_str}' が見つかりません",
        )
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=error_response.model_dump(),
        )
    return ai_provider_type


def _create_import_result_response(import_result: ImportResult) -> ImportResultResponse:
    """インポート結果からレスポンスを作成する.

    Args:
        import_result: インポート結果オブジェクト

    Returns:
        ImportResultResponse: API応答用のレスポンス
    """
    return ImportResultResponse(
        total_fetched=import_result.total_fetched,
        total_imported=import_result.total_imported,
        total_skipped=import_result.total_skipped,
        total_failed=import_result.total_failed,
        imported_inquiry_ids=import_result.imported_inquiry_ids,
        errors=[
            ImportErrorResponse(
                source_id=e.source_id,
                error_code=e.error_code,
                error_message=e.error_message,
            )
            for e in import_result.errors
        ],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# =============================================================================
# インポート実行API（タスク10.3）
# =============================================================================


@router.post(
    "/importers/execute",
    response_model=ImportResultResponse,
    responses={
        404: {"model": ErrorResponse, "description": "プラグインまたはAIプロバイダーが見つかりません"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def execute_import(
    request: ExecuteImportRequest,
    service: ImporterService = Depends(get_importer_service),
) -> ImportResultResponse:
    """インポートを実行する.

    指定されたデータソースプラグインからデータを取得し、
    AI解析を行い、問い合わせとして登録する。

    要件2.1-2.6: メールインポート
    要件4.1-4.5: 問い合わせ自動生成

    Args:
        request: インポート実行リクエスト
        service: ImporterServiceインスタンス

    Returns:
        ImportResultResponse: インポート結果

    Raises:
        HTTPException: プラグインが見つからない、接続エラー等
    """
    try:
        # AIプロバイダー種別を検証
        ai_provider_type = _validate_ai_provider(request.ai_provider_type)

        result = service.execute_import(
            plugin_type=request.plugin_type,
            ai_provider_type=ai_provider_type,
        )

        if result.is_err:
            error = result.unwrap_err()
            error_response = _create_error_response(error.code, error.message)
            raise HTTPException(
                status_code=_determine_error_status_code(error.code),
                detail=error_response.model_dump(),
            )

        import_result = result.unwrap()
        return _create_import_result_response(import_result)
    except HTTPException:
        raise
    except Exception as e:
        error_response = _create_error_response("GS-306", f"インポート実行に失敗しました: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


@router.post(
    "/importers/retry",
    response_model=ImportResultResponse,
    responses={
        404: {"model": ErrorResponse, "description": "プラグインまたはAIプロバイダーが見つかりません"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
async def retry_import(
    request: RetryImportRequest,
    service: ImporterService = Depends(get_importer_service),
) -> ImportResultResponse:
    """失敗したインポートをリトライする.

    指定されたソースIDのデータを再取得・再解析し、
    問い合わせとして登録する。

    要件5.2: 手動リトライ

    Args:
        request: リトライリクエスト
        service: ImporterServiceインスタンス

    Returns:
        ImportResultResponse: リトライ結果

    Raises:
        HTTPException: プラグインが見つからない、接続エラー等
    """
    try:
        # AIプロバイダー種別を検証
        ai_provider_type = _validate_ai_provider(request.ai_provider_type)

        result = service.retry_failed(
            plugin_type=request.plugin_type,
            source_ids=request.source_ids,
            ai_provider_type=ai_provider_type,
        )

        if result.is_err:
            error = result.unwrap_err()
            error_response = _create_error_response(error.code, error.message)
            raise HTTPException(
                status_code=_determine_error_status_code(error.code),
                detail=error_response.model_dump(),
            )

        import_result = result.unwrap()
        return _create_import_result_response(import_result)
    except HTTPException:
        raise
    except Exception as e:
        error_response = _create_error_response("GS-306", f"リトライ実行に失敗しました: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )

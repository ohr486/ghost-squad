"""Importer API - プラグイン管理、AIプロバイダー管理、インポート実行.

タスク10.1: プラグイン管理APIの実装
- GET /api/plugins - プラグイン一覧取得
- POST /api/plugins/{type}/enable - プラグイン有効化
- POST /api/plugins/{type}/disable - プラグイン無効化

タスク10.2: AIプロバイダー管理APIの実装
- GET /api/ai-providers - プロバイダー一覧取得
- POST /api/ai-providers/{type}/set-default - デフォルト設定

Requirements: 1.1, 1.2, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from models.schemas.importer import (AIProviderListResponse,
                                     AIProviderStatusResponse, ErrorResponse,
                                     PluginListResponse, PluginStatusResponse,
                                     ValidationErrorDetail)
from services.importer.ai_provider_base import AIProviderType
from services.importer.ai_provider_registry import AIProviderRegistryService
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

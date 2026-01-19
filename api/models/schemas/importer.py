"""Importer用Pydanticスキーマ.

プラグイン管理、AIプロバイダー管理、インポート実行のAPIスキーマを提供する。
"""

from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_serializers import PlainSerializer

# ISO 8601形式でシリアライズするdatetimeアノテーション
IsoDatetime = Annotated[
    datetime, PlainSerializer(lambda v: v.isoformat(), return_type=str)
]


# =============================================================================
# プラグイン管理スキーマ（タスク10.1）
# =============================================================================


class PluginStatusResponse(BaseModel):
    """プラグインステータスレスポンス.

    要件1.1, 1.2: プラグイン登録・有効/無効管理
    """

    plugin_type: str = Field(
        ...,
        description="プラグイン種別（例: email, sentry）",
    )
    enabled: bool = Field(
        ...,
        description="プラグインが有効かどうか",
    )
    initialized: bool = Field(
        ...,
        description="プラグインが正常に初期化されたかどうか",
    )
    error_message: Optional[str] = Field(
        None,
        description="初期化失敗時のエラーメッセージ",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plugin_type": "email",
                "enabled": True,
                "initialized": True,
                "error_message": None,
            }
        }
    )


class PluginListResponse(BaseModel):
    """プラグイン一覧レスポンス.

    要件1.1: プラグイン登録・解除
    """

    data: List[PluginStatusResponse] = Field(
        ...,
        description="プラグインステータスリスト",
    )
    timestamp: str = Field(
        ...,
        description="レスポンスタイムスタンプ（ISO 8601形式）",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [
                    {
                        "plugin_type": "email",
                        "enabled": True,
                        "initialized": True,
                        "error_message": None,
                    }
                ],
                "timestamp": "2024-01-01T00:00:00+00:00",
            }
        }
    )


# =============================================================================
# AIプロバイダー管理スキーマ（タスク10.2）
# =============================================================================


class AIProviderStatusResponse(BaseModel):
    """AIプロバイダーステータスレスポンス.

    要件3.1-3.6: AI解析機能
    """

    provider_type: str = Field(
        ...,
        description="プロバイダー種別（例: openai, anthropic）",
    )
    enabled: bool = Field(
        ...,
        description="プロバイダーが有効かどうか",
    )
    initialized: bool = Field(
        ...,
        description="プロバイダーが正常に初期化されたかどうか",
    )
    is_default: bool = Field(
        ...,
        description="デフォルトプロバイダーかどうか",
    )
    model: str = Field(
        ...,
        description="使用しているモデル名",
    )
    error_message: Optional[str] = Field(
        None,
        description="初期化失敗時のエラーメッセージ",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "provider_type": "openai",
                "enabled": True,
                "initialized": True,
                "is_default": True,
                "model": "gpt-4",
                "error_message": None,
            }
        }
    )


class AIProviderListResponse(BaseModel):
    """AIプロバイダー一覧レスポンス.

    要件3.1: カテゴリ判定
    """

    data: List[AIProviderStatusResponse] = Field(
        ...,
        description="プロバイダーステータスリスト",
    )
    timestamp: str = Field(
        ...,
        description="レスポンスタイムスタンプ（ISO 8601形式）",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [
                    {
                        "provider_type": "openai",
                        "enabled": True,
                        "initialized": True,
                        "is_default": True,
                        "model": "gpt-4",
                        "error_message": None,
                    }
                ],
                "timestamp": "2024-01-01T00:00:00+00:00",
            }
        }
    )


# =============================================================================
# 共通エラースキーマ
# =============================================================================


class ValidationErrorDetail(BaseModel):
    """バリデーションエラー詳細.

    エラーコード体系:
    - GS-301: プラグイン未検出
    - GS-302: プラグイン初期化失敗
    - GS-308: AIプロバイダー未登録
    - GS-309: AIプロバイダー初期化失敗
    """

    code: str = Field(
        ...,
        description="エラーコード（GS-xxx形式）",
    )
    message: str = Field(
        ...,
        description="エラーメッセージ（日本語）",
    )
    field: Optional[str] = Field(
        None,
        description="エラーが発生したフィールド名",
    )


class ErrorResponse(BaseModel):
    """エラーレスポンス.

    統一されたエラーレスポンスフォーマット。
    """

    errors: List[ValidationErrorDetail] = Field(
        ...,
        description="エラー詳細リスト",
    )
    timestamp: IsoDatetime = Field(
        ...,
        description="エラー発生タイムスタンプ",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "errors": [
                    {
                        "code": "GS-301",
                        "message": "プラグイン 'unknown' が見つかりません",
                        "field": None,
                    }
                ],
                "timestamp": "2024-01-01T00:00:00+00:00",
            }
        }
    )


# =============================================================================
# インポート実行スキーマ（タスク10.3）
# =============================================================================


class ExecuteImportRequest(BaseModel):
    """インポート実行リクエスト.

    要件2.1-2.6, 4.1-4.5: メールインポートと問い合わせ生成
    """

    plugin_type: str = Field(
        ...,
        description="データソースプラグイン種別（例: email）",
        min_length=1,
        max_length=50,
    )
    ai_provider_type: Optional[str] = Field(
        None,
        description="AIプロバイダー種別（例: openai, anthropic）。未指定時はデフォルト使用",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plugin_type": "email",
                "ai_provider_type": "openai",
            }
        }
    )


class RetryImportRequest(BaseModel):
    """インポートリトライリクエスト.

    要件5.2: 手動リトライ機能
    """

    plugin_type: str = Field(
        ...,
        description="データソースプラグイン種別（例: email）",
        min_length=1,
        max_length=50,
    )
    source_ids: List[str] = Field(
        ...,
        description="リトライ対象のソースIDリスト",
        min_length=1,
    )
    ai_provider_type: Optional[str] = Field(
        None,
        description="AIプロバイダー種別（例: openai, anthropic）。未指定時はデフォルト使用",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plugin_type": "email",
                "source_ids": [
                    "<message-id-1@example.com>",
                    "<message-id-2@example.com>",
                ],
                "ai_provider_type": None,
            }
        }
    )


class ImportErrorResponse(BaseModel):
    """インポートエラー情報.

    要件5.1: エラーログ出力
    """

    source_id: str = Field(
        ...,
        description="エラーが発生したソースID",
    )
    error_code: str = Field(
        ...,
        description="エラーコード（GS-3xx形式）",
    )
    error_message: str = Field(
        ...,
        description="エラーメッセージ（日本語）",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "<message-id@example.com>",
                "error_code": "GS-304",
                "error_message": "AI解析に失敗しました",
            }
        }
    )


class ImportResultResponse(BaseModel):
    """インポート結果レスポンス.

    要件2.1-2.6, 4.1-4.5: インポート実行結果
    """

    total_fetched: int = Field(
        ...,
        description="取得件数",
        ge=0,
    )
    total_imported: int = Field(
        ...,
        description="インポート成功件数",
        ge=0,
    )
    total_skipped: int = Field(
        ...,
        description="スキップ件数（重複等）",
        ge=0,
    )
    total_failed: int = Field(
        ...,
        description="失敗件数",
        ge=0,
    )
    imported_inquiry_ids: List[int] = Field(
        ...,
        description="インポートされた問い合わせIDリスト",
    )
    errors: List[ImportErrorResponse] = Field(
        default_factory=list,
        description="エラー情報リスト",
    )
    timestamp: str = Field(
        ...,
        description="レスポンスタイムスタンプ（ISO 8601形式）",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_fetched": 10,
                "total_imported": 8,
                "total_skipped": 1,
                "total_failed": 1,
                "imported_inquiry_ids": [101, 102, 103, 104, 105, 106, 107, 108],
                "errors": [
                    {
                        "source_id": "<error-message@example.com>",
                        "error_code": "GS-304",
                        "error_message": "AI解析に失敗しました",
                    }
                ],
                "timestamp": "2024-01-01T00:00:00+00:00",
            }
        }
    )

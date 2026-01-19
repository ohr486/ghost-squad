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

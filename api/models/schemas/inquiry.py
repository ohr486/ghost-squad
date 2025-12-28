"""問い合わせ用Pydanticスキーマ.

APIリクエスト/レスポンスのシリアライゼーションとバリデーションを提供する。
"""

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.functional_serializers import PlainSerializer

from models.enums.inquiry_status import InquiryStatus

# ISO 8601形式でシリアライズするdatetimeアノテーション
IsoDatetime = Annotated[
    datetime, PlainSerializer(lambda v: v.isoformat(), return_type=str)
]


class CreateInquiryRequest(BaseModel):
    """問い合わせ作成リクエスト.

    要件1.4: 問い合わせ内容を必須項目として検証する
    """

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="ユーザーID（英数字とアンダースコア、最大50文字）",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="問い合わせ内容（必須、最大10,000文字）",
    )
    source_system: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="送信元システム（例: manual, email, chat）",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """contentが空白のみでないことを検証."""
        if not v.strip():
            raise ValueError("問い合わせ内容が空です")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "test_user",
                "content": "ログイン機能が欲しい",
                "source_system": "manual",
            }
        }
    )


class UpdateInquiryRequest(BaseModel):
    """問い合わせ更新リクエスト.

    要件2.8: 問い合わせ編集機能
    部分更新をサポートするため、すべてのフィールドはオプショナル。
    """

    content: Optional[str] = Field(
        None,
        min_length=1,
        max_length=10000,
        description="問い合わせ内容（最大10,000文字）",
    )
    source_system: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="送信元システム",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """contentが提供された場合、空白のみでないことを検証."""
        if v is not None and not v.strip():
            raise ValueError("問い合わせ内容が空です")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "更新されたログイン機能の要望",
                "source_system": "email",
            }
        }
    )


class InquiryResponse(BaseModel):
    """問い合わせレスポンス.

    要件2.4: 各問い合わせについて ID、内容、ステータス、タイムスタンプを含む情報を返す
    タイムスタンプはISO 8601形式でシリアライズされる。
    """

    id: int = Field(..., description="問い合わせID")
    user_id: str = Field(..., description="ユーザーID")
    content: str = Field(..., description="問い合わせ内容")
    source_system: str = Field(..., description="送信元システム")
    timestamp: IsoDatetime = Field(..., description="問い合わせタイムスタンプ")
    status: InquiryStatus = Field(..., description="問い合わせステータス")
    created_at: IsoDatetime = Field(..., description="作成日時")
    updated_at: IsoDatetime = Field(..., description="更新日時")

    model_config = ConfigDict(
        from_attributes=True,  # ORMモデルからの変換を許可
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": "test_user",
                "content": "ログイン機能が欲しい",
                "source_system": "manual",
                "timestamp": "2025-12-27T00:00:00Z",
                "status": "received",
                "created_at": "2025-12-27T00:00:00Z",
                "updated_at": "2025-12-27T00:00:00Z",
            }
        },
    )


class ValidationErrorDetail(BaseModel):
    """バリデーションエラー詳細.

    個別のバリデーションエラー情報を表現する。
    """

    code: str = Field(..., description="エラーコード（GS-xxx形式）")
    message: str = Field(..., description="エラーメッセージ（日本語）")
    field: Optional[str] = Field(None, description="エラーが発生したフィールド名")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "GS-001",
                "message": "問い合わせ内容が空です",
                "field": "content",
            }
        }
    )


class ErrorResponse(BaseModel):
    """エラーレスポンス.

    要件1.3: エラーメッセージを報告者に表示する
    すべてのAPIエラーレスポンスで使用される統一フォーマット。
    """

    errors: list[ValidationErrorDetail] = Field(..., description="エラー情報のリスト")
    timestamp: IsoDatetime = Field(..., description="エラー発生日時")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "errors": [
                    {
                        "code": "GS-001",
                        "message": "問い合わせ内容が空です",
                        "field": "content",
                    }
                ],
                "timestamp": "2025-12-27T00:00:00Z",
            }
        },
    )

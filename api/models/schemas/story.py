"""ストーリー用Pydanticスキーマ.

タスク 3.1: Pydanticスキーマを定義する
APIリクエスト/レスポンスのシリアライゼーションとバリデーションを提供する。
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.functional_serializers import PlainSerializer

from models.enums.priority import Priority
from models.enums.story_status import StoryStatus

# ISO 8601形式でシリアライズするdatetimeアノテーション
IsoDatetime = Annotated[
    datetime, PlainSerializer(lambda v: v.isoformat(), return_type=str)
]


class CreateStoryRequest(BaseModel):
    """ストーリー作成リクエスト (手動作成用).

    要件2.11, 2.12: 手動ストーリー作成とバリデーション
    inquiry_idはパスパラメータで指定されるため、このスキーマには含まない。
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="ストーリータイトル（必須、最大500文字）",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="ストーリー説明（必須、最大50,000文字）",
    )
    priority: Priority = Field(
        ...,
        description="優先度（LOW/MEDIUM/HIGH/URGENT）",
    )
    estimated_effort: Optional[float] = Field(
        None,
        ge=0,
        description="推定工数（オプショナル、0以上）",
    )
    deadline: Optional[datetime] = Field(
        None,
        description="期限（オプショナル）",
    )
    assignee: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="担当者（オプショナル、最大50文字）",
    )

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        """タイトルが空白のみでないことを検証 (要件4.5)."""
        if not v.strip():
            raise ValueError("タイトルが空です")
        return v

    @field_validator("description")
    @classmethod
    def validate_description_not_empty(cls, v: str) -> str:
        """説明が空白のみでないことを検証 (要件4.6)."""
        if not v.strip():
            raise ValueError("説明が空です")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "ログイン機能を追加",
                "description": "ユーザーがメールアドレスとパスワードでログインできるようにする",
                "priority": "medium",
                "estimated_effort": 5.0,
                "deadline": "2026-12-31T23:59:59Z",
                "assignee": "user123",
            }
        }
    )


class UpdateStoryRequest(BaseModel):
    """ストーリー更新リクエスト.

    要件2.7, 2.8: ストーリー編集機能
    部分更新をサポートするため、すべてのフィールドはオプショナル。
    """

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="ストーリータイトル（最大500文字）",
    )
    description: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50000,
        description="ストーリー説明（最大50,000文字）",
    )
    priority: Optional[Priority] = Field(
        None,
        description="優先度（LOW/MEDIUM/HIGH/URGENT）",
    )
    estimated_effort: Optional[float] = Field(
        None,
        ge=0,
        description="推定工数（0以上）",
    )
    deadline: Optional[datetime] = Field(
        None,
        description="期限",
    )
    assignee: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="担当者（最大50文字）",
    )

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """タイトルが提供された場合、空白のみでないことを検証."""
        if v is not None and not v.strip():
            raise ValueError("タイトルが空です")
        return v

    @field_validator("description")
    @classmethod
    def validate_description_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """説明が提供された場合、空白のみでないことを検証."""
        if v is not None and not v.strip():
            raise ValueError("説明が空です")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "更新されたログイン機能",
                "priority": "high",
            }
        }
    )


class ApprovalMetadata(BaseModel):
    """承認メタデータ.

    要件3.3: 承認日時と承認者の記録
    """

    approved_at: datetime = Field(..., description="承認日時")
    approver: str = Field(..., description="承認者")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "approved_at": "2026-01-01T12:00:00Z",
                "approver": "user123",
            }
        }
    )


class RejectionMetadata(BaseModel):
    """却下メタデータ.

    要件3.5, 3.7: 却下理由必須、却下情報の記録
    """

    rejected_at: datetime = Field(..., description="却下日時")
    rejector: str = Field(..., description="却下者")
    reason: str = Field(
        ...,
        min_length=1,
        description="却下理由（必須）",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason_not_empty(cls, v: str) -> str:
        """却下理由が空白のみでないことを検証."""
        if not v.strip():
            raise ValueError("却下理由が空です")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rejected_at": "2026-01-01T12:00:00Z",
                "rejector": "user456",
                "reason": "要件が不明瞭",
            }
        }
    )


class StatusHistoryEntry(BaseModel):
    """ステータス履歴エントリ.

    要件3.9: ステータス遷移履歴の記録
    """

    from_status: StoryStatus = Field(..., description="変更前ステータス")
    to_status: StoryStatus = Field(..., description="変更後ステータス")
    changed_at: datetime = Field(..., description="変更日時")
    changed_by: str = Field(..., description="変更者")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "from_status": "waiting_review",
                "to_status": "approved",
                "changed_at": "2026-01-01T12:00:00Z",
                "changed_by": "user123",
            }
        }
    )


class StoryMetadata(BaseModel):
    """ストーリーメタデータ.

    承認・却下情報、ステータス履歴を管理する。
    """

    approval: Optional[ApprovalMetadata] = Field(None, description="承認情報")
    rejection: Optional[RejectionMetadata] = Field(None, description="却下情報")
    status_history: List[StatusHistoryEntry] = Field(
        default_factory=list,
        description="ステータス変更履歴",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "approval": {
                    "approved_at": "2026-01-01T12:00:00Z",
                    "approver": "user123",
                },
                "status_history": [
                    {
                        "from_status": "waiting_review",
                        "to_status": "approved",
                        "changed_at": "2026-01-01T12:00:00Z",
                        "changed_by": "user123",
                    }
                ],
            }
        }
    )


class StoryResponse(BaseModel):
    """ストーリーレスポンス.

    要件2.5: ストーリー詳細表示
    要件4.1-4.11: すべてのフィールドを含む
    タイムスタンプはISO 8601形式でシリアライズされる。
    """

    id: int = Field(..., description="ストーリーID")
    inquiry_id: int = Field(..., description="問い合わせID")
    title: str = Field(..., description="ストーリータイトル")
    description: str = Field(..., description="ストーリー説明")
    priority: Priority = Field(..., description="優先度")
    status: StoryStatus = Field(..., description="ストーリーステータス")
    estimated_effort: Optional[float] = Field(None, description="推定工数")
    deadline: Optional[IsoDatetime] = Field(None, description="期限")
    assignee: Optional[str] = Field(None, description="担当者")
    story_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="ストーリーメタデータ（承認・却下情報、ステータス履歴など）",
    )
    created_at: IsoDatetime = Field(..., description="作成日時")
    updated_at: IsoDatetime = Field(..., description="更新日時")

    model_config = ConfigDict(
        from_attributes=True,  # ORMモデルからの変換を許可
        json_schema_extra={
            "example": {
                "id": 1,
                "inquiry_id": 100,
                "title": "ログイン機能を追加",
                "description": "ユーザーがメールアドレスとパスワードでログインできるようにする",
                "priority": "medium",
                "status": "waiting_review",
                "estimated_effort": 5.0,
                "deadline": "2026-12-31T23:59:59Z",
                "assignee": "user123",
                "story_metadata": {},
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T12:00:00Z",
            }
        },
    )

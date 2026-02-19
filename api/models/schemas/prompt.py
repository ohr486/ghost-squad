"""プロンプト管理用Pydanticスキーマ.

APIリクエスト/レスポンスのシリアライゼーションとバリデーションを提供する。

Requirements: 1.1, 1.2, 1.3, 2.2, 2.5, 3.1, 3.2, 3.4, 4.4, 4.5
"""

from datetime import datetime
from typing import Annotated, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_serializers import PlainSerializer

# ISO 8601形式でシリアライズするdatetimeアノテーション
IsoDatetime = Annotated[
    datetime, PlainSerializer(lambda v: v.isoformat(), return_type=str)
]


class PromptResponse(BaseModel):
    """プロンプトレスポンス.

    プロンプトの詳細情報を返却する。
    """

    id: int = Field(..., description="プロンプトID")
    key: str = Field(..., description="プロンプトキー")
    name: str = Field(..., description="表示名")
    description: Optional[str] = Field(None, description="説明")
    category: str = Field(..., description="カテゴリ")
    content: str = Field(..., description="現在のプロンプト本文")
    default_content: str = Field(..., description="デフォルトプロンプト本文")
    variables: List[str] = Field(default_factory=list, description="プレースホルダー変数リスト")
    is_modified: bool = Field(..., description="デフォルトから変更されているか")
    editing_by: Optional[str] = Field(None, description="編集中ユーザーID")
    editing_since: Optional[IsoDatetime] = Field(None, description="編集開始日時")
    created_at: IsoDatetime = Field(..., description="作成日時")
    updated_at: IsoDatetime = Field(..., description="更新日時")

    model_config = ConfigDict(from_attributes=True)


class PromptListResponse(BaseModel):
    """プロンプト一覧レスポンス."""

    data: List[PromptResponse] = Field(..., description="プロンプトリスト")
    total: int = Field(..., description="総件数")


class UpdatePromptApiRequest(BaseModel):
    """プロンプト更新リクエスト."""

    content: str = Field(..., min_length=1, description="プロンプト本文（必須）")
    description: Optional[str] = Field(None, description="説明（オプション）")


class TestPromptApiRequest(BaseModel):
    """プロンプトテスト実行リクエスト."""

    content: str = Field(..., min_length=1, description="テスト対象のプロンプト本文")
    variables: Dict[str, str] = Field(
        default_factory=dict,
        description="プレースホルダー変数の値",
    )
    provider: Optional[str] = Field(
        None,
        description="AIプロバイダー（openai/anthropic）",
    )


class TestPromptApiResult(BaseModel):
    """プロンプトテスト実行結果."""

    output: str = Field(..., description="AI出力結果")
    provider: str = Field(..., description="使用プロバイダー")
    model: str = Field(..., description="使用モデル")
    elapsed_ms: int = Field(..., description="実行時間（ミリ秒）")


class AcquireLockApiRequest(BaseModel):
    """編集ロック取得リクエスト."""

    user_id: str = Field(..., min_length=1, description="編集者ID")


class LockResponse(BaseModel):
    """編集ロックレスポンス."""

    acquired: bool = Field(..., description="ロック取得成功フラグ")
    locked_by: Optional[str] = Field(None, description="ロック保持者")
    locked_since: Optional[IsoDatetime] = Field(None, description="ロック開始日時")

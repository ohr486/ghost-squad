"""プロンプトモデル."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.database.base import BaseModel
from models.enums.prompt_category import PromptCategory


class PromptModel(BaseModel):
    """プロンプトエンティティ.

    システム全体で使用されるAIプロンプトを一元管理する。
    """

    __tablename__ = "prompts"

    # 一意識別子キー（例: story_generation_system）
    key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    # 表示名
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 説明
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # カテゴリ
    category: Mapped[PromptCategory] = mapped_column(
        Enum(PromptCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )

    # 現在のプロンプト本文
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # デフォルトプロンプト本文（変更不可）
    default_content: Mapped[str] = mapped_column(Text, nullable=False)

    # プレースホルダー変数リスト（JSON配列）
    variables: Mapped[List[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )

    # デフォルトから変更されているか
    is_modified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # 編集ロック情報
    editing_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    editing_since: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        """文字列表現."""
        return (
            f"<PromptModel(id={self.id}, key='{self.key}', "
            f"category='{self.category.value}')>"
        )

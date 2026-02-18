"""PromptRepository data access layer.

プロンプトのCRUD操作を提供する。
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from models.database.prompt import PromptModel
from models.enums.prompt_category import PromptCategory


class CreatePromptData:
    """プロンプト作成データ."""

    def __init__(
        self,
        key: str,
        name: str,
        category: PromptCategory,
        content: str,
        default_content: str,
        variables: List[str],
        description: Optional[str] = None,
    ):
        """Initialize CreatePromptData.

        Args:
            key: プロンプトキー（一意識別子）
            name: 表示名
            category: カテゴリ
            content: プロンプト本文
            default_content: デフォルトプロンプト本文
            variables: プレースホルダー変数リスト
            description: 説明（オプショナル）
        """
        self.key = key
        self.name = name
        self.category = category
        self.content = content
        self.default_content = default_content
        self.variables = variables
        self.description = description


class UpdatePromptData:
    """プロンプト更新データ."""

    def __init__(
        self,
        content: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Initialize UpdatePromptData.

        Args:
            content: プロンプト本文（オプショナル）
            description: 説明（オプショナル）
        """
        self.content = content
        self.description = description


class PromptRepository:
    """プロンプトリポジトリ.

    プロンプトのCRUD操作を提供する。
    """

    def __init__(self, session: Session):
        """Initialize PromptRepository.

        Args:
            session: SQLAlchemyセッション
        """
        self.session = session

    def create(self, data: CreatePromptData) -> PromptModel:
        """プロンプトを作成する（シード用）.

        Args:
            data: プロンプト作成データ

        Returns:
            PromptModel: 作成されたプロンプトエンティティ
        """
        prompt = PromptModel(
            key=data.key,
            name=data.name,
            description=data.description,
            category=data.category,
            content=data.content,
            default_content=data.default_content,
            variables=data.variables,
            is_modified=False,
        )
        self.session.add(prompt)
        self.session.commit()
        self.session.refresh(prompt)
        return prompt

    def find_by_key(self, key: str) -> Optional[PromptModel]:
        """キーでプロンプトを取得する.

        Args:
            key: プロンプトキー

        Returns:
            PromptModel | None: プロンプトエンティティ、存在しない場合はNone
        """
        return self.session.query(PromptModel).filter(PromptModel.key == key).first()

    def find_all(self, category: Optional[PromptCategory] = None) -> List[PromptModel]:
        """全プロンプトを取得する（カテゴリフィルタリング対応）.

        Args:
            category: カテゴリフィルタ（Noneの場合は全件取得）

        Returns:
            List[PromptModel]: プロンプトエンティティのリスト
        """
        query = self.session.query(PromptModel)

        if category is not None:
            query = query.filter(PromptModel.category == category)

        return query.all()

    def update(self, key: str, data: UpdatePromptData) -> Optional[PromptModel]:
        """プロンプトを更新する（default_contentは更新不可）.

        Args:
            key: プロンプトキー
            data: 更新データ

        Returns:
            PromptModel | None: 更新されたプロンプト、存在しない場合はNone
        """
        prompt = self.find_by_key(key)
        if prompt is None:
            return None

        if data.content is not None:
            prompt.content = data.content
            # is_modifiedを自動計算
            prompt.is_modified = prompt.content != prompt.default_content

        if data.description is not None:
            prompt.description = data.description

        prompt.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(prompt)
        return prompt

    def reset_to_default(self, key: str) -> Optional[PromptModel]:
        """プロンプトをデフォルト値にリセットする.

        Args:
            key: プロンプトキー

        Returns:
            PromptModel | None: リセットされたプロンプト、存在しない場合はNone
        """
        prompt = self.find_by_key(key)
        if prompt is None:
            return None

        prompt.content = prompt.default_content
        prompt.is_modified = False
        prompt.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(prompt)
        return prompt

    def update_edit_lock(
        self,
        key: str,
        editing_by: Optional[str],
        editing_since: Optional[datetime],
    ) -> Optional[PromptModel]:
        """編集ロック情報を更新する.

        Args:
            key: プロンプトキー
            editing_by: 編集者ID（Noneでロック解放）
            editing_since: 編集開始日時（Noneでロック解放）

        Returns:
            PromptModel | None: 更新されたプロンプト、存在しない場合はNone
        """
        prompt = self.find_by_key(key)
        if prompt is None:
            return None

        prompt.editing_by = editing_by
        prompt.editing_since = editing_since

        self.session.commit()
        self.session.refresh(prompt)
        return prompt

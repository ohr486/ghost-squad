"""ストーリーバリデーションサービス.

タスク 3.2: StoryValidatorを実装する
- 作成リクエストの検証（validate_create_request）を実装する
- 更新リクエストの検証（validate_update_request）を実装する
- AI生成ストーリーの構造検証（validate_generated_story）を実装する
- 問い合わせID存在確認（validate_inquiry_exists）を実装する
- エラーコード体系（GS-2xx）に従った日本語エラーメッセージを実装する
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.database.inquiry import InquiryModel
from models.enums.priority import Priority
from models.schemas.story import CreateStoryRequest, UpdateStoryRequest


@dataclass
class ValidationError:
    """バリデーションエラー情報.

    Attributes:
        field: エラーが発生したフィールド名
        message: エラーメッセージ（日本語）
        code: エラーコード（GS-xxx形式）
    """

    field: str
    message: str
    code: str


@dataclass
class ValidationResult:
    """バリデーション結果.

    Attributes:
        valid: バリデーション成功フラグ
        errors: バリデーションエラーのリスト
    """

    valid: bool
    errors: List[ValidationError]


@dataclass
class GeneratedStoryData:
    """AI生成ストーリーデータ.

    Attributes:
        title: ストーリータイトル
        description: ストーリー説明
        priority: 優先度
        estimated_effort: 推定工数（オプショナル）
    """

    title: str
    description: str
    priority: Priority
    estimated_effort: Optional[float] = None


class StoryValidator:
    """ストーリーバリデーター.

    ストーリーデータのバリデーションを実施し、
    日本語のエラーメッセージとエラーコードを提供する。
    """

    # バリデーションルール定数
    TITLE_MAX_LENGTH = 500
    DESCRIPTION_MAX_LENGTH = 50000

    # エラーメッセージ定義
    ERROR_MESSAGES = {
        "GS-201": "タイトルが500文字を超えています",
        "GS-202": "必須フィールドが欠けています",
        "GS-203": "優先度が不正です",
        "GS-204": "問い合わせが見つかりません",
    }

    def validate_create_request(self, request: CreateStoryRequest) -> ValidationResult:
        """作成リクエストの検証.

        Args:
            request: 作成リクエスト

        Returns:
            ValidationResult: バリデーション結果
        """
        # Pydanticバリデーションが既に実行されているため、
        # 追加のビジネスルール検証がなければ常に有効
        return ValidationResult(valid=True, errors=[])

    def validate_update_request(self, request: UpdateStoryRequest) -> ValidationResult:
        """更新リクエストの検証.

        Args:
            request: 更新リクエスト

        Returns:
            ValidationResult: バリデーション結果
        """
        # Pydanticバリデーションが既に実行されているため、
        # 追加のビジネスルール検証がなければ常に有効
        return ValidationResult(valid=True, errors=[])

    def validate_generated_story(self, data: Dict[str, Any]) -> GeneratedStoryData:
        """AI生成ストーリーの構造検証.

        Args:
            data: AI生成データ（辞書形式）

        Returns:
            GeneratedStoryData: 検証済みストーリーデータ

        Raises:
            ValueError: 必須フィールド欠如、不正な値の場合
        """
        # 必須フィールドチェック
        if "title" not in data:
            raise ValueError("必須フィールドが欠けています: title")

        if "description" not in data:
            raise ValueError("必須フィールドが欠けています: description")

        if "priority" not in data:
            raise ValueError("必須フィールドが欠けています: priority")

        # 各フィールドの検証
        title = data["title"]
        if not isinstance(title, str):
            raise ValueError("タイトルは文字列である必要があります")

        if not title.strip():
            raise ValueError("タイトルが空です")

        if len(title) > self.TITLE_MAX_LENGTH:
            raise ValueError(f"タイトルが{self.TITLE_MAX_LENGTH}文字を超えています")

        description = data["description"]
        if not isinstance(description, str):
            raise ValueError("説明は文字列である必要があります")

        if not description.strip():
            raise ValueError("説明が空です")

        # 優先度の変換
        priority_str = data["priority"]
        if not isinstance(priority_str, str):
            raise ValueError("優先度は文字列である必要があります")

        priority_map = {
            "low": Priority.LOW,
            "medium": Priority.MEDIUM,
            "high": Priority.HIGH,
            "urgent": Priority.URGENT,
        }

        priority = priority_map.get(priority_str.lower())
        if priority is None:
            raise ValueError(f"不正な優先度: {priority_str}")

        # オプショナルフィールド
        estimated_effort = data.get("estimated_effort")

        return GeneratedStoryData(
            title=title,
            description=description,
            priority=priority,
            estimated_effort=estimated_effort,
        )

    def validate_inquiry_exists(self, session: Session, inquiry_id: int) -> bool:
        """問い合わせID存在確認.

        Args:
            session: データベースセッション
            inquiry_id: 問い合わせID

        Returns:
            bool: 問い合わせが存在する場合True

        Raises:
            ValueError: 問い合わせが存在しない場合（GS-204）
        """
        inquiry = session.query(InquiryModel).filter_by(id=inquiry_id).first()

        if inquiry is None:
            raise ValueError(
                f"GS-204: {self.ERROR_MESSAGES['GS-204']}: inquiry_id={inquiry_id}"
            )

        return True

"""問い合わせバリデーションサービス."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List


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


class InquiryValidator:
    """問い合わせバリデーター.

    問い合わせデータのバリデーションを実施し、
    日本語のエラーメッセージとエラーコードを提供する。
    """

    # バリデーションルール定数
    CONTENT_MAX_LENGTH = 10000
    USER_ID_MAX_LENGTH = 50
    SOURCE_SYSTEM_MAX_LENGTH = 50

    # エラーメッセージ定義
    ERROR_MESSAGES = {
        "GS-001": "問い合わせ内容が空です",
        "GS-002": "問い合わせ内容が長すぎます（最大10,000文字）",
        "GS-003": "ユーザーIDが不正です（英数字とアンダースコア、最大50文字）",
        "GS-004": "送信元システムが不正です（最大50文字）",
        "GS-005": "指定された問い合わせが見つかりません",
        "GS-006": "却下理由が長すぎます（最大1,000文字）",
        "GS-007": "不正なステータス遷移です",
        "GS-008": "この問い合わせは既に承認済みです",
        "GS-009": "この問い合わせは既に却下済みです",
        "GS-010": "データベース操作に失敗しました",
        "GS-011": "ページネーションパラメータが不正です",
        "GS-012": "問い合わせ内容は文字列である必要があります",
        "GS-013": "ユーザーIDは文字列である必要があります",
        "GS-014": "送信元システムは文字列である必要があります",
    }

    def validate_content(self, content: str) -> ValidationResult:
        """問い合わせ内容のバリデーション.

        Args:
            content: 問い合わせ内容

        Returns:
            ValidationResult: バリデーション結果
        """
        errors: List[ValidationError] = []

        # 型チェック
        if not isinstance(content, str):
            errors.append(
                ValidationError(
                    field="content",
                    message=self.ERROR_MESSAGES["GS-012"],
                    code="GS-012",
                )
            )
            return ValidationResult(valid=False, errors=errors)

        # 空文字チェック
        if not content or not content.strip():
            errors.append(
                ValidationError(
                    field="content",
                    message=self.ERROR_MESSAGES["GS-001"],
                    code="GS-001",
                )
            )

        # 最大文字数チェック
        if len(content) > self.CONTENT_MAX_LENGTH:
            errors.append(
                ValidationError(
                    field="content",
                    message=self.ERROR_MESSAGES["GS-002"],
                    code="GS-002",
                )
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def _validate_user_id(self, user_id: str) -> ValidationResult:
        """ユーザーIDのバリデーション.

        Args:
            user_id: ユーザーID

        Returns:
            ValidationResult: バリデーション結果
        """
        errors: List[ValidationError] = []

        # 型チェック
        if not isinstance(user_id, str):
            errors.append(
                ValidationError(
                    field="user_id",
                    message=self.ERROR_MESSAGES["GS-013"],
                    code="GS-013",
                )
            )
            return ValidationResult(valid=False, errors=errors)

        # 空文字チェック、文字種チェック、最大文字数チェック
        if (
            not user_id
            or not re.match(r"^[a-zA-Z0-9_]+$", user_id)
            or len(user_id) > self.USER_ID_MAX_LENGTH
        ):
            errors.append(
                ValidationError(
                    field="user_id",
                    message=self.ERROR_MESSAGES["GS-003"],
                    code="GS-003",
                )
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def _validate_source_system(self, source_system: Any) -> ValidationResult:
        """送信元システムのバリデーション.

        Args:
            source_system: 送信元システム（任意の型を受け取るが、文字列であることを検証）

        Returns:
            ValidationResult: バリデーション結果
        """
        errors: List[ValidationError] = []

        # 型チェック - 文字列以外の場合はエラー
        if not isinstance(source_system, str):
            errors.append(
                ValidationError(
                    field="source_system",
                    message=self.ERROR_MESSAGES["GS-004"],
                    code="GS-004",
                )
            )
            return ValidationResult(valid=False, errors=errors)

        # 空文字チェック
        if not source_system:
            errors.append(
                ValidationError(
                    field="source_system",
                    message=self.ERROR_MESSAGES["GS-004"],
                    code="GS-004",
                )
            )

        # 最大文字数チェック
        if len(source_system) > self.SOURCE_SYSTEM_MAX_LENGTH:
            errors.append(
                ValidationError(
                    field="source_system",
                    message=self.ERROR_MESSAGES["GS-004"],
                    code="GS-004",
                )
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_create(self, data: Dict[str, Any]) -> ValidationResult:
        """問い合わせ作成データのバリデーション.

        Args:
            data: 問い合わせ作成データ（user_id, content, source_system）

        Returns:
            ValidationResult: バリデーション結果
        """
        all_errors: List[ValidationError] = []

        # 必須フィールドチェック
        if "user_id" not in data:
            all_errors.append(
                ValidationError(
                    field="user_id",
                    message=self.ERROR_MESSAGES["GS-003"],
                    code="GS-003",
                )
            )
        else:
            user_id_result = self._validate_user_id(data["user_id"])
            all_errors.extend(user_id_result.errors)

        if "content" not in data:
            all_errors.append(
                ValidationError(
                    field="content",
                    message=self.ERROR_MESSAGES["GS-001"],
                    code="GS-001",
                )
            )
        else:
            content_result = self.validate_content(data["content"])
            all_errors.extend(content_result.errors)

        if "source_system" not in data:
            all_errors.append(
                ValidationError(
                    field="source_system",
                    message=self.ERROR_MESSAGES["GS-004"],
                    code="GS-004",
                )
            )
        else:
            source_result = self._validate_source_system(data["source_system"])
            all_errors.extend(source_result.errors)

        return ValidationResult(valid=len(all_errors) == 0, errors=all_errors)

    def validate_update(self, data: Dict[str, Any]) -> ValidationResult:
        """問い合わせ更新データのバリデーション.

        部分更新をサポートするため、提供されたフィールドのみをバリデーションする。

        Args:
            data: 問い合わせ更新データ（content, source_system）

        Returns:
            ValidationResult: バリデーション結果
        """
        all_errors: List[ValidationError] = []

        # contentが提供されている場合のみバリデーション
        if "content" in data:
            content_result = self.validate_content(data["content"])
            all_errors.extend(content_result.errors)

        # source_systemが提供されている場合のみバリデーション
        if "source_system" in data:
            source_result = self._validate_source_system(data["source_system"])
            all_errors.extend(source_result.errors)

        return ValidationResult(valid=len(all_errors) == 0, errors=all_errors)

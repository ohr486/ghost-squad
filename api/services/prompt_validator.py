"""プロンプトバリデーションサービス.

タスク 3.1: プロンプト入力のバリデーション機能を実装する
- プロンプト本文の空チェック（GS-401エラー）
- プレースホルダー構文の検証（GS-402エラー）
- 無効なカテゴリ指定に対する検証（GS-403エラー）
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from models.enums.prompt_category import PromptCategory


@dataclass
class ValidationError:
    """バリデーションエラー情報.

    Attributes:
        field: エラーが発生したフィールド名
        message: エラーメッセージ（日本語）
        code: エラーコード（GS-4xx形式）
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


# プレースホルダーのパターン: {variable_name} 形式
# 有効な変数名は英数字とアンダースコアのみ
_PLACEHOLDER_PATTERN = re.compile(r"\{([^}]*)\}")
_VALID_VARIABLE_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
# ネストした波括弧の検出パターン
_NESTED_BRACES_PATTERN = re.compile(r"\{\{")
# 閉じられていない波括弧の検出パターン
_UNCLOSED_BRACE_PATTERN = re.compile(r"\{[^}]*$", re.MULTILINE)


class PromptValidator:
    """プロンプトバリデーター.

    プロンプトデータのバリデーションを実施し、
    日本語のエラーメッセージとエラーコードを提供する。
    """

    # エラーメッセージ定義
    ERROR_MESSAGES = {
        "GS-401": "プロンプト本文が空です",
        "GS-402": "無効なプレースホルダー構文です",
        "GS-403": "無効なカテゴリです",
    }

    # 有効なカテゴリ値のセット
    _VALID_CATEGORIES = {c.value for c in PromptCategory}

    def validate_content(self, content: Optional[str]) -> ValidationResult:
        """プロンプト本文を検証する.

        Args:
            content: プロンプト本文

        Returns:
            ValidationResult: バリデーション結果
        """
        errors: List[ValidationError] = []

        if content is None or not isinstance(content, str) or not content.strip():
            errors.append(
                ValidationError(
                    field="content",
                    message=self.ERROR_MESSAGES["GS-401"],
                    code="GS-401",
                )
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_placeholders(
        self, content: str, allowed_variables: List[str]
    ) -> ValidationResult:
        """プレースホルダーの構文と変数名を検証する.

        Args:
            content: プロンプト本文
            allowed_variables: 許可された変数名のリスト

        Returns:
            ValidationResult: バリデーション結果
        """
        errors: List[ValidationError] = []
        allowed_set = set(allowed_variables)

        # ネストした波括弧の検出
        if _NESTED_BRACES_PATTERN.search(content):
            errors.append(
                ValidationError(
                    field="content",
                    message="ネストした波括弧は使用できません",
                    code="GS-402",
                )
            )
            return ValidationResult(valid=False, errors=errors)

        # 閉じられていない波括弧の検出
        if _UNCLOSED_BRACE_PATTERN.search(content):
            errors.append(
                ValidationError(
                    field="content",
                    message="閉じられていない波括弧があります",
                    code="GS-402",
                )
            )
            return ValidationResult(valid=False, errors=errors)

        # プレースホルダーを検出して検証
        matches = _PLACEHOLDER_PATTERN.findall(content)
        for var_name in matches:
            # 空の波括弧
            if not var_name:
                errors.append(
                    ValidationError(
                        field="content",
                        message="空のプレースホルダーは使用できません",
                        code="GS-402",
                    )
                )
                continue

            # 変数名の構文検証
            if not _VALID_VARIABLE_NAME.match(var_name):
                errors.append(
                    ValidationError(
                        field="content",
                        message=f"無効なプレースホルダー変数名です: {var_name}",
                        code="GS-402",
                    )
                )
                continue

            # 許可リストとの照合
            if var_name not in allowed_set:
                errors.append(
                    ValidationError(
                        field="content",
                        message=f"許可されていないプレースホルダー変数です: {var_name}",
                        code="GS-402",
                    )
                )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_category(self, category: Optional[str]) -> ValidationResult:
        """カテゴリを検証する.

        Args:
            category: カテゴリ文字列

        Returns:
            ValidationResult: バリデーション結果
        """
        errors: List[ValidationError] = []

        if (
            category is None
            or not isinstance(category, str)
            or category not in self._VALID_CATEGORIES
        ):
            errors.append(
                ValidationError(
                    field="category",
                    message=self.ERROR_MESSAGES["GS-403"],
                    code="GS-403",
                )
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

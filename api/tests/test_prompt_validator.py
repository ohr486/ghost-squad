"""Test PromptValidator.

タスク 3.1: プロンプト入力のバリデーション機能を実装する
- プロンプト本文の空チェック（GS-401エラー）
- プレースホルダー構文の検証（GS-402エラー）
- 無効なカテゴリ指定に対する検証（GS-403エラー）
- 各バリデーションルールのユニットテスト（正常系・異常系、エラーコード検証）
"""

from services.prompt_validator import (PromptValidator, ValidationError,
                                       ValidationResult)


class TestPromptValidatorValidateContent:
    """validate_contentのテスト（要件2.3, 2.4）."""

    def test_validate_content_valid(self):
        """正常なプロンプト本文のバリデーション成功."""
        validator = PromptValidator()

        result = validator.validate_content("これはプロンプトの本文です。")

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_content_empty_string(self):
        """空文字列の場合、GS-401エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_content("")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "content"
        assert result.errors[0].code == "GS-401"

    def test_validate_content_whitespace_only(self):
        """空白のみの場合、GS-401エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_content("   \t\n  ")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "GS-401"

    def test_validate_content_none(self):
        """Noneの場合、GS-401エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_content(None)  # type: ignore

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "GS-401"

    def test_validate_content_with_placeholders(self):
        """プレースホルダーを含む本文のバリデーション成功."""
        validator = PromptValidator()

        result = validator.validate_content("以下の内容を処理してください: {inquiry_content}")

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_content_multiline(self):
        """複数行のプロンプト本文のバリデーション成功."""
        validator = PromptValidator()
        content = """あなたはAIアシスタントです。
以下の問い合わせからストーリーを生成してください。

問い合わせ内容：
{inquiry_content}

出力形式：
- タイトル
- 説明
"""

        result = validator.validate_content(content)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_content_very_long(self):
        """非常に長いプロンプト本文でもバリデーション成功."""
        validator = PromptValidator()
        content = "あ" * 50000  # 50000文字

        result = validator.validate_content(content)

        assert result.valid is True
        assert len(result.errors) == 0


class TestPromptValidatorValidatePlaceholders:
    """validate_placeholdersのテスト（要件2.3）."""

    def test_validate_placeholders_valid_single(self):
        """単一の有効なプレースホルダーのバリデーション成功."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "問い合わせ: {inquiry_content}",
            ["inquiry_content"],
        )

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_placeholders_valid_multiple(self):
        """複数の有効なプレースホルダーのバリデーション成功."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "問い合わせ: {inquiry_content}\nテンプレート: {template_content}",
            ["inquiry_content", "template_content"],
        )

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_placeholders_no_placeholders(self):
        """プレースホルダーなしの本文でもバリデーション成功."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "プレースホルダーなしのプロンプト",
            ["inquiry_content"],
        )

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_placeholders_unknown_variable(self):
        """許可されていない変数名を使用した場合、GS-402エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "問い合わせ: {unknown_variable}",
            ["inquiry_content", "template_content"],
        )

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "GS-402"
        assert "unknown_variable" in result.errors[0].message

    def test_validate_placeholders_multiple_unknown(self):
        """複数の許可されていない変数を使用した場合、エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "{foo} と {bar}",
            ["inquiry_content"],
        )

        assert result.valid is False
        assert len(result.errors) >= 1
        assert result.errors[0].code == "GS-402"

    def test_validate_placeholders_invalid_syntax_unclosed(self):
        """閉じブラケットがないプレースホルダーの構文エラー."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "問い合わせ: {inquiry_content",
            ["inquiry_content"],
        )

        assert result.valid is False
        assert len(result.errors) >= 1
        assert result.errors[0].code == "GS-402"

    def test_validate_placeholders_invalid_variable_name_with_spaces(self):
        """変数名にスペースが含まれる場合、GS-402エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "{invalid name}",
            ["inquiry_content"],
        )

        assert result.valid is False
        assert result.errors[0].code == "GS-402"

    def test_validate_placeholders_empty_braces(self):
        """空の波括弧の場合、GS-402エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "テスト {}",
            ["inquiry_content"],
        )

        assert result.valid is False
        assert result.errors[0].code == "GS-402"

    def test_validate_placeholders_nested_braces(self):
        """ネストした波括弧の場合、GS-402エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "テスト {{nested}}",
            ["nested"],
        )

        assert result.valid is False
        assert result.errors[0].code == "GS-402"

    def test_validate_placeholders_valid_variable_name_underscore(self):
        """アンダースコアを含む変数名のバリデーション成功."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "{my_variable_name}",
            ["my_variable_name"],
        )

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_placeholders_empty_allowed_list(self):
        """許可変数リストが空の場合、プレースホルダーがあればエラー."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "{inquiry_content}",
            [],
        )

        assert result.valid is False
        assert result.errors[0].code == "GS-402"

    def test_validate_placeholders_allowed_list_empty_no_placeholders(self):
        """許可変数リストが空でプレースホルダーもない場合、成功."""
        validator = PromptValidator()

        result = validator.validate_placeholders(
            "プレースホルダーなし",
            [],
        )

        assert result.valid is True
        assert len(result.errors) == 0


class TestPromptValidatorValidateCategory:
    """validate_categoryのテスト（要件1.4）."""

    def test_validate_category_story_generation(self):
        """story_generationカテゴリのバリデーション成功."""
        validator = PromptValidator()

        result = validator.validate_category("story_generation")

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_category_import_analysis(self):
        """import_analysisカテゴリのバリデーション成功."""
        validator = PromptValidator()

        result = validator.validate_category("import_analysis")

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_category_general(self):
        """generalカテゴリのバリデーション成功."""
        validator = PromptValidator()

        result = validator.validate_category("general")

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_category_invalid(self):
        """無効なカテゴリの場合、GS-403エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_category("invalid_category")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "category"
        assert result.errors[0].code == "GS-403"

    def test_validate_category_empty(self):
        """空のカテゴリの場合、GS-403エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_category("")

        assert result.valid is False
        assert result.errors[0].code == "GS-403"

    def test_validate_category_none(self):
        """Noneの場合、GS-403エラーを返す."""
        validator = PromptValidator()

        result = validator.validate_category(None)  # type: ignore

        assert result.valid is False
        assert result.errors[0].code == "GS-403"

    def test_validate_category_case_sensitive(self):
        """カテゴリは大文字小文字を区別する."""
        validator = PromptValidator()

        result = validator.validate_category("STORY_GENERATION")

        assert result.valid is False
        assert result.errors[0].code == "GS-403"


class TestValidationErrorAndResult:
    """ValidationErrorとValidationResultのテスト."""

    def test_validation_error_structure(self):
        """ValidationErrorが正しい構造を持つ."""
        error = ValidationError(
            field="content",
            message="プロンプト本文が空です",
            code="GS-401",
        )

        assert error.field == "content"
        assert error.message == "プロンプト本文が空です"
        assert error.code == "GS-401"

    def test_validation_result_valid(self):
        """ValidationResultが有効な結果を表現できる."""
        result = ValidationResult(valid=True, errors=[])

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validation_result_invalid(self):
        """ValidationResultが無効な結果を表現できる."""
        error = ValidationError(
            field="content",
            message="プロンプト本文が空です",
            code="GS-401",
        )
        result = ValidationResult(valid=False, errors=[error])

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "GS-401"


class TestPromptValidatorErrorCodes:
    """エラーコード体系のテスト."""

    def test_error_code_gs401_empty_content(self):
        """GS-401: プロンプト本文が空."""
        validator = PromptValidator()
        result = validator.validate_content("")

        assert result.errors[0].code == "GS-401"
        assert "プロンプト本文が空です" in result.errors[0].message

    def test_error_code_gs402_invalid_placeholder(self):
        """GS-402: 無効なプレースホルダー構文."""
        validator = PromptValidator()
        result = validator.validate_placeholders(
            "{unknown_var}",
            ["inquiry_content"],
        )

        assert result.errors[0].code == "GS-402"

    def test_error_code_gs403_invalid_category(self):
        """GS-403: 無効なカテゴリ."""
        validator = PromptValidator()
        result = validator.validate_category("nonexistent")

        assert result.errors[0].code == "GS-403"
        assert "カテゴリ" in result.errors[0].message

    def test_error_messages_are_japanese(self):
        """すべてのエラーメッセージが日本語であることを確認."""
        validator = PromptValidator()

        # GS-401
        r1 = validator.validate_content("")
        assert any(ord(c) > 127 for c in r1.errors[0].message), "GS-401メッセージは日本語であるべき"

        # GS-402
        r2 = validator.validate_placeholders("{bad}", [])
        assert any(ord(c) > 127 for c in r2.errors[0].message), "GS-402メッセージは日本語であるべき"

        # GS-403
        r3 = validator.validate_category("invalid")
        assert any(ord(c) > 127 for c in r3.errors[0].message), "GS-403メッセージは日本語であるべき"

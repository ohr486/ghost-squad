"""問い合わせバリデーター テスト."""

from services.inquiry_validator import (InquiryValidator, ValidationError,
                                        ValidationResult)


class TestInquiryValidatorContent:
    """content フィールドのバリデーションテスト."""

    def test_validate_content_success(self):
        """正常なコンテンツのバリデーション成功."""
        validator = InquiryValidator()
        result = validator.validate_content("これは有効な問い合わせ内容です")

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_content_empty_string(self):
        """空文字列のバリデーション失敗."""
        validator = InquiryValidator()
        result = validator.validate_content("")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "content"
        assert result.errors[0].code == "GS-001"
        assert "空です" in result.errors[0].message

    def test_validate_content_whitespace_only(self):
        """空白のみの文字列のバリデーション失敗."""
        validator = InquiryValidator()
        result = validator.validate_content("   \n\t  ")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "content"
        assert result.errors[0].code == "GS-001"

    def test_validate_content_whitespace_exceeds_max_length(self):
        """10,001文字の空白文字列は単一エラーのみを返す."""
        validator = InquiryValidator()
        # 10,001文字の空白文字列（空白として扱われ、長さチェックはスキップされる）
        result = validator.validate_content(" " * 10001)

        assert result.valid is False
        # 空白のみなので、GS-001エラーのみが返され、GS-002は返されない
        assert len(result.errors) == 1
        assert result.errors[0].field == "content"
        assert result.errors[0].code == "GS-001"

    def test_validate_content_max_length(self):
        """最大文字数（10,000文字）のバリデーション成功."""
        validator = InquiryValidator()
        content = "a" * 10000
        result = validator.validate_content(content)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_content_exceeds_max_length(self):
        """最大文字数超過のバリデーション失敗."""
        validator = InquiryValidator()
        content = "a" * 10001
        result = validator.validate_content(content)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "content"
        assert result.errors[0].code == "GS-002"
        assert "長すぎます" in result.errors[0].message
        assert "10,000" in result.errors[0].message

    def test_validate_content_none_type(self):
        """Noneが渡された場合のバリデーション失敗."""
        validator = InquiryValidator()
        result = validator.validate_content(None)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "content"
        assert result.errors[0].code == "GS-012"
        assert "文字列である必要があります" in result.errors[0].message

    def test_validate_content_int_type(self):
        """整数が渡された場合のバリデーション失敗."""
        validator = InquiryValidator()
        result = validator.validate_content(123)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "content"
        assert result.errors[0].code == "GS-012"

    def test_validate_content_list_type(self):
        """リストが渡された場合のバリデーション失敗."""
        validator = InquiryValidator()
        result = validator.validate_content(["test", "content"])

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "content"
        assert result.errors[0].code == "GS-012"

    def test_validate_content_dict_type(self):
        """辞書が渡された場合のバリデーション失敗."""
        validator = InquiryValidator()
        result = validator.validate_content({"key": "value"})

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "content"
        assert result.errors[0].code == "GS-012"


class TestInquiryValidatorUserId:
    """user_id フィールドのバリデーションテスト."""

    def test_validate_user_id_success(self):
        """正常なユーザーIDのバリデーション成功."""
        validator = InquiryValidator()

        # 英数字
        assert validator._validate_user_id("user123").valid is True
        # アンダースコア含む
        assert validator._validate_user_id("user_123").valid is True
        # 最大長50文字
        assert validator._validate_user_id("a" * 50).valid is True

    def test_validate_user_id_empty(self):
        """空のユーザーIDのバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_user_id("")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "user_id"
        assert result.errors[0].code == "GS-003"

    def test_validate_user_id_whitespace_only(self):
        """空白のみのユーザーIDのバリデーション失敗."""
        validator = InquiryValidator()

        # スペースのみ
        result = validator._validate_user_id("   ")
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "user_id"
        assert result.errors[0].code == "GS-003"

        # タブとスペースと改行
        result = validator._validate_user_id("  \t\n  ")
        assert result.valid is False
        assert result.errors[0].code == "GS-003"

    def test_validate_user_id_invalid_characters(self):
        """不正な文字を含むユーザーIDのバリデーション失敗."""
        validator = InquiryValidator()

        # ハイフン
        result = validator._validate_user_id("user-123")
        assert result.valid is False
        assert result.errors[0].code == "GS-003"

        # スペース
        result = validator._validate_user_id("user 123")
        assert result.valid is False

        # 特殊文字
        result = validator._validate_user_id("user@123")
        assert result.valid is False

    def test_validate_user_id_exceeds_max_length(self):
        """最大文字数超過のユーザーIDのバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_user_id("a" * 51)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "user_id"
        assert result.errors[0].code == "GS-003"
        assert "50" in result.errors[0].message

    def test_validate_user_id_none_type(self):
        """Noneが渡された場合のバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_user_id(None)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "user_id"
        assert result.errors[0].code == "GS-013"
        assert "文字列である必要があります" in result.errors[0].message

    def test_validate_user_id_int_type(self):
        """整数が渡された場合のバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_user_id(123)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "user_id"
        assert result.errors[0].code == "GS-013"


class TestInquiryValidatorSourceSystem:
    """source_system フィールドのバリデーションテスト."""

    def test_validate_source_system_success(self):
        """正常な送信元システムのバリデーション成功."""
        validator = InquiryValidator()

        assert validator._validate_source_system("manual").valid is True
        assert validator._validate_source_system("email").valid is True
        assert validator._validate_source_system("chat").valid is True
        assert validator._validate_source_system("a" * 50).valid is True

    def test_validate_source_system_empty(self):
        """空の送信元システムのバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_source_system("")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "source_system"
        assert result.errors[0].code == "GS-004"

    def test_validate_source_system_whitespace_only(self):
        """空白のみの送信元システムのバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_source_system("   ")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "source_system"
        assert result.errors[0].code == "GS-004"

    def test_validate_source_system_exceeds_max_length(self):
        """最大文字数超過の送信元システムのバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_source_system("a" * 51)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "source_system"
        assert result.errors[0].code == "GS-004"
        assert "50" in result.errors[0].message

    def test_validate_source_system_none_type(self):
        """None型の送信元システムのバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_source_system(None)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "source_system"
        assert result.errors[0].code == "GS-004"

    def test_validate_source_system_int_type(self):
        """整数型の送信元システムのバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_source_system(123)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "source_system"
        assert result.errors[0].code == "GS-004"

    def test_validate_source_system_list_type(self):
        """リスト型の送信元システムのバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_source_system(["manual", "email"])

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "source_system"
        assert result.errors[0].code == "GS-004"

    def test_validate_source_system_dict_type(self):
        """辞書型の送信元システムのバリデーション失敗."""
        validator = InquiryValidator()
        result = validator._validate_source_system({"system": "manual"})

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "source_system"
        assert result.errors[0].code == "GS-004"


class TestInquiryValidatorCreate:
    """validateCreateメソッドのテスト."""

    def test_validate_create_success(self):
        """正常なデータのバリデーション成功."""
        validator = InquiryValidator()
        data = {
            "user_id": "test_user",
            "content": "ログイン機能が欲しい",
            "source_system": "manual",
        }
        result = validator.validate_create(data)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_create_multiple_errors(self):
        """複数のバリデーションエラーを検出."""
        validator = InquiryValidator()
        data = {
            "user_id": "",
            "content": "",
            "source_system": "",
        }
        result = validator.validate_create(data)

        assert result.valid is False
        assert len(result.errors) == 3
        # エラーコードの確認
        error_codes = [e.code for e in result.errors]
        assert "GS-003" in error_codes  # user_id
        assert "GS-001" in error_codes  # content
        assert "GS-004" in error_codes  # source_system

    def test_validate_create_missing_fields(self):
        """必須フィールド欠如のバリデーション失敗."""
        validator = InquiryValidator()
        data = {
            "user_id": "test_user",
            # content missing
            "source_system": "manual",
        }
        result = validator.validate_create(data)

        assert result.valid is False
        assert any(e.field == "content" for e in result.errors)

    def test_validate_create_non_string_types(self):
        """非文字列型のフィールドのバリデーション失敗."""
        validator = InquiryValidator()

        # user_idが整数
        data = {
            "user_id": 123,
            "content": "有効なコンテンツ",
            "source_system": "manual",
        }
        result = validator.validate_create(data)
        assert result.valid is False
        assert any(e.field == "user_id" and e.code == "GS-013" for e in result.errors)

        # contentがNone
        data = {
            "user_id": "test_user",
            "content": None,
            "source_system": "manual",
        }
        result = validator.validate_create(data)
        assert result.valid is False
        assert any(e.field == "content" and e.code == "GS-012" for e in result.errors)

        # source_systemがリスト
        data = {
            "user_id": "test_user",
            "content": "有効なコンテンツ",
            "source_system": ["manual"],
        }
        result = validator.validate_create(data)
        assert result.valid is False
        assert any(
            e.field == "source_system" and e.code == "GS-004" for e in result.errors
        )


class TestInquiryValidatorUpdate:
    """validateUpdateメソッドのテスト."""

    def test_validate_update_success(self):
        """正常な更新データのバリデーション成功."""
        validator = InquiryValidator()

        # content のみ更新
        result = validator.validate_update({"content": "更新された内容"})
        assert result.valid is True

        # source_system のみ更新
        result = validator.validate_update({"source_system": "email"})
        assert result.valid is True

        # 両方更新
        result = validator.validate_update(
            {"content": "更新された内容", "source_system": "chat"}
        )
        assert result.valid is True

    def test_validate_update_empty_dict(self):
        """空の更新データのバリデーション成功（部分更新）."""
        validator = InquiryValidator()
        result = validator.validate_update({})

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_update_invalid_content(self):
        """不正なcontentの更新のバリデーション失敗."""
        validator = InquiryValidator()
        result = validator.validate_update({"content": ""})

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "GS-001"

    def test_validate_update_invalid_source_system(self):
        """不正なsource_systemの更新のバリデーション失敗."""
        validator = InquiryValidator()
        result = validator.validate_update({"source_system": "a" * 51})

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "GS-004"


class TestValidationResult:
    """ValidationResultデータクラスのテスト."""

    def test_validation_result_creation(self):
        """ValidationResultの生成."""
        error = ValidationError(field="test_field", message="テストエラー", code="GS-999")
        result = ValidationResult(valid=False, errors=[error])

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "test_field"
        assert result.errors[0].message == "テストエラー"
        assert result.errors[0].code == "GS-999"


class TestValidationError:
    """ValidationErrorデータクラスのテスト."""

    def test_validation_error_creation(self):
        """ValidationErrorの生成."""
        error = ValidationError(field="content", message="問い合わせ内容が空です", code="GS-001")

        assert error.field == "content"
        assert error.message == "問い合わせ内容が空です"
        assert error.code == "GS-001"

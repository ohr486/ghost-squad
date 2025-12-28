"""Pydanticスキーマのテスト."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models.enums.inquiry_status import InquiryStatus
from models.schemas.inquiry import (CreateInquiryRequest, ErrorResponse,
                                    InquiryResponse, UpdateInquiryRequest,
                                    ValidationErrorDetail)


class TestCreateInquiryRequest:
    """CreateInquiryRequestスキーマのテスト."""

    def test_valid_create_request(self) -> None:
        """正常なリクエストデータの検証."""
        data = {
            "user_id": "test_user",
            "content": "ログイン機能が欲しい",
            "source_system": "manual",
        }
        request = CreateInquiryRequest(**data)

        assert request.user_id == "test_user"
        assert request.content == "ログイン機能が欲しい"
        assert request.source_system == "manual"

    def test_content_required(self) -> None:
        """content必須チェック."""
        data = {
            "user_id": "test_user",
            "source_system": "manual",
        }
        with pytest.raises(ValidationError) as exc_info:
            CreateInquiryRequest(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("content",)
        assert errors[0]["type"] == "missing"

    def test_content_empty_string(self) -> None:
        """空文字のcontentは拒否される."""
        data = {
            "user_id": "test_user",
            "content": "",
            "source_system": "manual",
        }
        with pytest.raises(ValidationError) as exc_info:
            CreateInquiryRequest(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("content",)
        assert errors[0]["type"] == "string_too_short"

    def test_content_whitespace_only(self) -> None:
        """空白のみのcontentは拒否される."""
        data = {
            "user_id": "test_user",
            "content": "   ",
            "source_system": "manual",
        }
        with pytest.raises(ValidationError) as exc_info:
            CreateInquiryRequest(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("content",)
        assert str(errors[0]["type"]).startswith("value_error")

    def test_content_max_length(self) -> None:
        """content最大文字数チェック."""
        data = {
            "user_id": "test_user",
            "content": "a" * 10001,  # 最大10,000文字を超える
            "source_system": "manual",
        }
        with pytest.raises(ValidationError) as exc_info:
            CreateInquiryRequest(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("content",)
        assert errors[0]["type"] == "string_too_long"

    def test_user_id_required(self) -> None:
        """user_id必須チェック."""
        data = {
            "content": "ログイン機能が欲しい",
            "source_system": "manual",
        }
        with pytest.raises(ValidationError) as exc_info:
            CreateInquiryRequest(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("user_id",)

    def test_user_id_pattern_alphanumeric_underscore(self) -> None:
        """user_idは英数字とアンダースコアのみ許可."""
        # 正常ケース
        valid_data = {
            "user_id": "test_user_123",
            "content": "テスト",
            "source_system": "manual",
        }
        request = CreateInquiryRequest(**valid_data)
        assert request.user_id == "test_user_123"

        # 異常ケース - ハイフンを含む
        invalid_data = {
            "user_id": "test-user",
            "content": "テスト",
            "source_system": "manual",
        }
        with pytest.raises(ValidationError) as exc_info:
            CreateInquiryRequest(**invalid_data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("user_id",)

    def test_user_id_max_length(self) -> None:
        """user_id最大50文字チェック."""
        data = {
            "user_id": "a" * 51,
            "content": "テスト",
            "source_system": "manual",
        }
        with pytest.raises(ValidationError) as exc_info:
            CreateInquiryRequest(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("user_id",)

    def test_source_system_required(self) -> None:
        """source_system必須チェック."""
        data = {
            "user_id": "test_user",
            "content": "テスト",
        }
        with pytest.raises(ValidationError) as exc_info:
            CreateInquiryRequest(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("source_system",)

    def test_source_system_max_length(self) -> None:
        """source_system最大50文字チェック."""
        data = {
            "user_id": "test_user",
            "content": "テスト",
            "source_system": "a" * 51,
        }
        with pytest.raises(ValidationError) as exc_info:
            CreateInquiryRequest(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("source_system",)


class TestUpdateInquiryRequest:
    """UpdateInquiryRequestスキーマのテスト."""

    def test_update_content_only(self) -> None:
        """contentのみ更新."""
        data = {"content": "更新されたコンテンツ"}
        request = UpdateInquiryRequest(**data)

        assert request.content == "更新されたコンテンツ"
        assert request.source_system is None

    def test_update_source_system_only(self) -> None:
        """source_systemのみ更新."""
        data = {"source_system": "email"}
        request = UpdateInquiryRequest(**data)

        assert request.content is None
        assert request.source_system == "email"

    def test_update_both_fields(self) -> None:
        """両方のフィールドを更新."""
        data = {"content": "更新されたコンテンツ", "source_system": "email"}
        request = UpdateInquiryRequest(**data)

        assert request.content == "更新されたコンテンツ"
        assert request.source_system == "email"

    def test_update_empty_request(self) -> None:
        """空のリクエスト（何も更新しない）."""
        data = {}
        request = UpdateInquiryRequest(**data)

        assert request.content is None
        assert request.source_system is None

    def test_update_content_validation(self) -> None:
        """更新時のcontentバリデーション."""
        # 空文字は拒否
        data = {"content": ""}
        with pytest.raises(ValidationError):
            UpdateInquiryRequest(**data)

        # 空白のみは拒否
        data = {"content": "   "}
        with pytest.raises(ValidationError):
            UpdateInquiryRequest(**data)

        # 最大文字数超過は拒否
        data = {"content": "a" * 10001}
        with pytest.raises(ValidationError):
            UpdateInquiryRequest(**data)


class TestInquiryResponse:
    """InquiryResponseスキーマのテスト."""

    def test_valid_response(self) -> None:
        """正常なレスポンスデータの検証."""
        now = datetime.now(UTC)
        data = {
            "id": 1,
            "user_id": "test_user",
            "content": "テスト問い合わせ",
            "source_system": "manual",
            "timestamp": now,
            "status": InquiryStatus.RECEIVED,
            "created_at": now,
            "updated_at": now,
        }
        response = InquiryResponse(**data)

        assert response.id == 1
        assert response.user_id == "test_user"
        assert response.content == "テスト問い合わせ"
        assert response.source_system == "manual"
        assert response.status == InquiryStatus.RECEIVED
        assert isinstance(response.timestamp, datetime)
        assert isinstance(response.created_at, datetime)
        assert isinstance(response.updated_at, datetime)

    def test_timestamp_serialization(self) -> None:
        """タイムスタンプのISO 8601シリアライゼーション."""
        now = datetime.now(UTC)
        data = {
            "id": 1,
            "user_id": "test_user",
            "content": "テスト",
            "source_system": "manual",
            "timestamp": now,
            "status": InquiryStatus.RECEIVED,
            "created_at": now,
            "updated_at": now,
        }
        response = InquiryResponse(**data)

        # model_dump でシリアライズ
        serialized = response.model_dump(mode="json")

        # ISO 8601形式の文字列になっていることを確認
        assert isinstance(serialized["timestamp"], str)
        assert isinstance(serialized["created_at"], str)
        assert isinstance(serialized["updated_at"], str)

        # ISO 8601フォーマットをパース可能
        datetime.fromisoformat(serialized["timestamp"].replace("Z", "+00:00"))
        datetime.fromisoformat(serialized["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(serialized["updated_at"].replace("Z", "+00:00"))


class TestErrorResponse:
    """ErrorResponseスキーマのテスト."""

    def test_single_error(self) -> None:
        """単一エラーのレスポンス."""
        now = datetime.now(UTC)
        error = ValidationErrorDetail(
            code="GS-001", message="問い合わせ内容が空です", field="content"
        )
        response = ErrorResponse(errors=[error], timestamp=now)

        assert len(response.errors) == 1
        assert response.errors[0].code == "GS-001"
        assert response.errors[0].message == "問い合わせ内容が空です"
        assert response.errors[0].field == "content"
        assert isinstance(response.timestamp, datetime)

    def test_multiple_errors(self) -> None:
        """複数エラーのレスポンス."""
        now = datetime.now(UTC)
        errors = [
            ValidationErrorDetail(
                code="GS-001", message="問い合わせ内容が空です", field="content"
            ),
            ValidationErrorDetail(
                code="GS-003", message="ユーザーIDが不正です", field="user_id"
            ),
        ]
        response = ErrorResponse(errors=errors, timestamp=now)

        assert len(response.errors) == 2
        assert response.errors[0].code == "GS-001"
        assert response.errors[1].code == "GS-003"

    def test_error_without_field(self) -> None:
        """フィールド指定なしのエラー（システムエラーなど）."""
        now = datetime.now(UTC)
        error = ValidationErrorDetail(code="GS-010", message="データベース操作に失敗しました")
        response = ErrorResponse(errors=[error], timestamp=now)

        assert len(response.errors) == 1
        assert response.errors[0].field is None

"""共通Result型モジュール.

Rust風のResult型を簡易実装。
プラグインとAIプロバイダーの両方で使用される共通エラーハンドリング機構。
"""
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

# ジェネリック型パラメータ
T = TypeVar("T")
E = TypeVar("E", bound="BaseError")


@dataclass
class BaseError:
    """エラーの基底クラス.

    Attributes:
        code: エラーコード (例: "GS-301")
        message: エラーメッセージ
    """

    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class Result(Generic[T]):
    """Result型：成功または失敗を表す.

    Rust風のResult型を簡易実装。
    """

    def __init__(
        self, value: Optional[T] = None, error: Optional[BaseError] = None
    ) -> None:
        self._value = value
        self._error = error

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        """成功結果を作成."""
        return cls(value=value)

    @classmethod
    def err(cls, error: BaseError) -> "Result[T]":
        """失敗結果を作成."""
        return cls(error=error)

    @property
    def is_ok(self) -> bool:
        """成功かどうかを返す."""
        return self._error is None

    @property
    def is_err(self) -> bool:
        """失敗かどうかを返す."""
        return self._error is not None

    def unwrap(self) -> T:
        """成功時の値を取得。成功でない場合は例外を発生。"""
        if self._error is not None:
            raise ValueError(f"Called unwrap on an Err value: {self._error}")
        return self._value  # type: ignore

    def unwrap_err(self) -> BaseError:
        """失敗時のエラーを取得。失敗でない場合は例外を発生。"""
        if self._error is None:
            raise ValueError("Called unwrap_err on an Ok value")
        return self._error

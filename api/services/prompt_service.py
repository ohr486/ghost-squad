"""PromptService - プロンプト管理のビジネスロジック層.

タスク 4.1: プロンプトの取得・更新・リセットロジック
タスク 4.2: プロンプトのテスト実行機能
タスク 4.3: 編集ロック管理機能

Requirements: 1.1, 1.2, 1.3, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.4,
              4.4, 5.1, 5.2, 5.3, 5.4, 5.5
"""
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.database.prompt import PromptModel
from models.enums.prompt_category import PromptCategory
from services.importer.ai_provider_base import (AIAnalysisRequest,
                                                AIProviderType)
from services.prompt_cache import PromptCache, PromptCacheEntry
from services.prompt_repository import PromptRepository, UpdatePromptData
from services.prompt_validator import PromptValidator

logger = logging.getLogger(__name__)

# 編集ロックのタイムアウト（分）
EDIT_LOCK_TIMEOUT_MINUTES = 30

# テスト実行のタイムアウト（秒）
TEST_EXECUTION_TIMEOUT_SECONDS = 30


# =============================================================================
# データクラス定義
# =============================================================================


@dataclass
class PromptData:
    """プロンプトデータ（サービス層の返却型）."""

    key: str
    name: str
    description: Optional[str]
    category: str
    content: str
    default_content: str
    variables: List[str]
    is_modified: bool
    editing_by: Optional[str] = None
    editing_since: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class UpdatePromptRequest:
    """プロンプト更新リクエスト."""

    content: str
    description: Optional[str] = None


@dataclass
class PromptTestRequest:
    """プロンプトテスト実行リクエスト."""

    content: str
    variables: Dict[str, str] = field(default_factory=dict)
    provider: Optional[str] = None


# エイリアス（後方互換性）
TestPromptRequest = PromptTestRequest


@dataclass
class PromptTestResult:
    """プロンプトテスト実行結果."""

    output: str
    provider: str
    model: str
    elapsed_ms: int


# エイリアス（後方互換性）
TestPromptResult = PromptTestResult


@dataclass
class EditLockResult:
    """編集ロック結果."""

    acquired: bool
    locked_by: Optional[str] = None
    locked_since: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# =============================================================================
# 例外クラス定義
# =============================================================================


class PromptNotFoundError(Exception):
    """プロンプトが見つからない場合のエラー (GS-404)."""


class PromptValidationError(Exception):
    """プロンプトバリデーションエラー (GS-401, GS-402, GS-403)."""


class PromptTestTimeoutError(Exception):
    """テスト実行タイムアウトエラー (GS-406)."""


class PromptTestError(Exception):
    """テスト実行エラー (GS-407)."""


class PromptEditLockError(Exception):
    """編集ロックエラー (GS-405)."""


# =============================================================================
# PromptService
# =============================================================================


class PromptService:
    """プロンプト管理サービス.

    プロンプトの取得・更新・リセット・テスト実行・編集ロック管理を提供する。
    """

    def __init__(
        self,
        session: Session,
        cache: Optional[PromptCache] = None,
        ai_provider_registry: Optional[Any] = None,
    ) -> None:
        """Initialize PromptService.

        Args:
            session: SQLAlchemyセッション
            cache: プロンプトキャッシュ（Noneの場合は新規作成）
            ai_provider_registry: AIプロバイダーレジストリ（テスト実行用）
        """
        self._repository = PromptRepository(session)
        self._validator = PromptValidator()
        self._cache = cache if cache is not None else PromptCache()
        self._ai_provider_registry = ai_provider_registry

    # =========================================================================
    # Task 4.1: get_prompt
    # =========================================================================

    def get_prompt(self, key: str) -> PromptData:
        """プロンプトを取得する（キャッシュ → DB → エラー）.

        フォールバック戦略:
        1. キャッシュから取得
        2. DBから取得 → キャッシュに格納
        3. DB障害時はキャッシュのフォールバックを使用
        4. すべて失敗した場合はPromptNotFoundError

        Args:
            key: プロンプトキー

        Returns:
            PromptData: プロンプトデータ

        Raises:
            PromptNotFoundError: プロンプトが見つからない場合
        """
        # 1. キャッシュから取得
        cached = self._cache.get(key)
        if cached is not None:
            logger.debug(f"キャッシュヒット: {key}")
            return PromptData(
                key=cached.key,
                name="",
                description=None,
                category="",
                content=cached.content,
                default_content=cached.default_content,
                variables=cached.variables,
                is_modified=cached.content != cached.default_content,
            )

        # 2. DBから取得
        try:
            prompt = self._repository.find_by_key(key)
            if prompt is not None:
                # キャッシュに格納
                self._cache.set(
                    key,
                    PromptCacheEntry(
                        key=prompt.key,
                        content=prompt.content,
                        default_content=prompt.default_content,
                        variables=prompt.variables,
                    ),
                )
                return self._to_prompt_data(prompt)
        except Exception as e:
            logger.warning(f"DB取得エラー、フォールバック試行: {key}: {e}")
            # 3. DB障害時フォールバック
            fallback = self._cache.get_fallback(key)
            if fallback is not None:
                logger.warning(f"キャッシュフォールバック使用: {key}")
                return PromptData(
                    key=fallback.key,
                    name="",
                    description=None,
                    category="",
                    content=fallback.content,
                    default_content=fallback.default_content,
                    variables=fallback.variables,
                    is_modified=fallback.content != fallback.default_content,
                )
            raise PromptNotFoundError(f"GS-404: プロンプト '{key}' が見つかりません（DB障害）") from e

        # 4. 存在しない場合
        raise PromptNotFoundError(f"GS-404: プロンプト '{key}' が見つかりません")

    # =========================================================================
    # Task 4.1: list_prompts
    # =========================================================================

    def list_prompts(
        self, category: Optional[PromptCategory] = None
    ) -> List[PromptData]:
        """プロンプト一覧を取得する.

        Args:
            category: カテゴリフィルタ（Noneの場合は全件取得）

        Returns:
            List[PromptData]: プロンプトデータのリスト
        """
        prompts = self._repository.find_all(category=category)
        return [self._to_prompt_data(p) for p in prompts]

    # =========================================================================
    # Task 4.1: update_prompt
    # =========================================================================

    def update_prompt(self, key: str, request: UpdatePromptRequest) -> PromptData:
        """プロンプトを更新する.

        バリデーション → DB更新 → キャッシュ無効化

        Args:
            key: プロンプトキー
            request: 更新リクエスト

        Returns:
            PromptData: 更新後のプロンプトデータ

        Raises:
            PromptNotFoundError: プロンプトが見つからない場合
            PromptValidationError: バリデーションエラー
        """
        # プロンプトの存在確認
        existing = self._repository.find_by_key(key)
        if existing is None:
            raise PromptNotFoundError(f"GS-404: プロンプト '{key}' が見つかりません")

        # コンテンツのバリデーション
        content_result = self._validator.validate_content(request.content)
        if not content_result.valid:
            errors = content_result.errors
            raise PromptValidationError(f"{errors[0].code}: {errors[0].message}")

        # プレースホルダーのバリデーション
        placeholder_result = self._validator.validate_placeholders(
            request.content, existing.variables
        )
        if not placeholder_result.valid:
            errors = placeholder_result.errors
            raise PromptValidationError(f"{errors[0].code}: {errors[0].message}")

        # DB更新
        update_data = UpdatePromptData(
            content=request.content,
            description=request.description,
        )
        updated = self._repository.update(key, update_data)
        if updated is None:
            raise PromptNotFoundError(f"GS-404: プロンプト '{key}' が見つかりません")

        # キャッシュ無効化
        self._cache.invalidate(key)

        return self._to_prompt_data(updated)

    # =========================================================================
    # Task 4.1: reset_to_default
    # =========================================================================

    def reset_to_default(self, key: str) -> PromptData:
        """プロンプトをデフォルト値にリセットする.

        Args:
            key: プロンプトキー

        Returns:
            PromptData: リセット後のプロンプトデータ

        Raises:
            PromptNotFoundError: プロンプトが見つからない場合
        """
        reset = self._repository.reset_to_default(key)
        if reset is None:
            raise PromptNotFoundError(f"GS-404: プロンプト '{key}' が見つかりません")

        # キャッシュ無効化
        self._cache.invalidate(key)

        return self._to_prompt_data(reset)

    # =========================================================================
    # Task 4.2: test_prompt
    # =========================================================================

    def test_prompt(self, request: TestPromptRequest) -> TestPromptResult:
        """プロンプトをテスト実行する.

        プレースホルダー置換 → AIプロバイダー呼び出し → 結果返却

        Args:
            request: テスト実行リクエスト

        Returns:
            TestPromptResult: テスト実行結果

        Raises:
            PromptTestError: AIプロバイダーが利用できない場合
            PromptTestTimeoutError: テスト実行タイムアウト
        """
        if self._ai_provider_registry is None:
            raise PromptTestError("GS-407: AIプロバイダーレジストリが設定されていません")

        # プロバイダーの取得
        provider_type = None
        if request.provider:
            # AIProviderType enumに変換を試行
            try:
                provider_type = AIProviderType(request.provider)
            except ValueError:
                pass

        provider = self._ai_provider_registry.get_provider(provider_type)
        if provider is None:
            raise PromptTestError("GS-407: 利用可能なAIプロバイダーがありません")

        # プレースホルダー置換
        substituted = request.content
        for var_name, var_value in request.variables.items():
            substituted = substituted.replace(f"{{{var_name}}}", var_value)

        # AI呼び出し（タイムアウト付き）
        start_time = time.monotonic()
        try:
            ai_request = AIAnalysisRequest(
                content=substituted,
                subject="プロンプトテスト",
                sender="system",
                source_type="prompt_test",
            )

            # ThreadPoolExecutorを使用してタイムアウトを実装
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(provider.analyze, ai_request)
                try:
                    response = future.result(timeout=TEST_EXECUTION_TIMEOUT_SECONDS)
                except FuturesTimeoutError as e:
                    raise PromptTestTimeoutError(
                        f"GS-406: テスト実行がタイムアウトしました（{TEST_EXECUTION_TIMEOUT_SECONDS}秒）"
                    ) from e

            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            return TestPromptResult(
                output=response.content,
                provider=response.provider_type,
                model=response.model,
                elapsed_ms=elapsed_ms,
            )
        except PromptTestTimeoutError:
            raise
        except Exception as e:
            raise PromptTestError(f"GS-407: AI API呼び出しに失敗しました: {e}") from e

    # =========================================================================
    # Task 4.3: edit lock management
    # =========================================================================

    def acquire_edit_lock(self, key: str, user_id: str) -> EditLockResult:
        """編集ロックを取得する.

        Args:
            key: プロンプトキー
            user_id: 編集者ID

        Returns:
            EditLockResult: ロック取得結果

        Raises:
            PromptNotFoundError: プロンプトが見つからない場合
        """
        prompt = self._repository.find_by_key(key)
        if prompt is None:
            raise PromptNotFoundError(f"GS-404: プロンプト '{key}' が見つかりません")

        # 既存ロックのチェック
        if prompt.editing_by is not None:
            # 同じユーザーなら再取得OK
            if prompt.editing_by == user_id:
                now = datetime.now(timezone.utc)
                self._repository.update_edit_lock(key, user_id, now)
                return EditLockResult(
                    acquired=True,
                    locked_by=user_id,
                    locked_since=now,
                )

            # タイムアウト判定（30分）
            if prompt.editing_since is not None:
                now = datetime.now(timezone.utc)
                editing_since = prompt.editing_since
                # timezone-naive datetimeの場合はUTCとして扱う
                if editing_since.tzinfo is None:
                    editing_since = editing_since.replace(tzinfo=timezone.utc)
                lock_age = now - editing_since
                if lock_age < timedelta(minutes=EDIT_LOCK_TIMEOUT_MINUTES):
                    # ロック有効 → 競合
                    return EditLockResult(
                        acquired=False,
                        locked_by=prompt.editing_by,
                        locked_since=prompt.editing_since,
                        error_code="GS-405",
                        error_message=f"ユーザー '{prompt.editing_by}' が編集中です",
                    )
            # タイムアウト or editing_since が None → 古いロック、上書き可

        # ロック取得
        now = datetime.now(timezone.utc)
        self._repository.update_edit_lock(key, user_id, now)
        return EditLockResult(
            acquired=True,
            locked_by=user_id,
            locked_since=now,
        )

    def release_edit_lock(self, key: str, user_id: str) -> None:
        """編集ロックを解放する.

        Note: user_id パラメータは受け取るが、実装では使用しません。
        これは管理者が他のユーザーのロックを解放できるようにするためです。
        将来的にユーザー検証を追加する場合に備えてシグネチャを維持しています。

        Args:
            key: プロンプトキー
            user_id: 編集者ID（現在は未使用、将来の拡張用）

        Raises:
            PromptNotFoundError: プロンプトが見つからない場合
        """
        result = self._repository.update_edit_lock(key, None, None)
        if result is None:
            raise PromptNotFoundError(f"GS-404: プロンプト '{key}' が見つかりません")

    # =========================================================================
    # ヘルパーメソッド
    # =========================================================================

    def _to_prompt_data(self, prompt: PromptModel) -> PromptData:
        """PromptModelをPromptDataに変換する."""
        return PromptData(
            key=prompt.key,
            name=prompt.name,
            description=prompt.description,
            category=prompt.category.value,
            content=prompt.content,
            default_content=prompt.default_content,
            variables=prompt.variables,
            is_modified=prompt.is_modified,
            editing_by=prompt.editing_by,
            editing_since=prompt.editing_since,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
        )

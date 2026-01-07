"""StoryGenerationService - AI駆動のストーリー生成サービス.

タスク 4.1: StoryGenerationServiceを実装する
- 問い合わせからストーリーを生成（generate_story）する機能を実装する
- Inquiryステータス検証（task_working）を実装する
- Inquiryステータス更新（task_working → processing → completed）を実装する
- OpenAI API呼び出し（_call_openai_api）を実装する
- リトライ戦略（3回、指数バックオフ、タイムアウト30秒）を実装する
- AI生成結果の構造検証を実装する
- AI生成失敗時のInquiryステータスロールバック（_rollback_inquiry_status）を実装する
- トランザクション境界管理（Inquiry + Story）を実装する
"""
import json
import os
import time
from typing import Any, Dict

from openai import OpenAI
from sqlalchemy.orm import Session

from models.database.inquiry import InquiryModel
from models.database.story import StoryModel
from models.enums.inquiry_status import InquiryStatus
from services.story_repository import CreateStoryData, StoryRepository
from services.story_validator import StoryValidator


class InquiryNotFoundError(Exception):
    """問い合わせが見つからない場合のエラー."""


class InvalidInquiryStatusError(Exception):
    """問い合わせのステータスが不正な場合のエラー."""


class AIGenerationError(Exception):
    """AI生成失敗時のエラー."""


class StoryGenerationService:
    """ストーリー生成サービス.

    OpenAI APIを使用して問い合わせからストーリーを生成する。
    """

    def __init__(self, session: Session):
        """Initialize StoryGenerationService.

        Args:
            session: SQLAlchemyセッション
        """
        self.session = session
        self.validator = StoryValidator()
        self.repository = StoryRepository(session)

        # Initialize OpenAI client once for better performance
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIGenerationError("OPENAI_API_KEY environment variable not set")

        # Basic format validation to catch obvious configuration errors early
        # OpenAI API keys typically start with "sk-" and have sufficient length.
        if not (api_key.startswith("sk-") and len(api_key) >= 20):
            raise AIGenerationError("OPENAI_API_KEY does not appear to be valid format")

        self.openai_client = OpenAI(api_key=api_key)
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4")

    def generate_story(self, inquiry_id: int) -> StoryModel:
        """問い合わせからストーリーを生成する（要件1.1-1.9）.

        Args:
            inquiry_id: 問い合わせID

        Returns:
            StoryModel: 生成されたストーリー

        Raises:
            InquiryNotFoundError: 問い合わせが存在しない
            InvalidInquiryStatusError: ステータスが task_working でない
            AIGenerationError: AI生成失敗（リトライ後も失敗）
            ValueError: 生成結果の構造検証失敗
        """
        # 入力検証: inquiry_id は正の整数でなければならない
        if not isinstance(inquiry_id, int) or inquiry_id <= 0:
            raise ValueError("inquiry_id must be a positive integer")
        # トランザクション境界を設定し、InquiryとStoryの更新を一括管理する
        with self.session.begin():
            # 1. 問い合わせの取得と検証（要件1.1）
            inquiry = self.session.query(InquiryModel).filter_by(id=inquiry_id).first()

            if inquiry is None:
                raise InquiryNotFoundError(f"Inquiry with id {inquiry_id} not found")

            if inquiry.status != InquiryStatus.TASK_WORKING:
                raise InvalidInquiryStatusError(
                    f"Inquiry status must be task_working, got {inquiry.status.value}"
                )

            # 2. Inquiryステータスを processing に変更（要件1.2）
            original_status = inquiry.status
            inquiry.status = InquiryStatus.PROCESSING

            try:
                # 3. AI APIを呼び出してストーリーを生成（要件1.3）
                # セキュリティ: 入力内容を検証・サニタイズ
                sanitized_content = self._sanitize_inquiry_content(inquiry.content)
                ai_response = self._call_openai_api(sanitized_content)

                # 4. AI生成結果を検証（要件1.8）
                validated_data = self.validator.validate_generated_story(ai_response)

                # 5. ストーリーを作成（要件1.4, 1.5, 1.6）
                story_data = CreateStoryData(
                    inquiry_id=inquiry_id,
                    title=validated_data.title,
                    description=validated_data.description,
                    priority=validated_data.priority,
                    estimated_effort=validated_data.estimated_effort,
                )
                story = self.repository.create(story_data)

                # 6. Inquiryステータスを completed に変更
                inquiry.status = InquiryStatus.COMPLETED

                return story

            except (AIGenerationError, ValueError):
                # AI生成失敗時はトランザクション全体をロールバックすることで
                # Inquiryステータスも元に戻す（要件1.7）
                inquiry.status = original_status
                raise
            except Exception as e:
                # 予期しないエラーの場合はログに記録してロールバック
                inquiry.status = original_status
                # 元の例外を再送出して上位で処理
                raise AIGenerationError(
                    f"予期しないエラーが発生しました: {type(e).__name__}: {str(e)}"
                ) from e

    def _sanitize_inquiry_content(self, content: str) -> str:
        """問い合わせ内容をサニタイズする.

        セキュリティ対策として以下を実施:
        - 最大長を制限（5000文字）してAPIコストとプロンプトインジェクションを防ぐ
        - 制御文字を除去

        Args:
            content: 問い合わせ内容

        Returns:
            str: サニタイズされた内容

        Raises:
            ValueError: 内容が空または長すぎる場合
        """
        if not content or not content.strip():
            raise ValueError("Inquiry content cannot be empty")

        # 制御文字を除去（タブ、改行、復帰は許可）
        sanitized = "".join(
            char for char in content if char.isprintable() or char in ["\n", "\r", "\t"]
        )

        # 最大長を制限（5000文字 = 約1250トークン）
        max_length = 5000
        if len(sanitized) > max_length:
            raise ValueError(
                f"Inquiry content too long: {len(sanitized)} characters "
                f"(maximum: {max_length})"
            )

        return sanitized.strip()

    def _call_openai_api(
        self, inquiry_content: str, retry_count: int = 3
    ) -> Dict[str, Any]:
        """OpenAI APIを呼び出す（要件1.3, 1.7）.

        Args:
            inquiry_content: 問い合わせ内容（サニタイズ済み）
            retry_count: リトライ回数（デフォルト3回）

        Returns:
            Dict[str, Any]: AI生成結果（JSON辞書）

        Raises:
            AIGenerationError: リトライ後も失敗
        """
        # Prompt for story generation
        prompt = f"""以下の問い合わせから、アジャイル開発で使用するユーザーストーリーを生成してください。

問い合わせ内容：
{inquiry_content}

出力形式（JSON）：
{{
    "title": "簡潔なタイトル（500文字以内）",
    "description": "詳細な説明",
    "priority": "low/medium/high/urgent のいずれか",
    "estimated_effort": 推定工数（数値、オプショナル）
}}

JSON形式のみで応答してください（説明文は不要）。"""

        # Retry logic with exponential backoff
        for attempt in range(retry_count):
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "あなたはアジャイル開発の専門家です。" "問い合わせから適切なユーザーストーリーを" "生成してください。"
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                    timeout=30.0,
                )

                # Extract and parse JSON response
                content = response.choices[0].message.content
                if content is None:
                    raise AIGenerationError("OpenAI APIからの応答が空です")
                story_data: Dict[str, Any] = json.loads(content)
                return story_data

            except json.JSONDecodeError as e:
                if attempt < retry_count - 1:
                    self._wait_with_exponential_backoff(attempt)
                    continue
                raise AIGenerationError(f"JSONパースエラー（リトライ後も失敗）: {str(e)}")

            except Exception as e:
                if attempt < retry_count - 1:
                    self._wait_with_exponential_backoff(attempt)
                    continue
                raise AIGenerationError(f"OpenAI APIエラー（リトライ後も失敗）: {str(e)}")

        # この行には到達しないはずですが、型チェックのために追加
        raise AIGenerationError("予期しないエラー: 最大リトライ回数に到達")

    def _wait_with_exponential_backoff(self, attempt: int) -> None:
        """指数バックオフで待機する.

        リトライ間の待機時間を指数的に増加させる。
        - 1回目のリトライ前: 2^0 = 1秒
        - 2回目のリトライ前: 2^1 = 2秒
        - 3回目のリトライ前: 2^2 = 4秒

        Args:
            attempt: 現在の試行回数（0から開始）
        """
        wait_time = 2**attempt
        time.sleep(wait_time)

    def _rollback_inquiry_status(
        self,
        inquiry_id: int,
        original_status: InquiryStatus = InquiryStatus.TASK_WORKING,
    ) -> None:
        """AI生成失敗時にInquiryステータスをロールバックする.

        Args:
            inquiry_id: 問い合わせID
            original_status: ロールバック先のステータス（デフォルト: task_working）

        Raises:
            InquiryNotFoundError: 問い合わせが存在しない
        """
        inquiry = self.session.query(InquiryModel).filter_by(id=inquiry_id).first()

        if inquiry is None:
            raise InquiryNotFoundError(f"Inquiry with id {inquiry_id} not found")

        inquiry.status = original_status
        self.session.commit()

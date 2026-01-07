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

    pass


class InvalidInquiryStatusError(Exception):
    """問い合わせのステータスが不正な場合のエラー."""

    pass


class AIGenerationError(Exception):
    """AI生成失敗時のエラー."""

    pass


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
        self.session.commit()

        try:
            # 3. AI APIを呼び出してストーリーを生成（要件1.3）
            ai_response = self._call_openai_api(inquiry.content)

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
            self.session.commit()

            return story

        except (AIGenerationError, ValueError, Exception):
            # AI生成失敗時、Inquiryステータスをロールバック（要件1.7）
            self._rollback_inquiry_status(inquiry_id, original_status)
            raise

    def _call_openai_api(
        self, inquiry_content: str, retry_count: int = 3
    ) -> Dict[str, Any]:
        """OpenAI APIを呼び出す（要件1.3, 1.7）.

        Args:
            inquiry_content: 問い合わせ内容
            retry_count: リトライ回数（デフォルト3回）

        Returns:
            Dict[str, Any]: AI生成結果（JSON辞書）

        Raises:
            AIGenerationError: リトライ後も失敗
        """
        # OpenAI API key configuration
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIGenerationError(
                "OPENAI_API_KEY environment variable not set"
            )

        client = OpenAI(api_key=api_key)

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
                model_name = os.getenv("OPENAI_MODEL", "gpt-4")
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "あなたはアジャイル開発の専門家です。"
                                "問い合わせから適切なユーザーストーリーを"
                                "生成してください。"
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
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    time.sleep(wait_time)
                    continue
                raise AIGenerationError(
                    f"JSONパースエラー（リトライ後も失敗）: {str(e)}"
                )

            except Exception as e:
                if attempt < retry_count - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    time.sleep(wait_time)
                    continue
                raise AIGenerationError(
                    f"OpenAI APIエラー（リトライ後も失敗）: {str(e)}"
                )

        # この行には到達しないはずですが、型チェックのために追加
        raise AIGenerationError("予期しないエラー: 最大リトライ回数に到達")

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

"""Anthropicプロバイダーモジュール.

Task 5.1: AnthropicProviderConfigと設定検証の実装
- AnthropicProviderConfigデータクラスの定義（AIProviderConfig継承）
- サポートモデル一覧の定義（claude-3-opus、claude-3-sonnet、claude-3-haiku、claude-3-5-sonnet）
- API Key形式検証の実装
- モデル名検証の実装

Task 5.2: AnthropicProviderの解析機能の実装
- Anthropicクライアント初期化の実装（initialize）
- 問い合わせ解析プロンプトの構築（日本語対応、OpenAIProviderと共通化）
- AI解析リクエストの実行（analyze）
- レスポンス解析とAIAnalysisResponseへの変換
- カテゴリ判定、優先度推定、タイトル生成、本文構造化
- 信頼度スコアの算出
- 指数バックオフによるリトライ戦略の実装
- ヘルスチェック機能の実装（health_check）

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from anthropic import Anthropic

from services.importer.ai_provider_base import (AIAnalysisRequest,
                                                AIAnalysisResponse, AIProvider,
                                                AIProviderConfig,
                                                AIProviderType)
from services.importer.plugin_base import ValidationError, ValidationResult

# ロガー設定
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnthropicProviderConfig(AIProviderConfig):
    """Anthropicプロバイダー設定.

    AIProviderConfigを継承し、Anthropic固有の設定を定義。

    Attributes:
        model: 使用するモデル（デフォルト: claude-3-sonnet-20240229）

    契約:
        - api_keyは'sk-ant-'で始まること
        - modelはサポートモデル一覧に含まれること
    """

    model: str = "claude-3-sonnet-20240229"


# 解析用システムプロンプト（日本語対応、OpenAIProviderと共通化）
ANALYSIS_SYSTEM_PROMPT = """あなたは問い合わせ解析の専門家です。
与えられたメールやメッセージを分析し、以下の情報をJSON形式で出力してください。

出力形式（必ずこの形式で出力してください）:
{
    "title": "問い合わせタイトル（簡潔に30文字以内）",
    "content": "構造化された問い合わせ内容（箇条書きで整理）",
    "priority": "優先度（low/medium/high/urgentのいずれか）",
    "category": "カテゴリ（development/testing/documentation/research/maintenance/custom）",
    "confidence_score": 0.0〜1.0の数値（解析の確信度）
}

優先度の判断基準:
- urgent: 緊急、至急、障害、エラー、ダウン等の緊急性を示す語がある
- high: 重要、早急、優先等の語がある、または期限が迫っている
- medium: 通常の問い合わせ、質問、依頼
- low: 参考、確認、将来的な検討事項

カテゴリの判断基準:
- development: 新機能開発、機能追加、実装依頼
- testing: テスト、検証、品質確認
- documentation: ドキュメント作成、マニュアル
- research: 調査、技術検討、PoC
- maintenance: 保守、バグ修正、障害対応
- custom: 上記に該当しない場合

信頼度スコアの基準:
- 0.9以上: 明確な内容で高い確信度
- 0.7〜0.9: 標準的な問い合わせ
- 0.5〜0.7: 曖昧な部分がある
- 0.5未満: 内容が不明確、追加情報が必要

必ず有効なJSONのみを出力してください。説明や追加のテキストは含めないでください。"""


def _build_user_prompt(request: AIAnalysisRequest) -> str:
    """ユーザープロンプトを構築する.

    Args:
        request: 解析リクエスト

    Returns:
        str: ユーザープロンプト文字列
    """
    return f"""以下の問い合わせを解析してください。

【件名】
{request.subject}

【送信者】
{request.sender}

【データソース】
{request.source_type}

【本文】
{request.content}

上記の内容を解析し、JSON形式で出力してください。"""


class AnthropicProvider(AIProvider[AnthropicProviderConfig]):
    """Anthropic AIプロバイダー.

    Anthropic Claude系モデルを使用した問い合わせ解析を提供する。

    Attributes:
        SUPPORTED_MODELS: サポートするモデル一覧

    契約:
        - Preconditions: 有効なAnthropic API Key
        - Postconditions: JSON形式のレスポンスを解析してAIAnalysisResponseを返す
        - Invariants: SUPPORTED_MODELSに含まれるモデルのみ使用可能
    """

    SUPPORTED_MODELS: List[str] = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20241022",
    ]

    def __init__(
        self,
        config: AnthropicProviderConfig,
        system_prompt_getter: Optional[Callable[[], str]] = None,
    ) -> None:
        """AnthropicProviderを初期化.

        Args:
            config: Anthropicプロバイダー設定
            system_prompt_getter: システムプロンプト取得関数（オプション）
        """
        self._config = config
        self._client: Optional[Anthropic] = None
        self._initialized = False
        self._system_prompt_getter = system_prompt_getter

    @property
    def provider_type(self) -> AIProviderType:
        """プロバイダー種別を返す.

        Returns:
            AIProviderType: ANTHROPIC
        """
        return AIProviderType.ANTHROPIC

    @property
    def supported_models(self) -> List[str]:
        """サポートするモデル一覧を返す.

        Returns:
            List[str]: サポートするモデル名のリスト
        """
        return self.SUPPORTED_MODELS

    def validate_config(self, config: AnthropicProviderConfig) -> ValidationResult:
        """設定情報を検証する.

        Args:
            config: 検証する設定

        Returns:
            ValidationResult: バリデーション結果

        検証項目:
            - API Keyが'sk-ant-'で始まること
            - API Keyが空でないこと
            - モデルがサポートモデル一覧に含まれること
        """
        errors: List[ValidationError] = []

        # API Key検証
        if not config.api_key:
            errors.append(
                ValidationError(
                    field="api_key",
                    message="API Keyは必須です",
                    code="GS-308",
                )
            )
        elif not config.api_key.startswith("sk-ant-"):
            errors.append(
                ValidationError(
                    field="api_key",
                    message="API Keyは'sk-ant-'で始まる必要があります",
                    code="GS-308",
                )
            )

        # モデル検証
        if config.model not in self.SUPPORTED_MODELS:
            errors.append(
                ValidationError(
                    field="model",
                    message=f"サポートされていないモデルです: {config.model}。"
                    f"サポートモデル: {', '.join(self.SUPPORTED_MODELS)}",
                    code="GS-309",
                )
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def initialize(self) -> None:
        """プロバイダーを初期化する.

        Anthropicクライアントを作成し、接続を確立する。

        Raises:
            RuntimeError: 初期化に失敗した場合
        """
        try:
            self._client = Anthropic(
                api_key=self._config.api_key,
                timeout=float(self._config.timeout),
            )
            self._initialized = True
            logger.info("Anthropicプロバイダーを初期化しました")
        except Exception as e:
            logger.error(f"Anthropicプロバイダーの初期化に失敗しました: {e}")
            raise RuntimeError(f"Anthropicプロバイダーの初期化に失敗しました: {e}")

    def _get_system_prompt(self) -> str:
        """システムプロンプトを取得する.

        system_prompt_getterが設定されている場合はそれを使用し、
        失敗時はデフォルト定数にフォールバックする。

        Returns:
            str: システムプロンプト
        """
        if self._system_prompt_getter is not None:
            try:
                return self._system_prompt_getter()
            except Exception as e:
                logger.warning(
                    "プロンプト取得に失敗、"
                    "デフォルトにフォールバック: %s",
                    e,
                )
        return ANALYSIS_SYSTEM_PROMPT

    def analyze(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
        """コンテンツを解析する.

        取得したデータをClaudeで解析し、構造化された問い合わせ情報を生成する。

        Args:
            request: 解析リクエスト

        Returns:
            AIAnalysisResponse: 解析結果

        Raises:
            RuntimeError: プロバイダーが初期化されていない場合
            RuntimeError: 最大リトライ回数を超えた場合
        """
        if not self._initialized or self._client is None:
            raise RuntimeError("プロバイダーが初期化されていません")

        user_prompt = _build_user_prompt(request)
        system_prompt = self._get_system_prompt()

        last_error: Optional[Exception] = None
        for attempt in range(self._config.retry_max):
            try:
                response = self._client.messages.create(
                    model=self._config.model,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self._config.temperature,
                    max_tokens=self._config.max_tokens,
                )

                # Anthropicのレスポンスからテキストを抽出
                raw_content = ""
                if response.content and len(response.content) > 0:
                    raw_content = response.content[0].text or ""

                parsed = self._parse_response(raw_content)

                return AIAnalysisResponse(
                    title=parsed.get("title", "タイトル未設定"),
                    content=parsed.get("content", ""),
                    priority=parsed.get("priority", "medium"),
                    category=parsed.get("category"),
                    confidence_score=self._normalize_confidence(
                        parsed.get("confidence_score", 0.8)
                    ),
                    raw_response={"raw_content": raw_content, "parsed": parsed},
                    provider_type=self.provider_type.value,
                    model=self._config.model,
                )

            except Exception as e:
                last_error = e
                retry_max = self._config.retry_max
                logger.warning(
                    f"Anthropic API呼び出しに失敗しました(試行 {attempt + 1}/{retry_max}): {e}"
                )

                if attempt < self._config.retry_max - 1:
                    # 指数バックオフ
                    wait_time = self._config.retry_backoff_base**attempt
                    logger.info(f"{wait_time}秒後にリトライします")
                    time.sleep(wait_time)

        raise RuntimeError(
            f"Anthropic API呼び出しが最大リトライ回数({self._config.retry_max})を超えました: {last_error}"
        )

    def _parse_response(self, raw_content: str) -> Dict[str, Any]:
        """APIレスポンスをパースする.

        Args:
            raw_content: 生のレスポンス文字列

        Returns:
            Dict[str, Any]: パースされたJSON辞書
        """
        try:
            # JSONブロックを抽出（コードブロックで囲まれている場合）
            content = raw_content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result: Dict[str, Any] = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"JSONパースに失敗しました: {e}")
            # パース失敗時はデフォルト値を返す
            return {
                "title": "解析エラー",
                "content": raw_content,
                "priority": "medium",
                "confidence_score": 0.5,
            }

    def _normalize_confidence(self, score: Any) -> float:
        """信頼度スコアを正規化する.

        Args:
            score: 信頼度スコア（数値または文字列）

        Returns:
            float: 0.0〜1.0の範囲に正規化されたスコア
        """
        try:
            value = float(score)
            return max(0.0, min(1.0, value))
        except (ValueError, TypeError):
            return 0.5

    def health_check(self) -> bool:
        """接続状態を確認する.

        Returns:
            bool: 接続が正常な場合True
        """
        if not self._initialized or self._client is None:
            return False

        try:
            # 短いメッセージを送信して接続確認
            self._client.messages.create(
                model=self._config.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=10,
            )
            return True
        except Exception as e:
            logger.warning(f"Anthropicヘルスチェックに失敗しました: {e}")
            return False

"""ImporterAnalysisServiceモジュール.

Task 6.1: ImporterAnalysisServiceの実装
- AIProviderRegistryとの統合
- 解析用プロンプトの構築（全プロバイダー共通、日本語対応）
- プロバイダー選択機能（引数指定またはデフォルト使用）
- AIレスポンスからAnalysisResultへの変換
- 信頼度に基づくneeds_reviewフラグ判定（閾値0.8）
- AnalysisResultデータクラスの定義

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from models.enums.priority import Priority
from services.importer.ai_provider_base import (AIAnalysisRequest,
                                                AIAnalysisResponse,
                                                AIProviderType)
from services.importer.ai_provider_registry import AIProviderRegistryService
from services.importer.plugin_base import RawImportData
from services.importer.result import BaseError, Result

# ロガー設定
logger = logging.getLogger(__name__)

# 信頼度閾値（この値以上であればneeds_review = False）
CONFIDENCE_THRESHOLD = 0.8


@dataclass
class AnalysisResult:
    """AI解析結果.

    AIプロバイダーによる解析結果を構造化した形式。

    Attributes:
        title: 生成されたタイトル
        content: 構造化された本文
        priority: 推定優先度（Priority列挙型）
        category: カテゴリ（オプション）
        confidence_score: 信頼度スコア（0.0〜1.0）
        needs_review: レビュー必要フラグ
        provider_type: 使用したプロバイダー
        model: 使用したモデル
        analysis_metadata: 解析メタデータ

    契約:
        - confidence_scoreは0.0〜1.0の範囲
        - confidence_score < 0.8の場合、needs_review = True
        - priorityはPriority列挙型の値
    """

    title: str
    content: str
    priority: Priority
    confidence_score: float
    needs_review: bool
    provider_type: str
    model: str
    analysis_metadata: Dict[str, Any]
    category: Optional[str] = None


@dataclass
class AnalysisError(BaseError):
    """解析エラー.

    AI解析処理中に発生したエラーを表す。

    Attributes:
        code: エラーコード（GS-3xx形式）
        message: エラーメッセージ
    """

    pass


class ImporterAnalysisService:
    """問い合わせ解析サービス.

    AIProviderRegistryを使用してプラグインから取得した生データを解析し、
    構造化された問い合わせ情報を生成する。

    契約:
        - Preconditions: raw_data.contentが空でないこと
        - Postconditions: confidence_score < 0.8の場合、needs_review = True
        - Invariants: 日本語コンテンツの解析をサポート
    """

    def __init__(self, provider_registry: AIProviderRegistryService) -> None:
        """ImporterAnalysisServiceを初期化.

        Args:
            provider_registry: AIプロバイダーレジストリ
        """
        self._provider_registry = provider_registry

    def analyze(
        self,
        raw_data: RawImportData,
        provider_type: Optional[AIProviderType] = None,
    ) -> Result[AnalysisResult]:
        """生データを解析し、構造化された問い合わせ情報を生成.

        Args:
            raw_data: プラグインから取得した生データ
            provider_type: 使用するプロバイダー種別（未指定時はデフォルト使用）

        Returns:
            Result[AnalysisResult]: 解析結果
        """
        # プロバイダーを取得
        provider = self._provider_registry.get_provider(provider_type)
        if provider is None:
            provider_name = provider_type.value if provider_type else "デフォルト"
            logger.error(f"AIプロバイダーが見つかりません: {provider_name}")
            return Result.err(
                AnalysisError(
                    code="GS-308",
                    message=f"AIプロバイダーが見つかりません: {provider_name}",
                )
            )

        # AIAnalysisRequestを構築
        request = self._build_request(raw_data)

        # AI解析を実行
        try:
            ai_response = provider.analyze(request)
        except Exception as e:
            logger.error(f"AI解析に失敗しました: {e}")
            return Result.err(
                AnalysisError(
                    code="GS-304",
                    message=f"AI解析に失敗しました: {e}",
                )
            )

        # AIレスポンスをAnalysisResultに変換
        analysis_result = self._convert_response(ai_response, raw_data)

        return Result.ok(analysis_result)

    def _build_request(self, raw_data: RawImportData) -> AIAnalysisRequest:
        """解析用リクエストを構築.

        Args:
            raw_data: プラグインから取得した生データ

        Returns:
            AIAnalysisRequest: 解析リクエスト
        """
        return AIAnalysisRequest(
            content=raw_data.content,
            subject=raw_data.subject,
            sender=raw_data.sender,
            source_type=raw_data.source_type,
            additional_context=raw_data.raw_metadata,
        )

    def _convert_response(
        self, ai_response: AIAnalysisResponse, raw_data: RawImportData
    ) -> AnalysisResult:
        """AIレスポンスをAnalysisResultに変換.

        Args:
            ai_response: AIプロバイダーからのレスポンス
            raw_data: 元の生データ

        Returns:
            AnalysisResult: 変換された解析結果
        """
        # 優先度を変換
        priority = self._convert_priority(ai_response.priority)

        # needs_reviewフラグを判定
        needs_review = self._determine_needs_review(ai_response.confidence_score)

        # メタデータを構築
        analysis_metadata = {
            "raw_response": ai_response.raw_response,
            "source_id": raw_data.source_id,
            "source_type": raw_data.source_type,
        }

        return AnalysisResult(
            title=ai_response.title,
            content=ai_response.content,
            priority=priority,
            category=ai_response.category,
            confidence_score=ai_response.confidence_score,
            needs_review=needs_review,
            provider_type=ai_response.provider_type,
            model=ai_response.model,
            analysis_metadata=analysis_metadata,
        )

    def _convert_priority(self, priority_str: str) -> Priority:
        """優先度文字列をPriority列挙型に変換.

        Args:
            priority_str: 優先度文字列（low/medium/high/urgent）

        Returns:
            Priority: 対応するPriority列挙型値

        Note:
            不明な優先度の場合はPriority.MEDIUMにデフォルト
        """
        priority_map = {
            "low": Priority.LOW,
            "medium": Priority.MEDIUM,
            "high": Priority.HIGH,
            "urgent": Priority.URGENT,
        }
        return priority_map.get(priority_str.lower(), Priority.MEDIUM)

    def _determine_needs_review(self, confidence: float) -> bool:
        """レビュー必要フラグを判定.

        Args:
            confidence: 信頼度スコア（0.0〜1.0）

        Returns:
            bool: レビューが必要な場合True

        Note:
            閾値: 0.8
            confidence >= 0.8 の場合は False
            confidence < 0.8 の場合は True
        """
        return confidence < CONFIDENCE_THRESHOLD

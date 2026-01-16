"""AIプロバイダー基盤モジュール.

Task 2.1: AIプロバイダー共通インターフェースの実装
- AIProviderType列挙型の定義（OPENAI、ANTHROPIC）
- AIProviderConfig基底データクラスの定義
- AIAnalysisRequestデータクラスの定義
- AIAnalysisResponseデータクラスの定義
- AIProvider抽象基底クラスの定義

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from services.importer.plugin_base import ValidationResult

# 設定型のジェネリック型パラメータ
TConfig = TypeVar("TConfig")


class AIProviderType(str, Enum):
    """AIプロバイダー種別.

    サポートされるAIプロバイダーの列挙型。
    将来的にGemini、Local LLM等を追加可能。

    Attributes:
        OPENAI: OpenAI（GPT-4等）
        ANTHROPIC: Anthropic（Claude等）
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass(frozen=True)
class AIProviderConfig:
    """AIプロバイダー共通設定.

    すべてのAIプロバイダーが使用する基本設定。
    プロバイダー固有の設定はこのクラスを継承して定義する。

    Attributes:
        api_key: API認証キー
        model: 使用するモデル名
        temperature: 生成温度（0.0〜1.0）
        max_tokens: 最大生成トークン数
        timeout: API呼び出しタイムアウト（秒）
        retry_max: 最大リトライ回数
        retry_backoff_base: リトライ指数バックオフの基数

    契約:
        - api_keyは機密情報として扱う（ログに出力しない）
        - temperatureは0.0〜1.0の範囲
        - max_tokensはモデルの制限内
    """

    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    retry_max: int = 3
    retry_backoff_base: float = 2.0


@dataclass
class AIAnalysisRequest:
    """AI解析リクエスト.

    プラグインから取得した生データをAIで解析する際のリクエスト形式。

    Attributes:
        content: 解析対象コンテンツ（本文）
        subject: 件名/タイトル
        sender: 送信者情報
        source_type: データソース種別（email, sentry等）
        additional_context: 追加コンテキスト情報

    契約:
        - contentは空でないこと
        - source_typeはプラグインのplugin_typeと一致
    """

    content: str
    subject: str
    sender: str
    source_type: str
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIAnalysisResponse:
    """AI解析レスポンス.

    AIプロバイダーによる解析結果を標準化した形式。

    Attributes:
        title: 生成されたタイトル
        content: 構造化された本文
        priority: 推定優先度（low/medium/high/urgent）
        category: カテゴリ（オプション）
        confidence_score: 信頼度スコア（0.0〜1.0）
        raw_response: プロバイダーからの生レスポンス
        provider_type: 使用したプロバイダー
        model: 使用したモデル

    契約:
        - confidence_scoreは0.0〜1.0の範囲
        - priorityはlow/medium/high/urgentのいずれか
        - raw_responseはプロバイダー固有の形式を保持
    """

    title: str
    content: str
    priority: str
    confidence_score: float
    raw_response: Dict[str, Any]
    provider_type: str
    model: str
    category: Optional[str] = None


class AIProvider(ABC, Generic[TConfig]):
    """AIプロバイダーの抽象基底クラス.

    すべてのAIプロバイダー（OpenAI, Anthropic等）はこのクラスを継承し、
    共通インターフェースを実装する。

    型パラメータ:
        TConfig: プロバイダー固有の設定クラス（AIProviderConfigの派生）

    使用例:
        ```python
        class OpenAIProvider(AIProvider[OpenAIProviderConfig]):
            @property
            def provider_type(self) -> AIProviderType:
                return AIProviderType.OPENAI

            @property
            def supported_models(self) -> List[str]:
                return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]

            def validate_config(self, config: OpenAIProviderConfig) -> ValidationResult:
                # 設定検証ロジック
                pass

            # ... 他のメソッド実装
        ```

    契約:
        - Preconditions: validate_config()が成功していること
        - Postconditions: analyze()はAIAnalysisResponseを返す
        - Invariants: confidence_scoreは0.0〜1.0の範囲
    """

    @property
    @abstractmethod
    def provider_type(self) -> AIProviderType:
        """プロバイダー種別を返す.

        Returns:
            AIProviderType: プロバイダー種別（OPENAI, ANTHROPIC等）
        """
        ...

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """サポートするモデル一覧を返す.

        Returns:
            List[str]: サポートするモデル名のリスト

        Example:
            ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        """
        ...

    @abstractmethod
    def validate_config(self, config: TConfig) -> ValidationResult:
        """設定情報を検証する.

        Args:
            config: プロバイダー固有の設定

        Returns:
            ValidationResult: バリデーション結果
        """
        ...

    @abstractmethod
    def initialize(self) -> None:
        """プロバイダーを初期化する.

        APIクライアントの作成、接続テスト等を実行。

        Raises:
            RuntimeError: 初期化に失敗した場合
        """
        ...

    @abstractmethod
    def analyze(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
        """コンテンツを解析する.

        取得したデータをAIで解析し、構造化された問い合わせ情報を生成する。

        Args:
            request: 解析リクエスト

        Returns:
            AIAnalysisResponse: 解析結果

        Raises:
            RuntimeError: プロバイダーが初期化されていない場合
            APIError: API呼び出しに失敗した場合
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """接続状態を確認する.

        Returns:
            bool: 接続が正常な場合True
        """
        ...

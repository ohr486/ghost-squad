---
inclusion: always
---

# Ghost Squad プロダクト開発ガイドライン

Ghost Squadは、自然言語での問い合わせを構造化されたユーザーストーリーに変換するAI駆動のタスク管理プラットフォームです。このコードベースで作業する際は、以下のプロダクト固有の規約とパターンに従ってください。

## プロダクト概要

**コアバリュー**
- **効率性**: 非構造化要件から構造化ストーリーへの高速変換
- **品質**: ストーリー変換コンテンツの人間によるレビュー・編集機能
- **統合性**: 既存開発ワークフローとの seamless な統合
- **国際化**: 日本語ファーストの設計思想

**ターゲットユーザー**
- プロダクトマネージャー（要件整理・ストーリー作成）
- 開発チームリード（技術要件の構造化）
- スクラムマスター（バックログ管理・スプリント計画）

## 現在の実装状況

### ✅ 実装済み機能

**バックエンド（完全実装）**
- **問い合わせ管理**: 日本語での問い合わせ入力・保存・履歴管理・検索
- **バリデーション層**: InquiryValidator（入力検証、日本語エラーメッセージ、GS-xxxエラーコード体系）
- **データアクセス層**: InquiryRepository（CRUD操作、フィルタリング、ソート、ページネーション）
- **クエリサービス**: InquiryQueryService（一覧取得、検索、フィルタリング、ページネーション）
- **ワークフローサービス**: InquiryWorkflowService（承認・却下処理、ステータス遷移管理）
- **Pydanticスキーマ**: 完全な型安全APIスキーマ（CreateInquiryRequest、UpdateInquiryRequest、InquiryResponse）
- **REST API層**: 問い合わせCRUD + ワークフローエンドポイント完全実装（`routers/inquiry.py`）
- **トランザクション管理**: ロールバック対応、エラーハンドリング強化
- **データ永続化**: PostgreSQL + SQLAlchemy + Alembic
- **開発環境**: Docker Compose + Makefile統合
- **テスト**: 189テスト、高カバレッジ（inquiry: 91%、database接続テスト含む）

**Importer機能（基盤＋AIプロバイダー実装済み）**
- **ダブルプラグインアーキテクチャ**: データソースとAIプロバイダーの二層拡張構造
- **プラグイン基盤**:
  - DataSourcePlugin抽象基底クラス（RawImportData、ValidationResult）
  - PluginRegistryサービス（登録・解除・有効/無効切替）
- **AIプロバイダー基盤**:
  - AIProvider抽象基底クラス（AIAnalysisRequest/Response、AIProviderType列挙型）
  - AIProviderRegistryサービス（登録・初期化・デフォルト設定）
  - OpenAIProvider（GPT-4統合、構造化プロンプト）
  - AnthropicProvider（Claude統合）
- **メールプラグイン**: EmailPlugin（IMAP接続、メール取得・解析、リトライ戦略、EmailPluginConfig）
- **解析サービス**: ImporterAnalysisService（信頼度判定、needs_reviewフラグ、AnalysisResult）
- **エラーログ管理**: ImportErrorLogRepository（エラー記録・統計・自動解決マーク）
- **共通Result型**: Rust風Result型によるエラーハンドリング
- **エラーコード体系**:
  - GS-301〜GS-309: プラグイン管理エラー
  - GS-310〜GS-319: メールプラグイン設定エラー
  - GS-320〜GS-329: メール接続・認証エラー
  - GS-304: AI解析失敗
  - GS-306: データ取得失敗
  - GS-308: AIプロバイダー未登録

**プロンプト管理（フルスタック実装済み）**
- **プロンプト一元管理**: DB管理化、WebUI経由の編集・リセット・テスト実行
- **TTLキャッシュ**: 60秒インメモリキャッシュ + DB障害時フォールバック
- **編集ロック**: 楽観的排他制御（30分タイムアウト）
- **プレースホルダー検証**: {variable_name}構文のバリデーション
- **テスト実行**: AIプロバイダー経由のプロンプトテスト（30秒タイムアウト）
- **シーダー**: アプリ起動時デフォルトプロンプト自動投入（冪等性保証）
- **テスト**: 225バックエンドテスト + フロントエンドテスト

**フロントエンド（基盤完成、98%実装）**
- **TypeScript基盤**: strict mode、型定義完備（InquiryResponse、StoryResponse等）
- **APIクライアント**: Axios統合、エラーハンドリング、CORS対応
- **状態管理**: TanStack React Query 5.8.4（サーバー状態管理）
- **Inquiryコンポーネント**:
  - InquiryForm（問い合わせ入力、React Hook Form + Zod、100% statements）
  - InquiryList（一覧表示、ページネーション、フィルタリング、84.21% statements）
  - InquiryDetail（詳細・編集・承認/却下・ストーリー生成トリガー、94.64% statements）
- **Storyコンポーネント**:
  - StoryList（一覧表示、ページネーション、フィルタ、ソート、95.83% statements）
  - StoryForm（作成フォーム、React Hook Form + Zod、モーダル）
  - StoryDetail（詳細・編集・承認/却下/削除、93.85% statements）
- **E2E統合テスト**: StoryIntegration.test.tsx（ストーリー生成・作成・承認/却下フロー）
- **テスト**: 178テスト、10スイート（Jest + React Testing Library）
- **コード品質**: Prettier + ESLint設定完備

### 🚧 開発中機能
- **フロントエンド統合**: レスポンシブデザイン最適化、E2Eテスト
- **ストーリー管理**: バックエンド・フロントエンド実装完了、統合テスト・UI最適化が進行中

## ドメインモデル

**主要エンティティ**
- **Inquiry（問い合わせ）**: ユーザーからの自然言語入力
  - 日本語サポート必須
  - 音声入力対応（将来機能）
  - 添付ファイル対応（画像、文書）
- **Story（ストーリー）**: 構造化されたユーザーストーリー
  - タイトル、説明、受け入れ基準を含む
  - 優先度分類
  - 工数見積もり（ストーリーポイント）
- **Template（テンプレート）**: 再利用可能なストーリーパターン
  - 業界別・機能別テンプレート
  - カスタムテンプレート作成機能

**ビジネスルール**
- すべてのストーリーは生成後にレビュー状態（waiting_review）になる
- ストーリーは必ず問い合わせ（inquiry_id）に関連付けられる
- ステータス遷移は一方向（waiting_review → approved/rejected）
- 却下時は理由（reason）が必須
- 問い合わせ履歴は監査ログとして保持

**API設計原則**

**現在実装済みのRESTful設計**
```
# 実装済み（Inquiry API - 完全実装）
POST   /api/inquiries              # 問い合わせ作成
GET    /api/inquiries              # 問い合わせ一覧（ページネーション・フィルタリング・ソート）
GET    /api/inquiries/{id}         # 問い合わせ詳細
PUT    /api/inquiries/{id}         # 問い合わせ更新
POST   /api/inquiries/{id}/approve # 承認処理
POST   /api/inquiries/{id}/reject  # 却下処理

# システムエンドポイント
GET    /health                     # ヘルスチェック

# 実装中（Story API - サービス層完了、API層実装中）
GET    /api/stories                # ストーリー一覧（実装済み）
GET    /api/stories/{id}           # ストーリー詳細（実装済み）
POST   /api/inquiries/{id}/stories # ストーリー生成（AI or 手動）（実装済み）
PUT    /api/stories/{id}           # ストーリー編集（実装済み）
POST   /api/stories/{id}/approve   # ストーリー承認（実装済み）
POST   /api/stories/{id}/reject    # ストーリー却下（実装済み）
DELETE /api/stories/{id}           # ストーリー削除（実装済み）
POST   /api/stories/batch-approve  # 一括承認（実装済み）

# 実装済み（Prompt API - 完全実装）
GET    /api/prompts                # プロンプト一覧（カテゴリフィルタ）
GET    /api/prompts/{key}          # プロンプト詳細
PUT    /api/prompts/{key}          # プロンプト更新
POST   /api/prompts/{key}/reset    # デフォルトリセット
POST   /api/prompts/{key}/lock     # 編集ロック取得
DELETE /api/prompts/{key}/lock     # 編集ロック解放
POST   /api/prompts/test           # テスト実行

# 将来実装
GET    /api/templates          # テンプレート一覧
POST   /api/templates          # カスタムテンプレート作成
```

**レスポンス標準化**
```json
{
  "data": {},           // 実際のデータ
  "meta": {             // メタデータ
    "page": 1,
    "limit": 20,
    "total": 100,
    "has_next": true
  },
  "errors": [],         // エラー情報（該当時のみ）
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**エラーハンドリング標準**
- HTTP ステータスコード準拠
- 日本語エラーメッセージ
- エラーコード体系（GS-001形式）
- 詳細なエラー情報（開発環境のみ）

**データモデル設計**

**実装済みステータス管理**
```python
# 問い合わせステータス（実装済み）
class InquiryStatus(Enum):
    RECEIVED = "received"                    # 受付済み
    TASK_WORKING = "task_working"           # タスク作業中（承認済み、AI変換待ち）
    PROCESSING = "processing"                # AI処理中（ストーリー生成中）
    COMPLETED = "completed"                  # 完了（タスク作業完了）
    REJECTED = "rejected"                    # 却下済み
    NEEDS_CLARIFICATION = "needs_clarification"  # 明確化要求（将来実装）

# ストーリーステータス（実装済み）
class StoryStatus(Enum):
    PENDING_REVIEW = "pending_review"        # レビュー待ち
    APPROVED = "approved"                    # 承認済み
    REJECTED = "rejected"                    # 拒否

# 優先度（実装済み）
class Priority(Enum):
    LOW = "low"                             # 低
    MEDIUM = "medium"                       # 中
    HIGH = "high"                          # 高
    URGENT = "urgent"                      # 緊急
```

**問い合わせワークフロー（実装済み）**

問い合わせのステータス遷移は以下の通り：
- `received` → `task_working`: 承認操作
- `received` → `rejected`: 却下操作
- `received` → `needs_clarification`: 明確化要求（将来実装）
- `needs_clarification` → `received`: 明確化完了（将来実装）
- `task_working` → `processing`: AI変換開始（StoryGenerationServiceで実装済み）
- `processing` → `completed`: タスク完了（StoryGenerationServiceで実装済み）

**ストーリーワークフロー（実装済み）**

ストーリーのステータス遷移は以下の通り：
- `waiting_review` → `approved`: 承認操作（StoryWorkflowService）
- `waiting_review` → `rejected`: 却下操作（StoryWorkflowService）
- 却下時は理由（reason）が必須
- ステータス履歴は story_metadata に記録される

**実装済みフィールド設計**
```python
# 全エンティティ共通（BigInteger ID使用）
id: int                        # 一意識別子（BigInteger、自動インクリメント）
created_at: datetime          # 作成日時（UTC）
updated_at: datetime          # 更新日時（UTC）

# 問い合わせ固有（実装済み）
user_id: str                  # ユーザーID
content: str                  # 問い合わせ内容（必須）
language: str = "ja"          # 言語（デフォルト日本語）
timestamp: datetime           # タイムスタンプ
status: InquiryStatus         # ステータス
inquiry_metadata: dict        # メタデータ（JSON）
                              # - rejection: 却下情報（rejected_at、reason）
                              # - status_history: ステータス変更履歴

# ストーリー固有（実装済み: データモデル・リポジトリ）
inquiry_id: int               # 問い合わせID（外部キー、必須）
title: str                    # タイトル（必須、最大500文字）
description: str              # 説明（必須）
priority: Priority            # 優先度
status: StoryStatus           # ステータス
estimated_effort: float       # 推定工数（オプショナル）
deadline: datetime           # 期限（オプショナル）
assignee: str                # 担当者（オプショナル、最大50文字）
story_metadata: dict         # メタデータ（JSON、approval/rejection/status_history記録用）
```

## AI統合ガイドライン

**OpenAI API使用パターン**
```python
# プロンプト構造化
STORY_GENERATION_PROMPT = """
以下の問い合わせから、アジャイル開発で使用するユーザーストーリーを生成してください。

問い合わせ内容：
{inquiry_content}

出力形式：
- タイトル：[簡潔なタイトル]
- 説明：As a [ユーザー], I want [機能] so that [価値]
- 受け入れ基準：
  1. [具体的な基準1]
  2. [具体的な基準2]
  ...

テンプレート（参考）：
{template_content}
"""

# リトライ戦略
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def generate_story(inquiry: str, template: Optional[str] = None):
    # ストーリー変換ロジック
    pass
```

**AI品質保証**
- 生成結果の構造検証（必須フィールドチェック）
- 不適切コンテンツフィルタリング
- 生成時間監視（タイムアウト設定）
- 使用量追跡・コスト管理

## ユーザー体験設計

**ワークフロー最適化**
1. **問い合わせ入力**: 自然言語 + 添付ファイル対応
2. **AI処理**: リアルタイム進捗表示 + 推定完了時間
3. **レビュー・編集**: インライン編集 + 変更履歴
4. **承認**: ワンクリック承認 + 一括承認

**レスポンシブ設計**
- モバイルファースト（スマートフォン対応）
- タブレット最適化（レビュー作業効率化）
- デスクトップ高機能版（一括操作・詳細分析）

**アクセシビリティ**
- WCAG 2.1 AA準拠
- キーボードナビゲーション対応
- スクリーンリーダー対応
- 高コントラストモード

## 国際化・ローカライゼーション

**言語サポート**
- **主要言語**: 日本語（デフォルト）
- **副次言語**: 英語（技術用語・API）
- **将来対応**: 中国語、韓国語

**日本語特有の考慮事項**
- 文字数制限（全角・半角考慮）
- 日付フォーマット（和暦対応検討）
- 敬語・丁寧語の適切な使用
- 業界用語・専門用語の統一

## パフォーマンス要件

**レスポンス時間目標**
- 問い合わせ登録: < 500ms
- ストーリー変換処理: < 30秒（通常 < 10秒）
- ストーリー一覧表示: < 1秒

**スケーラビリティ設計**
- 同時ユーザー数: 100人（初期）→ 1000人（目標）
- ストーリー数: 10,000件（初期）→ 100,000件（目標）
- AI API呼び出し: 1,000回/日（初期）→ 10,000回/日（目標）

## セキュリティ・プライバシー

**データ保護**
- 個人情報の最小化収集
- データ暗号化（保存時・転送時）
- アクセスログ記録
- データ保持期間ポリシー

**AI倫理**
- 生成コンテンツの偏見チェック
- 機密情報の漏洩防止
- AI判断の透明性確保
- 人間による最終承認必須
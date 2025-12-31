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

**フロントエンド（基盤完成、85%実装）**
- **TypeScript基盤**: strict mode、型定義完備（InquiryResponse、CreateInquiryRequest等）
- **APIクライアント**: Axios統合、エラーハンドリング、CORS対応（86.11%カバレッジ）
- **状態管理**: TanStack React Query 5.8.4（サーバー状態管理）
- **コンポーネント**:
  - InquiryForm（問い合わせ入力、React Hook Form + Zod、100% statements）
  - InquiryList（一覧表示、ページネーション、フィルタリング、84.21% statements）
  - InquiryDetail（詳細・編集・承認/却下、94.64% statements）
- **テスト**: 54テスト、91.02%カバレッジ（Jest + React Testing Library）
- **コード品質**: Prettier + ESLint設定完備

### 🚧 開発中機能
- **フロントエンド統合**: ページレイアウト、React Routerルーティング、E2Eテスト
- **AI統合**: OpenAI APIによるストーリー生成
- **ストーリー管理**: レビュー・承認ワークフロー
- **外部統合**: Trello、Jira、GitHub Projects連携

## ドメインモデル

**主要エンティティ**
- **Inquiry（問い合わせ）**: ユーザーからの自然言語入力
  - 日本語サポート必須
  - 音声入力対応（将来機能）
  - 添付ファイル対応（画像、文書）
- **Story（ストーリー）**: 構造化されたユーザーストーリー
  - タイトル、説明、受け入れ基準を含む
  - 優先度・カテゴリ分類
  - 工数見積もり（ストーリーポイント）
- **Template（テンプレート）**: 再利用可能なストーリーパターン
  - 業界別・機能別テンプレート
  - カスタムテンプレート作成機能
- **Export（エクスポート）**: 外部システム連携データ
  - Trello、Jira、GitHub Projects対応
  - カスタムフォーマット対応

**ビジネスルール**
- すべてのストーリーは生成後にレビュー状態になる
- エクスポート前に必ず人間による承認が必要
- テンプレートは組織内で共有可能
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

# 開発中（Story API）
GET    /api/stories                # ストーリー一覧
POST   /api/stories/generate       # ストーリー変換エンドポイント
PUT    /api/stories/{id}           # ストーリー編集
POST   /api/stories/batch          # 一括操作

# 将来実装
GET    /api/templates          # テンプレート一覧
POST   /api/templates          # カスタムテンプレート作成
POST   /api/export/trello      # Trelloエクスポート
POST   /api/export/jira        # Jiraエクスポート
POST   /api/export/github      # GitHub Projectsエクスポート
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
    EXPORTED = "exported"                    # エクスポート済み
    REJECTED = "rejected"                    # 拒否

# 優先度（実装済み）
class Priority(Enum):
    LOW = "low"                             # 低
    MEDIUM = "medium"                       # 中
    HIGH = "high"                          # 高
    URGENT = "urgent"                      # 緊急

# ストーリーカテゴリ（実装済み）
class StoryCategory(Enum):
    DEVELOPMENT = "development"              # 開発
    TESTING = "testing"                     # テスト
    DOCUMENTATION = "documentation"          # ドキュメント
    RESEARCH = "research"                   # 調査
    MAINTENANCE = "maintenance"             # メンテナンス
    CUSTOM = "custom"                      # カスタム
```

**問い合わせワークフロー（実装済み）**

問い合わせのステータス遷移は以下の通り：
- `received` → `task_working`: 承認操作
- `received` → `rejected`: 却下操作
- `received` → `needs_clarification`: 明確化要求（将来実装）
- `needs_clarification` → `received`: 明確化完了（将来実装）
- `task_working` → `processing`: AI変換開始（story specで実装予定）
- `processing` → `completed`: タスク完了（story specで実装予定）

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

# ストーリー固有（実装済み）
inquiry_id: int               # 問い合わせID（外部キー）
title: str                    # タイトル（必須、最大500文字）
description: str              # 説明（必須）
category: StoryCategory       # カテゴリ
priority: Priority            # 優先度
estimated_effort: float       # 推定工数
deadline: datetime           # 期限（オプション）
assignee: str                # 担当者（オプション）
tags: List[str]              # タグ（JSON配列）
dependencies: List[int]       # 依存関係（JSON配列）
story_metadata: dict         # メタデータ（JSON）
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

## 外部システム統合

**エクスポート形式標準**
```python
# Trello形式
{
    "name": "ストーリータイトル",
    "desc": "説明\n\n受け入れ基準:\n- 基準1\n- 基準2",
    "labels": [{"name": "優先度:高", "color": "red"}],
    "due": "2024-12-31",
    "pos": "top"
}

# Jira形式
{
    "fields": {
        "project": {"key": "PROJ"},
        "summary": "ストーリータイトル",
        "description": "説明と受け入れ基準",
        "issuetype": {"name": "Story"},
        "priority": {"name": "High"},
        "customfield_10016": 5  # ストーリーポイント
    }
}
```

**統合パターン**
- アダプターパターンによる外部システム抽象化
- Webhook対応（双方向同期）
- バッチエクスポート機能
- エクスポート履歴・ロールバック機能

## ユーザー体験設計

**ワークフロー最適化**
1. **問い合わせ入力**: 自然言語 + 添付ファイル対応
2. **AI処理**: リアルタイム進捗表示 + 推定完了時間
3. **レビュー・編集**: インライン編集 + 変更履歴
4. **承認**: ワンクリック承認 + 一括承認
5. **エクスポート**: 複数システム同時エクスポート

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
- エクスポート処理: < 5秒

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
# ストーリーボード機能 ギャップ分析

## 分析サマリー

- **分析日**: 2025年12月26日
- **スコープ**: 問い合わせ受付から承認・却下、AI駆動ストーリー変換、ストーリー管理、Web UIまでのエンドツーエンド実装
- **主要な課題**:
  - 問い合わせ編集・検索APIが未実装（バックエンド）
  - 承認・却下ワークフローAPIが未実装（バックエンド）
  - AI変換機能（OpenAI統合）が完全未実装
  - ストーリー管理API全体が未実装（バックエンド）
  - フロントエンド表示・編集・管理コンポーネント群が部分実装
- **推奨アプローチ**: ハイブリッドアプローチ（既存パターン拡張 + 新規コンポーネント作成）
- **実装規模**: Large-XL（要件6つ、複数層にまたがる統合、AI統合含む）
- **リスク**: Medium-High（既存パターン活用可能だが、AI統合、ワークフロー、UI統合に不確実性あり）

---

## 1. 現状調査

### 1.1 既存のドメイン関連資産

#### データベースモデル（完全実装済み）

**InquiryModel** (`backend/models/database/inquiry.py`)
- ✅ 全必須フィールド実装済み
  - `id` (BigInteger), `user_id` (String), `content` (Text), `language` (String)
  - `timestamp` (DateTime), `status` (String), `inquiry_metadata` (JSON)
- ✅ StoryModelとの1対多リレーションシップ設定済み（`stories = relationship(...)`）
- ✅ マイグレーション適用済み（`initial_schema_for_storyboard.py`）
- ✅ デフォルト値: `language='ja'`, `status='received'`, `inquiry_metadata={}`

**StoryModel** (`backend/models/database/story.py`)
- ✅ 全必須フィールド実装済み
  - `id` (BigInteger), `inquiry_id` (BigInteger, 外部キー), `title` (String), `description` (Text)
  - `category` (String), `priority` (String), `estimated_effort` (Float), `deadline` (DateTime, nullable)
  - `status` (String), `assignee` (String, nullable), `tags` (JSON), `dependencies` (JSON)
  - `story_metadata` (JSON), `created_at` (DateTime), `updated_at` (DateTime)
- ✅ InquiryModelとの多対1リレーションシップ設定済み（`inquiry = relationship(...)`）
- ✅ マイグレーション適用済み
- ✅ デフォルト値: `status='pending_review'`, `tags=[]`, `dependencies=[]`, `story_metadata={}`

**StoryTemplateModel** (`backend/models/database/story_template.py`)
- ✅ 全必須フィールド実装済み
  - `id` (BigInteger), `name`, `pattern`, `fields` (JSON), `checklist` (JSON)
  - `default_estimate`, `is_custom`, `user_id` (nullable), `created_at`, `updated_at`
- ✅ マイグレーション適用済み
- ✅ デフォルト値: `fields=[]`, `checklist=[]`, `is_custom=false`

**Enumクラス** (`backend/models/enums/`)
- ✅ `InquiryStatus`: RECEIVED, PROCESSING, NEEDS_CLARIFICATION, TASK_WORKING, COMPLETED, FAILED
- ✅ `StoryStatus`: PENDING_REVIEW, APPROVED, EXPORTED, REJECTED
- ✅ `Priority`: LOW, MEDIUM, HIGH, URGENT
- ✅ `StoryCategory`: DEVELOPMENT, TESTING, DOCUMENTATION, RESEARCH, MAINTENANCE, CUSTOM
- ✅ `StoryPattern`: （実装済み、詳細未確認）

#### API層（部分実装）

**問い合わせAPI** (`backend/api/inquiries.py`)
- ✅ `POST /api/inquiries` - 問い合わせ作成（完全実装、236行のテスト）
  - Pydantic Request/Responseモデル使用
  - 詳細なエラーハンドリング（SQLAlchemyError, ValidationError, 一般Exception）
  - 日本語エラーメッセージ
  - ロギング統合
- ✅ `GET /api/inquiries` - 一覧取得（ページネーション対応）
  - `limit` (1-1000, default: 100), `offset` (>=0, default: 0)
  - `user_id`フィルタリング対応
  - `timestamp DESC, id DESC`でソート
- ✅ `GET /api/inquiries/{id}` - 個別取得
  - 404エラーハンドリング
- ❌ `PUT /api/inquiries/{id}` - 問い合わせ更新（未実装）
- ❌ `PATCH /api/inquiries/{id}/approve` - 承認エンドポイント（未実装）
- ❌ `PATCH /api/inquiries/{id}/reject` - 却下エンドポイント（未実装）
- ❌ 検索・フィルタリング拡張（未実装）

**ストーリーAPI**
- ❌ `backend/api/stories.py` ファイル自体が存在しない
- ❌ ストーリーCRUD操作が全て未実装
  - `GET /api/stories` - 一覧取得
  - `GET /api/stories/{id}` - 個別取得
  - `POST /api/stories` - 作成
  - `PUT /api/stories/{id}` - 更新
  - `DELETE /api/stories/{id}` - 削除
  - `PATCH /api/stories/{id}/approve` - 承認
  - `PATCH /api/stories/{id}/reject` - 拒否
- ❌ AI変換エンドポイント（未実装）
  - `POST /api/inquiries/{id}/convert` - 問い合わせからストーリー変換
  - または `POST /api/stories/generate`

#### サービス層（未実装）

**ディレクトリ構造**
- ❌ `backend/services/` ディレクトリ自体が存在しない
- ❌ 必要なサービスクラス：
  - `AIService` - OpenAI統合、プロンプト管理
  - `StoryService` - ストーリー生成ビジネスロジック
  - `WorkflowService` - ステータス遷移管理（FSM）

#### フロントエンド（部分実装）

**実装済みコンポーネント**
- ✅ `InquiryForm.tsx` (349行) - React Hook Form + Zod バリデーション
  - 入力検証（10-5000文字）
  - 言語選択（ja/en）
  - リアルタイム文字カウント
  - 送信状態管理（idle/loading/success/error）
  - アクセシビリティ対応（aria属性、role属性）
- ✅ `InquiryService.ts` - API呼び出しサービス
  - `createInquiry()`, `getInquiries()`, `getInquiry()` 実装済み
  - `updateInquiry()` フロントエンドコードは存在するが、バックエンドエンドポイント未実装
- ✅ `apiClient.ts` - Axiosベースクライアント（エラーハンドリング統合）
- ✅ 型定義 - 42ファイル、バックエンドと完全対応
  - `types/models/inquiry.ts`, `types/models/story.ts`
  - `types/api/requests.ts`, `types/api/responses.ts`
  - `types/enums/*` (5ファイル)
- ✅ `Layout.tsx` - ナビゲーション、ダークモード対応
- ✅ `useDarkMode.ts` カスタムフック

**未実装コンポーネント**
- ❌ 問い合わせ一覧表示コンポーネント（`InquiriesPage.tsx`は骨格のみ）
- ❌ 問い合わせ編集コンポーネント
- ❌ 問い合わせ詳細表示コンポーネント
- ❌ 承認・却下UIコンポーネント
- ❌ 検索・フィルタリングUIコンポーネント
- ❌ ストーリー表示コンポーネント（一覧、詳細）
- ❌ ストーリー編集コンポーネント
- ❌ ストーリーレビューUIコンポーネント
- ❌ カスタムフック（`useInfiniteInquiries`, `useStories`）

### 1.2 既存の設計パターンと規約

**API設計パターン**（`backend/api/inquiries.py`から抽出）
- FastAPI Router使用（`APIRouter(prefix="/resource", tags=["resource"])`）
- Pydantic Request/Responseモデル使用（`models/api/`から）
- 依存性注入によるDBセッション管理（`Depends(get_db)`）
- 詳細なエラーハンドリング：
  - `SQLAlchemyError` → 500エラー + 日本語メッセージ
  - `ValidationError` → 422エラー + 日本語メッセージ
  - `Exception` → 500エラー + 日本語メッセージ
- ロギング（`logger.error(..., exc_info=True)`）
- HTTPステータスコード適切使用（201, 200, 404, 422, 500）
- ORM to Response変換（`InquiryResponse.model_validate(inquiry)`）

**命名規則**（`structure.md`から）
- ファイル: `snake_case.py`
- クラス: `PascalCase`（例: `InquiryModel`, `InquiryService`）
- 関数・変数: `snake_case`
- Enumメンバー: `UPPER_SNAKE_CASE`
- データベーステーブル: `snake_case`複数形（`inquiries`, `stories`, `story_templates`）

**ディレクトリ構造**
```
backend/
  api/
    __init__.py
    inquiries.py      # ← 既存パターン（207行）
    (stories.py)      # ← 新規作成が必要
  models/
    database/         # ORMモデル（3モデル実装済み）
    schemas/          # Pydanticスキーマ（実装済み）
    api/              # Request/Responseモデル（実装済み）
    enums/            # 列挙型（5種類実装済み）
  services/           # ← ディレクトリ自体が未作成
    (ai_service.py)   # ← 新規必要
    (story_service.py)# ← 新規必要
    (workflow_service.py) # ← 新規必要
```

**フロントエンドパターン**（`InquiryForm.tsx`, `inquiryService.ts`から抽出）
- React Hook Form + Zodバリデーション
- TanStack React Query使用想定（設定済みだが未使用）
- Axiosベースのサービス層（`services/inquiryService.ts`）
- Tailwind CSS + Lucide Reactアイコン
- ダークモード対応（`useDarkMode`フック）
- アクセシビリティ考慮（`aria-label`, `aria-describedby`, `role`属性）
- TypeScript strict mode

### 1.3 統合ポイント

**既存の統合箇所**
- ✅ FastAPI CORS設定（`main.py`）
  - `http://localhost:3000`, `http://127.0.0.1:3000`, `http://frontend:3000`
  - `allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]`
- ✅ PostgreSQL接続管理（`database.py`）
  - `pool_pre_ping=True`, `pool_recycle=300`
  - 環境変数ベース設定（`DATABASE_URL`または個別変数）
- ✅ Alembicマイグレーション管理
  - `initial_schema_for_storyboard.py` 適用済み
- ✅ 環境変数管理（`.env`）
  - `DATABASE_URL`, `OPENAI_API_KEY`, `SECRET_KEY`, `ENVIRONMENT`, `DEBUG`
- ✅ Docker Compose統合
  - backend (FastAPI + Uvicorn), frontend (React), db (PostgreSQL 15 Alpine)
- ✅ OpenAI API依存関係（`requirements.txt`に`openai==1.3.7`）

**不足している統合箇所**
- ❌ OpenAI APIクライアント実装（`AIService`クラス）
- ❌ ストーリー変換サービス層（`StoryService`クラス）
- ❌ ワークフローサービス層（`WorkflowService`クラス、FSM実装）
- ❌ ストーリーAPIルーター登録（`main.py`への`api_router.include_router(story_router)`追加）
- ❌ フロントエンド - バックエンド間のストーリーAPI統合

---

## 2. 要件の実現可能性分析

### 要件1: 問い合わせの作成

**ユーザーストーリー**: 報告者として、自然言語で問い合わせを作成したい。

**技術的ニーズ**
- データモデル: ✅ InquiryModel（実装済み）
- API:
  - ✅ POST /api/inquiries（実装済み）
- UI:
  - ✅ InquiryForm（実装済み）
- バリデーション:
  - ✅ Pydantic（バックエンド、実装済み）
  - ✅ Zod（フロントエンド、実装済み）

**ギャップ**
- なし（要件1は完全実装済み）

**制約**
- 既存のInquiryModelスキーマ維持必須
- BigInteger ID使用（変更不可）

**実装済み**
- ✅ タイムスタンプ自動記録（UTC）
- ✅ 報告者名記録（`user_id`フィールド）
- ✅ 問い合わせ内容記録（`content`フィールド）
- ✅ 報告元システム記録（`inquiry_metadata`に格納可能）
- ✅ 問い合わせ内容必須検証（Pydantic: `min_length=1`, Zod: `min(10)`）
- ✅ 一意識別ID付与（自動インクリメント）
- ✅ ステータス初期値「received」設定
- ✅ エラーハンドリング（保存失敗時のエラーメッセージ）

### 要件2: 問い合わせの一覧表示、検索、編集

**ユーザーストーリー**: ユーザーとして、受け付けた問い合わせの一覧を表示・検索・編集したい。

**技術的ニーズ**
- データモデル: ✅ InquiryModel（実装済み）
- API:
  - ✅ GET /api/inquiries（ページネーション実装済み）
  - ✅ GET /api/inquiries/{id}（実装済み）
  - ❌ PUT /api/inquiries/{id}（未実装）
  - ❌ 検索パラメータ拡張（未実装）
- UI:
  - ❌ 問い合わせ一覧表示コンポーネント（未実装）
  - ❌ 検索UIコンポーネント（未実装）
  - ❌ 編集UIコンポーネント（未実装）

**ギャップ**
- **Missing**: PUT /api/inquiries/{id} エンドポイント
  - 問い合わせ内容、言語の更新
  - 更新タイムスタンプ記録（`updated_at`フィールド追加が必要？）
  - バリデーション（既存のPydanticスキーマ再利用可能）
- **Missing**: 検索機能拡張
  - ステータスフィルタリング（`status`パラメータ）
  - 日付範囲フィルタリング（`timestamp_from`, `timestamp_to`パラメータ）
  - 内容検索（`search`パラメータ、LIKE検索またはFulltext）
- **Missing**: フロントエンド一覧表示コンポーネント
  - TanStack Query `useInfiniteQuery`使用
  - Intersection Observerで無限スクロール
  - ページネーション制御
- **Missing**: フロントエンド編集UIコンポーネント
  - 編集フォーム（InquiryFormの再利用または拡張）
  - 楽観的更新（Optimistic Updates）

**制約**
- ページネーション制約（limit: 1-100、API仕様では1-1000だが、UIでは制限推奨）
- 既存の`user_id`フィルタリング維持

**Complexity**
- 検索機能の複雑性（LIKE検索のパフォーマンス、インデックス追加検討）

### 要件3: 問い合わせの承認と却下

**ユーザーストーリー**: ユーザーとして、受け付けた問い合わせを承認または却下したい。

**技術的ニーズ**
- データモデル: ✅ InquiryModel.status（実装済み）
- API:
  - ❌ PATCH /api/inquiries/{id}/approve（新規必要）
  - ❌ PATCH /api/inquiries/{id}/reject（新規必要）
  - または PUT /api/inquiries/{id} でステータス更新
- ビジネスロジック:
  - ❌ ステータス遷移ルール（FSM実装）
    - RECEIVED → APPROVED/REJECTED
    - 不正遷移の防止（例: COMPLETED → RECEIVED）
  - ❌ タイムスタンプ・承認者記録（`inquiry_metadata`に格納）
- UI:
  - ❌ 承認・却下ボタンコンポーネント（未実装）
  - ❌ ステータス表示バッジ（未実装）

**ギャップ**
- **Missing**: 承認・却下APIエンドポイント
- **Missing**: ステータス遷移バリデーション（FSMパターン）
  - `python-statemachine`ライブラリ使用推奨（research.mdで評価済み）
  - 状態: RECEIVED, APPROVED, REJECTED, PROCESSING, TASK_WORKING, COMPLETED, FAILED
  - イベント: approve, reject, start_conversion, complete, fail
- **Missing**: 承認者情報の記録
  - `inquiry_metadata`に`approved_by`, `approved_at`, `rejected_by`, `rejected_at`を追加
- **Missing**: フロントエンド承認・却下UIコンポーネント
  - ボタンUI（条件付き表示）
  - 確認ダイアログ（誤操作防止）
  - 楽観的更新

**Constraint**
- ステータス遷移ルールの厳格性（後方遷移禁止）

**Research Needed**
- `python-statemachine`ライブラリ統合方法（research.mdで調査済み）
- FSMテスト戦略

### 要件4: 問い合わせからストーリーへの変換

**ユーザーストーリー**: ユーザーとして、承認された問い合わせを構造化されたストーリーに変換したい。

**技術的ニーズ**
- データモデル: ✅ StoryModel（実装済み）
- AI統合:
  - ❌ OpenAI APIクライアント（未実装）
    - `AIService`クラス（`backend/services/ai_service.py`）
  - ❌ ストーリー生成プロンプト設計（未実装）
    - プロンプトテンプレート管理（`backend/services/prompts.py`）
  - ❌ AI応答のパース・バリデーション（未実装）
    - Pydantic Response Model（`backend/models/ai/`）
  - ❌ リトライ戦略（未実装）
    - `tenacity`ライブラリ使用推奨（research.mdで評価済み）
- API:
  - ❌ POST /api/inquiries/{id}/convert（未実装）
  - または POST /api/stories/generate（未実装）
- ビジネスロジック:
  - ❌ 承認済み問い合わせのみ変換可能（ステータスチェック）
  - ❌ 変換失敗時のエラーハンドリング（ステータスを「failed」に更新）
  - ❌ ストーリーと問い合わせの関連付け（外部キー設定済み、ビジネスロジックで実装）
  - ❌ AI処理中ステータス管理（「processing」）
- UI:
  - ❌ ストーリー変換トリガーボタン（未実装）
  - ❌ AI処理中表示（ローディング、進捗表示）
  - ❌ エラー通知UI

**ギャップ**
- **Missing**: OpenAI統合サービス層
  - `backend/services/ai_service.py`
  - GPT-4o (`gpt-4o-2024-08-06`) 使用推奨（research.mdで選定済み）
  - 構造化出力（`response_format`パラメータ）
  - Pydantic Response Model統合
- **Missing**: ストーリー生成プロンプト管理
  - `backend/services/prompts.py`
  - テンプレート変数（`{inquiry_content}`, `{template_hint}`）
- **Missing**: リトライロジック
  - `tenacity`ライブラリ統合（`requirements.txt`に追加）
  - Exponential backoff with jitter（1-60秒、最大6回）
  - 対象エラー: `RateLimitError`, `APIError`, `Timeout`
- **Missing**: AI応答パーサー
  - `backend/models/ai/story_generation.py`
  - Pydantic Response Model: `title`, `description`, `acceptance_criteria`, `category`, `priority`, `estimated_effort`
- **Missing**: ストーリー生成APIエンドポイント
  - POST /api/inquiries/{id}/convert
  - ステータスチェック（APPROVED以外は403エラー）
  - AI処理中ステータス更新（PROCESSING）
  - 成功時: ストーリー作成（PENDING_REVIEW）、問い合わせステータス更新（TASK_WORKING）
  - 失敗時: 問い合わせステータス更新（FAILED）、エラーメッセージ記録
- **Missing**: フロントエンド変換UIコンポーネント
  - 変換ボタン（承認済みのみ表示）
  - ローディング表示
  - エラートースト通知

**Constraint**
- OpenAI API依存（外部サービス）
- API応答時間の不確実性（タイムアウト設定必要: 60秒推奨）
- APIレート制限（使用量モニタリング必要）

**Research Needed**
- プロンプトエンジニアリングのベストプラクティス（research.mdで調査済み）
- 生成品質の評価手法（A/Bテスト、Few-shot例の充実）

### 要件5: ストーリーの管理とレビュー

**ユーザーストーリー**: ユーザーとして、生成されたストーリーを確認・編集・承認したい。

**技術的ニーズ**
- データモデル: ✅ StoryModel（実装済み）
- API:
  - ❌ GET /api/stories（未実装）
  - ❌ GET /api/stories/{id}（未実装）
  - ❌ PUT /api/stories/{id}（未実装）
  - ❌ PATCH /api/stories/{id}/approve（未実装）
  - ❌ PATCH /api/stories/{id}/reject（未実装）
- ビジネスロジック:
  - ❌ ストーリーステータス遷移（PENDING_REVIEW → APPROVED/REJECTED）
  - ❌ 依存関係管理（`dependencies`フィールド）
  - ❌ 担当者・期限設定
- UI:
  - ❌ ストーリー一覧表示（未実装）
  - ❌ ストーリー詳細表示（未実装）
  - ❌ ストーリー編集フォーム（未実装）
  - ❌ 承認・拒否ボタン（未実装）

**ギャップ**
- **Missing**: ストーリーCRUD API（`backend/api/stories.py`）
  - GET /api/stories - 一覧取得（ページネーション、フィルタリング）
  - GET /api/stories/{id} - 個別取得
  - PUT /api/stories/{id} - 更新（title, description, category, priority, estimated_effort, deadline, assignee, tags, dependencies）
  - PATCH /api/stories/{id}/approve - 承認
  - PATCH /api/stories/{id}/reject - 拒否
- **Missing**: ストーリーサービス層（`backend/services/story_service.py`）
  - ストーリーバリデーション
  - 依存関係検証（循環依存防止）
- **Missing**: フロントエンドストーリー表示コンポーネント
  - `frontend/src/components/stories/StoryList.tsx`
  - `frontend/src/components/stories/StoryDetail.tsx`
  - `frontend/src/components/stories/StoryEditForm.tsx`
  - `frontend/src/services/storyService.ts`
  - カスタムフック（`useStories`, `useStory`）

**Constraint**
- ストーリーの削除は慎重に（問い合わせとの関連維持）
- 依存関係の整合性維持

### 要件6: ユーザーインターフェース

**ユーザーストーリー**: 報告者およびユーザーとして、ストーリーボードシステムと対話するための直感的な Web インターフェースが欲しい。

**技術的ニーズ**
- UI:
  - ✅ InquiryForm（実装済み、バリデーション統合）
  - ❌ 問い合わせ履歴表示ページ（未実装）
  - ❌ 問い合わせ詳細・編集ページ（未実装）
  - ❌ ストーリー一覧ページ（未実装）
  - ❌ ストーリー詳細・編集ページ（未実装）
- バリデーション:
  - ✅ Zodスキーマ（InquiryForm実装済み）
  - ❌ ストーリー編集用Zodスキーマ（未実装）

**ギャップ**
- **Missing**: 問い合わせ履歴表示ページ（`InquiriesPage.tsx`の完全実装）
  - 一覧表示（TanStack Query `useInfiniteQuery`）
  - ページネーション/無限スクロール
  - ステータスバッジ表示
  - 検索・フィルタリングUI
- **Missing**: 問い合わせ詳細・編集ページ
  - 詳細情報表示（メタデータ含む）
  - インライン編集または別ページ遷移
  - 承認・却下ボタン
  - ストーリー変換ボタン
- **Missing**: ストーリー一覧ページ（`StoriesPage.tsx`）
  - 一覧表示（カード型またはテーブル型）
  - ステータス別フィルタリング
  - 優先度・カテゴリーフィルタリング
- **Missing**: ストーリー詳細・編集ページ（`StoryDetailPage.tsx`）
  - 詳細情報表示（受入基準、メタデータ、依存関係）
  - 編集フォーム（React Hook Form + Zod）
  - 承認・拒否ボタン
- **Missing**: エラー表示UI
  - フォームバリデーションエラー（InquiryFormでは実装済み、他フォームでも必要）
  - API エラートースト（apiClientでは実装済み、追加のUI改善検討）

**Constraint**
- アクセシビリティ考慮（WCAG 2.1 AA基準）
- ダークモード対応（既存パターン踏襲）

---

## 3. 実装アプローチのオプション

### オプションA: 既存コンポーネント拡張

**拡張対象**
- `backend/api/inquiries.py` に以下を追加:
  - PUT /api/inquiries/{id} エンドポイント
  - PATCH /api/inquiries/{id}/approve エンドポイント
  - PATCH /api/inquiries/{id}/reject エンドポイント
  - POST /api/inquiries/{id}/convert エンドポイント
  - 検索パラメータ拡張（status, timestamp_from, timestamp_to, search）
- `frontend/src/services/inquiryService.ts` に承認・却下メソッド追加
- `frontend/src/pages/InquiriesPage.tsx` に一覧表示・承認UI追加

**互換性評価**
- ✅ 既存のInquiryModelスキーマと完全互換
- ✅ 既存のAPI設計パターンと一貫性維持
- ✅ 後方互換性：既存エンドポイントに影響なし

**複雑性と保守性**
- ✅ 認知負荷：低（既存パターン踏襲）
- ⚠️ ファイルサイズ：inquiries.pyが500行超に増加（やや肥大化）
- ❌ 単一責任原則：問い合わせ関連とストーリー変換が混在（やや違反）

**トレードオフ**
- ✅ 最小限の新規ファイル
- ✅ 既存パターン活用で開発速度向上
- ✅ テストの拡張が容易（既存のtest_inquiry_api.py拡張）
- ❌ inquiries.py が肥大化する可能性（保守性低下）
- ❌ ストーリー関連機能は別ファイル必須（混在不可）
- ❌ AI統合は別サービス必須（APIファイル内にロジック含めるのは不適切）

### オプションB: 新規コンポーネント作成

**新規作成対象**

**バックエンド**
- `backend/api/stories.py` - ストーリーCRUD操作
  - GET /api/stories, GET /api/stories/{id}, PUT /api/stories/{id}
  - PATCH /api/stories/{id}/approve, PATCH /api/stories/{id}/reject
- `backend/services/ai_service.py` - OpenAI統合
  - `generate_story()` メソッド
  - プロンプト管理
  - リトライロジック（tenacity）
- `backend/services/story_service.py` - ストーリー生成ビジネスロジック
  - ストーリーバリデーション
  - 依存関係検証
- `backend/services/workflow_service.py` - ステータス遷移管理
  - `InquiryStateMachine`クラス（python-statemachine）
  - `StoryStateMachine`クラス
- `backend/models/ai/story_generation.py` - AI応答Pydanticモデル
- `backend/services/prompts.py` - プロンプトテンプレート

**フロントエンド**
- `frontend/src/services/storyService.ts` - ストーリーAPIクライアント
- `frontend/src/components/stories/StoryList.tsx` - ストーリー一覧
- `frontend/src/components/stories/StoryDetail.tsx` - ストーリー詳細
- `frontend/src/components/stories/StoryEditForm.tsx` - ストーリー編集
- `frontend/src/components/inquiries/InquiryList.tsx` - 問い合わせ一覧
- `frontend/src/components/inquiries/InquiryDetail.tsx` - 問い合わせ詳細
- `frontend/src/hooks/useInfiniteInquiries.ts` - カスタムフック（無限スクロール）
- `frontend/src/hooks/useStories.ts` - カスタムフック

**統合ポイント**
- FastAPIのルーター統合（`main.py`に`api_router.include_router(story_router)`追加）
- InquiryModel ↔ StoryModel間のリレーションシップ活用
- 共通のエラーハンドリング・ロギングパターン使用
- 共通のPydanticモデル再利用

**責任境界**
- **inquiries.py**: 問い合わせCRUD、承認・却下
- **stories.py**: ストーリーCRUD、承認・拒否
- **ai_service.py**: OpenAI API呼び出し、プロンプト管理
- **story_service.py**: ストーリー生成ビジネスロジック、バリデーション
- **workflow_service.py**: ステータス遷移管理（FSM）

**トレードオフ**
- ✅ 関心の分離が明確
- ✅ 既存コンポーネントへの影響最小
- ✅ テストの独立性向上
- ✅ 将来の拡張性向上（テンプレート管理、外部システム統合）
- ❌ ファイル数増加（ナビゲーション複雑化）
- ❌ 初期開発コスト高
- ❌ 統合テストの複雑性増加

### オプションC: ハイブリッドアプローチ（推奨）

**戦略**
- **既存拡張**: 問い合わせ更新・承認・却下は`inquiries.py`に追加
- **新規作成**: ストーリー管理、AI統合、ワークフローは新規ファイル
- **段階実装**:
  1. **Phase 1**: 問い合わせ更新・承認・却下API実装（inquiries.py拡張）
  2. **Phase 2**: ワークフローサービス実装（workflow_service.py新規）
  3. **Phase 3**: AI統合実装（ai_service.py, story_service.py新規）
  4. **Phase 4**: ストーリーCRUD API実装（stories.py新規）
  5. **Phase 5**: フロントエンド統合（問い合わせ一覧・詳細・編集）
  6. **Phase 6**: フロントエンドストーリー統合（ストーリー一覧・詳細・編集）

**詳細な実装計画**

**Phase 1: 問い合わせ管理拡張（3-4日）**
- `backend/api/inquiries.py` 拡張:
  - PUT /api/inquiries/{id} - 問い合わせ更新
  - 検索パラメータ拡張（status, timestamp_from, timestamp_to, search）
- `backend/models/api/requests.py` 拡張:
  - `InquiryUpdateRequest`クラス追加
- テスト拡張:
  - `backend/tests/test_inquiry_api.py` に更新・検索テスト追加

**Phase 2: ワークフローサービス実装（3-4日）**
- `backend/services/workflow_service.py` 新規作成:
  - `InquiryStateMachine`クラス（python-statemachine）
  - `StoryStateMachine`クラス
  - ステータス遷移ルール定義
  - コールバック実装（タイムスタンプ、承認者記録）
- `backend/api/inquiries.py` 拡張:
  - PATCH /api/inquiries/{id}/approve
  - PATCH /api/inquiries/{id}/reject
  - ワークフローサービス統合
- 依存関係追加:
  - `requirements.txt`に`python-statemachine`追加
- テスト:
  - `backend/tests/test_workflow_service.py` 新規作成
  - FSMテストケース（正常遷移、不正遷移、コールバック）

**Phase 3: AI統合実装（4-5日）**
- `backend/services/ai_service.py` 新規作成:
  - `AIService`クラス
  - `generate_story()` メソッド
  - OpenAI API呼び出し（GPT-4o）
  - 構造化出力（`response_format`）
  - リトライロジック（tenacity）
- `backend/services/prompts.py` 新規作成:
  - プロンプトテンプレート定義
  - テンプレート変数（`{inquiry_content}`, `{template_hint}`）
- `backend/models/ai/story_generation.py` 新規作成:
  - `StoryGenerationResponse` Pydanticモデル
- `backend/services/story_service.py` 新規作成:
  - `StoryService`クラス
  - `create_story_from_inquiry()` メソッド
  - ストーリーバリデーション
- `backend/api/inquiries.py` 拡張:
  - POST /api/inquiries/{id}/convert
  - AI統合、ステータス管理
- 依存関係追加:
  - `requirements.txt`に`tenacity`追加
- テスト:
  - `backend/tests/test_ai_service.py` 新規作成（モック使用）
  - `backend/tests/test_story_service.py` 新規作成

**Phase 4: ストーリーCRUD API実装（3-4日）**
- `backend/api/stories.py` 新規作成:
  - GET /api/stories（ページネーション、フィルタリング）
  - GET /api/stories/{id}
  - PUT /api/stories/{id}
  - PATCH /api/stories/{id}/approve
  - PATCH /api/stories/{id}/reject
- `backend/models/api/requests.py` 拡張:
  - `StoryUpdateRequest`（既存、確認）
- `backend/main.py` 拡張:
  - `api_router.include_router(story_router)`
- テスト:
  - `backend/tests/test_story_api.py` 新規作成

**Phase 5: フロントエンド問い合わせ統合（3-4日）**
- `frontend/src/components/inquiries/InquiryList.tsx` 新規作成:
  - TanStack Query `useInfiniteQuery`
  - 無限スクロール（Intersection Observer）
  - ステータスバッジ表示
- `frontend/src/components/inquiries/InquiryDetail.tsx` 新規作成:
  - 詳細情報表示
  - 承認・却下ボタン
  - ストーリー変換ボタン
- `frontend/src/hooks/useInfiniteInquiries.ts` 新規作成:
  - カスタムフック
- `frontend/src/services/inquiryService.ts` 拡張:
  - `updateInquiry()`, `approveInquiry()`, `rejectInquiry()`, `convertInquiry()`
- `frontend/src/pages/InquiriesPage.tsx` 拡張:
  - InquiryList統合
- テスト:
  - コンポーネントテスト追加

**Phase 6: フロントエンドストーリー統合（3-4日）**
- `frontend/src/components/stories/StoryList.tsx` 新規作成
- `frontend/src/components/stories/StoryDetail.tsx` 新規作成
- `frontend/src/components/stories/StoryEditForm.tsx` 新規作成
- `frontend/src/services/storyService.ts` 新規作成
- `frontend/src/hooks/useStories.ts` 新規作成
- `frontend/src/pages/StoriesPage.tsx` 新規作成（または`TasksPage.tsx`を拡張）
- `frontend/src/App.tsx` 拡張:
  - `/stories`ルート追加
- テスト:
  - コンポーネントテスト追加

**リスク軽減**
- 段階的なリリースで問題の早期発見
- 各フェーズでのテスト充実（ユニット、統合）
- AI統合の技術的不確実性をPhase 3に隔離（他機能への影響最小化）
- フェーズごとのレビューとフィードバック

**トレードオフ**
- ✅ バランスの取れたアプローチ
- ✅ 段階的な価値提供（Phase 1-2で承認ワークフロー提供）
- ✅ リスクの分散
- ✅ テスト戦略が明確
- ❌ フェーズ間の調整コスト（インターフェース設計の前倒し必要）
- ❌ 初期フェーズで全機能提供不可（ユーザー期待管理必要）

---

## 4. 実装複雑性とリスク

### 実装規模

**Effort: L-XL (Large-XL, 2-3週間)**

**根拠**
- Phase 1（問い合わせ管理拡張）: 3-4日
- Phase 2（ワークフロー実装）: 3-4日
- Phase 3（AI統合）: 4-5日
- Phase 4（ストーリーCRUD API）: 3-4日
- Phase 5（フロントエンド問い合わせ）: 3-4日
- Phase 6（フロントエンドストーリー）: 3-4日
- 統合テスト・デバッグ: 2-3日
- **合計**: 21-28日（3-4週間）

**複雑性シグナル**
- ✅ 単純CRUD: 問い合わせ・ストーリーの基本操作
- ⚠️ ワークフローロジック: ステータス遷移ルール、FSM実装
- ⚠️ AI統合: OpenAI API、プロンプト設計、リトライロジック
- ⚠️ 外部統合: OpenAI API依存、レート制限対応

### リスク評価

**Risk: Medium-High**

**High Riskの要素**
- **AI統合の不確実性**:
  - OpenAI APIの応答品質（プロンプトチューニング必要）
  - APIレスポンス時間の変動（タイムアウト設定: 60秒推奨）
  - 使用量制限・コスト管理（モニタリング必須）
  - レート制限エラー（tenacityリトライ必須）
  - **対策**:
    - プロンプトテンプレートのA/Bテスト
    - Few-shot例の充実
    - レート制限モニタリングとアラート
    - フォールバック処理（手動ストーリー作成）

- **ワークフロー複雑性**:
  - ステータス遷移ルールの正確な実装
  - 不正遷移の防止（例: COMPLETED → RECEIVED）
  - 並行更新時の競合（楽観的ロック検討）
  - **対策**:
    - python-statemachineライブラリ使用（グラフ検証機能）
    - 包括的なFSMテストスイート
    - ステータス遷移図のMermaid文書化

**Medium Riskの要素**
- **新規パターン導入**:
  - サービス層の設計（既存に前例なし）
  - AI応答パーサーの実装（JSON Schema検証）
  - **対策**:
    - 既存のAPI設計パターン踏襲
    - OpenAI SDKのPydanticネイティブサポート使用

- **統合テスト範囲**:
  - フロントエンド ↔ バックエンド統合
  - AI ↔ データベース統合
  - **対策**:
    - E2Eテスト実装
    - CI/CDパイプラインでの自動テスト

- **UI/UX複雑性**:
  - 無限スクロールのメモリリーク
  - 楽観的更新の整合性
  - **対策**:
    - Windowingテクニック（近隣ページのみ状態保持）
    - TanStack Queryのキャッシュ戦略設定
    - 楽観的更新のロールバック処理

**Low Riskの要素**
- **既存パターン活用**:
  - 問い合わせAPI拡張（inquiries.pyパターン踏襲）
  - データベーススキーマ（変更不要）
  - フロントエンドサービス層（InquiryService参考）
  - **対策**: なし（既存実績あり）

---

## 5. 要件-資産マップ

| 要件 | 必要な資産 | 状態 | ギャップ | タグ |
|------|-----------|------|---------|------|
| **要件1: 問い合わせの作成** | | | | |
| | InquiryModel | ✅ 実装済み | - | - |
| | POST /api/inquiries | ✅ 実装済み | - | - |
| | InquiryForm | ✅ 実装済み | - | - |
| | Pydantic/Zodバリデーション | ✅ 実装済み | - | - |
| **要件2: 問い合わせの一覧表示、検索、編集** | | | | |
| | GET /api/inquiries（ページネーション） | ✅ 実装済み | - | - |
| | GET /api/inquiries/{id} | ✅ 実装済み | - | - |
| | PUT /api/inquiries/{id} | ❌ 未実装 | バックエンド更新API | **Missing** |
| | 検索パラメータ拡張 | ❌ 未実装 | status, timestamp, search | **Missing** |
| | InquiryList UI | ❌ 未実装 | 一覧表示、無限スクロール | **Missing** |
| | InquiryDetail UI | ❌ 未実装 | 詳細表示、編集UI | **Missing** |
| | useInfiniteInquiries | ❌ 未実装 | カスタムフック | **Missing** |
| **要件3: 問い合わせの承認と却下** | | | | |
| | InquiryModel.status | ✅ 実装済み | - | - |
| | PATCH /api/inquiries/{id}/approve | ❌ 未実装 | 承認エンドポイント | **Missing** |
| | PATCH /api/inquiries/{id}/reject | ❌ 未実装 | 却下エンドポイント | **Missing** |
| | ステータス遷移FSM | ❌ 未実装 | WorkflowService, python-statemachine | **Missing** |
| | 承認者記録 | ❌ 未実装 | inquiry_metadata拡張 | **Missing** |
| | 承認・却下UI | ❌ 未実装 | ボタンコンポーネント、確認ダイアログ | **Missing** |
| **要件4: 問い合わせからストーリーへの変換** | | | | |
| | StoryModel | ✅ 実装済み | - | - |
| | OpenAI APIクライアント | ❌ 未実装 | AIService, GPT-4o統合 | **Missing** |
| | プロンプト管理 | ❌ 未実装 | prompts.py | **Missing**, **Unknown** |
| | AI応答パーサー | ❌ 未実装 | StoryGenerationResponse Pydantic | **Missing** |
| | リトライロジック | ❌ 未実装 | tenacity統合 | **Missing** |
| | POST /api/inquiries/{id}/convert | ❌ 未実装 | 変換エンドポイント | **Missing** |
| | StoryService | ❌ 未実装 | ストーリー生成ビジネスロジック | **Missing** |
| | 変換UI | ❌ 未実装 | ボタン、ローディング、エラー通知 | **Missing** |
| | OpenAI API使用量制限対応 | ❌ 未実装 | モニタリング、アラート | **Unknown** |
| **要件5: ストーリーの管理とレビュー** | | | | |
| | GET /api/stories | ❌ 未実装 | 一覧取得API | **Missing** |
| | GET /api/stories/{id} | ❌ 未実装 | 個別取得API | **Missing** |
| | PUT /api/stories/{id} | ❌ 未実装 | 更新API | **Missing** |
| | PATCH /api/stories/{id}/approve | ❌ 未実装 | 承認API | **Missing** |
| | PATCH /api/stories/{id}/reject | ❌ 未実装 | 拒否API | **Missing** |
| | ストーリーステータス遷移FSM | ❌ 未実装 | StoryStateMachine | **Missing** |
| | StoryList UI | ❌ 未実装 | 一覧表示 | **Missing** |
| | StoryDetail UI | ❌ 未実装 | 詳細表示 | **Missing** |
| | StoryEditForm UI | ❌ 未実装 | 編集フォーム | **Missing** |
| | storyService.ts | ❌ 未実装 | APIクライアント | **Missing** |
| | useStories | ❌ 未実装 | カスタムフック | **Missing** |
| **要件6: ユーザーインターフェース** | | | | |
| | InquiryForm | ✅ 実装済み | - | - |
| | 問い合わせ履歴ページ | ❌ 未実装 | InquiriesPage完全実装 | **Missing** |
| | 問い合わせ詳細ページ | ❌ 未実装 | InquiryDetailPage | **Missing** |
| | ストーリー一覧ページ | ❌ 未実装 | StoriesPage | **Missing** |
| | ストーリー詳細ページ | ❌ 未実装 | StoryDetailPage | **Missing** |
| | フォームバリデーション | ✅ 実装済み（Inquiry） | ストーリー編集Zodスキーマ | **Missing** |

---

## 6. 設計フェーズへの推奨事項

### 推奨アプローチ

**オプションC（ハイブリッドアプローチ）を推奨**

**理由**
1. 既存のinquiries.pyパターンを活用しつつ、ストーリー管理・AI統合は新規分離
2. 段階的な実装でリスク軽減（各フェーズでのテスト充実）
3. AI統合の不確実性をPhase 3に隔離（他機能への影響最小化）
4. テスト戦略が明確（フェーズごとのユニット・統合テスト）
5. 段階的な価値提供（Phase 1-2で承認ワークフロー、Phase 3-4でAI変換）

### 主要な設計決定事項

**Phase 1: 問い合わせ管理完成**
1. **決定**: PUT /api/inquiries/{id} 実装方法
   - オプションA: 汎用的なPUTエンドポイント（全フィールド更新可能）
   - オプションB: PATCH専用エンドポイント（/approve, /reject）のみ
   - 推奨: **オプションA（汎用PUT）+ オプションB（専用PATCH）併用**
   - 根拠: 汎用PUTで編集機能実現、専用PATCHでワークフロー明確化

2. **決定**: 検索機能の実装範囲
   - オプションA: LIKE検索のみ
   - オプションB: PostgreSQL Full-text Search
   - 推奨: **オプションA（LIKE検索）** 初期実装、必要に応じてオプションB移行
   - 根拠: MVP段階ではLIKE検索で十分、インデックス追加でパフォーマンス改善

**Phase 2: ワークフロー実装**
1. **決定**: ステータス遷移ルール
   - FSMライブラリ: **python-statemachine** (research.mdで評価済み)
   - 状態: RECEIVED, APPROVED, REJECTED, PROCESSING, TASK_WORKING, COMPLETED, FAILED
   - イベント: approve, reject, start_conversion, complete, fail
   - 許可されない遷移時のエラー: 403 Forbidden + 日本語エラーメッセージ

2. **決定**: 承認者情報の記録
   - `inquiry_metadata`に以下を追加:
     - `approved_by` (user_id), `approved_at` (timestamp)
     - `rejected_by` (user_id), `rejected_at` (timestamp)
   - コールバック: `on_enter_approved`, `on_enter_rejected`でメタデータ更新

**Phase 3: AI統合**
1. **決定**: OpenAI APIモデル選択
   - **GPT-4o** (`gpt-4o-2024-08-06`) (research.mdで選定済み)
   - 根拠: 構造化出力ネイティブサポート、コストパフォーマンス良好

2. **決定**: プロンプト管理方法
   - **コード内ハードコード（初期実装）** → データベース管理（将来）
   - `backend/services/prompts.py`にテンプレート定義
   - テンプレート変数: `{inquiry_content}`, `{template_hint}`

3. **決定**: AI生成失敗時のハンドリング
   - リトライ戦略: **tenacity**ライブラリ、Exponential backoff with jitter（1-60秒、最大6回）
   - 対象エラー: `RateLimitError`, `APIError`, `Timeout`
   - フォールバック: 問い合わせステータスを「failed」に更新、エラーメッセージ記録
   - ユーザー通知: エラートースト + 手動ストーリー作成リンク

4. **決定**: タイムアウト設定
   - OpenAI API呼び出しタイムアウト: **60秒**
   - 根拠: GPT-4oの応答時間（通常10-30秒）+ マージン

**Phase 4: ストーリー管理API**
1. **決定**: ストーリーCRUD APIの設計
   - RESTful設計（GET, PUT）、DELETE除外（問い合わせ削除でカスケード）
   - フィルタリング: status, priority, category, assignee
   - ソート: created_at DESC, priority, deadline

2. **決定**: ストーリーと問い合わせの関連管理
   - 問い合わせ削除時のストーリーカスケード処理: **CASCADE DELETE**（既存設定維持）
   - 複数ストーリー生成の可否: **1問い合わせ → 1ストーリー**（初期実装）、将来的に複数対応検討

**Phase 5-6: フロントエンド統合**
1. **決定**: 状態管理戦略
   - **TanStack Query単独**（research.mdで選定済み）
   - キャッシュ戦略: `staleTime: 5分`, `cacheTime: 30分`
   - 楽観的更新: 承認・却下操作で適用

2. **決定**: ページネーション戦略
   - **無限スクロール**（TanStack Query `useInfiniteQuery`）
   - Intersection Observerでスクロール末尾の自動ロード
   - ページ上限: 10ページ（メモリリーク防止）

3. **決定**: リアルタイム更新
   - **ポーリング**（初期実装）、5秒間隔
   - WebSocket: 将来機能として保留

### Research Items（設計フェーズで調査）

1. **OpenAI統合**（research.mdで調査済み）
   - ✅ ベストプラクティス調査（プロンプトエンジニアリング）
   - ✅ レート制限・コスト管理手法
   - ✅ エラーハンドリングパターン

2. **FSMパターン実装**（research.mdで調査済み）
   - ✅ python-statemachineライブラリ統合
   - ⚠️ テスト戦略（設計フェーズで詳細化）

3. **フロントエンドコンポーネント設計**
   - ⚠️ アクセシビリティガイドライン適用（WCAG 2.1 AA）
   - ⚠️ ダークモード対応パターン（既存踏襲）

4. **パフォーマンス最適化**（設計フェーズで調査）
   - ⚠️ LIKE検索のインデックス戦略
   - ⚠️ TanStack Queryキャッシュ戦略の詳細設定
   - ⚠️ 無限スクロールのWindowingテクニック

---

## 7. 次のステップ

### 設計フェーズへの移行

**完了条件**
- ✅ ギャップ分析完了
- ✅ 実装アプローチ決定（ハイブリッド推奨）
- ✅ 主要な設計課題の特定
- ✅ リスク評価完了

**設計フェーズで実施すべき内容**
1. **詳細なAPI設計**（OpenAPI仕様）
   - 問い合わせ拡張API（PUT, PATCH /approve, PATCH /reject, POST /convert）
   - ストーリーCRUD API（GET, PUT, PATCH /approve, PATCH /reject）
   - リクエスト・レスポンスモデル定義
2. **サービス層の設計**（クラス図、シーケンス図）
   - AIService, StoryService, WorkflowService
   - 依存関係、インターフェース設計
3. **AI統合の詳細設計**
   - プロンプトテンプレート設計（Few-shot例含む）
   - エラーハンドリングフロー
   - リトライロジック詳細
4. **FSM設計**
   - ステータス遷移図（Mermaid）
   - コールバック処理詳細
5. **フロントエンドコンポーネント設計**
   - コンポーネント階層図
   - 状態管理フロー
   - UIワイヤーフレーム
6. **テスト戦略策定**
   - ユニットテスト範囲（目標カバレッジ80%）
   - 統合テスト範囲
   - E2Eテストシナリオ

**設計ドキュメント生成コマンド**
```bash
/kiro:spec-design storyboard
```

または要件を自動承認して直接設計フェーズに進む場合
```bash
/kiro:spec-design storyboard -y
```

---

## 付録A: 技術スタック確認

### 既存の依存関係（活用可能）

**バックエンド**
- ✅ FastAPI 0.104.1
- ✅ SQLAlchemy 2.0.23
- ✅ Pydantic 2.5.0
- ✅ OpenAI 1.3.7（依存関係追加済み、未使用）
- ✅ pytest 7.4.3 + hypothesis 6.92.1（PBT）
- ✅ black 23.11.0 + flake8 6.1.0 + mypy 1.7.1

**フロントエンド**
- ✅ React 18.2.0 + TypeScript 4.9.5
- ✅ TanStack React Query 5.8.4（設定済み、未使用）
- ✅ React Hook Form 7.43.0 + Zod 3.22.4
- ✅ Tailwind CSS 3.3.5
- ✅ Axios 1.6.2
- ✅ Lucide React 0.294.0

### 追加が必要な依存関係

**バックエンド**
- ❌ `python-statemachine` (v2.5.0+) - FSM実装
- ❌ `tenacity` (v8.x) - リトライロジック

**フロントエンド**
- なし（既存依存関係で実装可能）

---

## 付録B: 既存実装の詳細統計

### バックエンド実装統計
- **API endpoints**: 7個（問い合わせ3、システム4）
- **Database models**: 3個（InquiryModel, StoryModel, StoryTemplateModel）
- **Pydantic schemas**: 複数（Request/Response定義）
- **Tests**: 14+テストケース（test_inquiry_api.py: 236行）
- **Enum classes**: 5個（InquiryStatus, StoryStatus, Priority, StoryCategory, StoryPattern）

### フロントエンド実装統計
- **Components**: 3個（Layout, InquiryForm, 3ページ）
- **Services**: 2個（apiClient, inquiryService）
- **Custom hooks**: 1個（useDarkMode）
- **Type definitions**: 42ファイル
- **Lines of code**: InquiryForm 349行

### データベース統計
- **Tables**: 3個（inquiries, stories, story_templates）
- **Migrations**: 1個（initial_schema_for_storyboard.py）
- **Foreign keys**: 1個（stories.inquiry_id → inquiries.id）
- **Indexes**: 自動生成（Primary Key）

---

## 付録C: アーキテクチャパターン評価

| オプション | 説明 | 強み | リスク / 制約 | 備考 |
|-----------|------|------|--------------|------|
| **レイヤードアーキテクチャ（既存）** | API層 → サービス層 → リポジトリ層 → モデル層 | 既存システムと一貫、チーム習熟度高い | サービス層が未実装で新規作成必要 | 推奨：既存パターン踏襲 |
| **ヘキサゴナル（ポート＆アダプター）** | ドメイン中心、外部依存を抽象化 | AI統合の分離が明確、テスト容易 | 実装コスト高、既存との整合性課題 | AI統合部分のみ適用検討 |
| **イベント駆動** | ストーリー生成をイベントで非同期処理 | スケーラビリティ高、疎結合 | 複雑性増大、デバッグ困難 | 将来拡張として保留 |

**選定パターン**: **レイヤードアーキテクチャ（サービス層追加）**

---

## 付録D: セキュリティ考慮事項

### 認証・認可（将来実装）
- 現在のユーザー認証: **未実装**（`user_id`はハードコード "user-001"）
- 将来実装:
  - JWT トークンベース認証（python-jose）
  - ロールベースアクセス制御（RBAC）
  - 承認・却下権限管理

### APIセキュリティ
- ✅ CORS設定（既存）
- ✅ 入力値バリデーション（Pydantic）
- ✅ SQLインジェクション対策（SQLAlchemy ORM）
- ❌ レート制限（未実装）
- ❌ APIキー管理（OPENAI_API_KEY環境変数のみ、将来的にシークレット管理サービス検討）

### データ保護
- ✅ 環境変数管理（`.env`、`.gitignore`登録）
- ✅ PostgreSQLパスワード保護
- ❌ データ暗号化（未実装、将来検討）

---

**分析完了日**: 2025年12月26日
**次回更新**: 設計フェーズ完了時

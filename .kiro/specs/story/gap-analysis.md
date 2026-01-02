# ストーリー管理機能 ギャップ分析

## 分析サマリー

**スコープ**: 問い合わせからAI生成ストーリーを作成し、レビュー・編集・承認するCRUDワークフロー
**依存関係**: Inquiry機能（完全実装済み）との緊密な統合が必要
**主な課題**: AI API統合（OpenAI/Gemini）、新規Storyエンティティ、既存パターンとの整合性維持

### 重要な発見

- ✅ **Inquiryパターンの再利用性**: モデル、サービス層、APIルーター、フロントエンドコンポーネントの既存パターンが高度に成熟しており、ストーリー機能に適用可能
- ⚠️ **AI統合は新規領域**: OpenAI APIクライアント実装とエラーハンドリング（リトライ、レート制限）が未経験領域
- ✅ **データモデルの類似性**: Story↔Inquiryは類似構造（ステータス、メタデータ、ワークフロー）のため、既存コードを参考に実装可能
- 🔍 **要調査項目**: AI APIの抽象化戦略（複数プロバイダー対応）、プロンプトエンジニアリング手法

---

## 1. 現状調査

### 1.1 既存アセット（Inquiry機能）

#### バックエンド（Python/FastAPI）

**データモデル層** (`api/models/database/`)
- `base.py` - 共通ベースモデル（id、created_at、updated_at、BigInteger ID）
- `inquiry.py` - InquiryModel（ステータスEnum、JSON metadata、CHECK制約）
  - パターン: Enum型ステータス、JSONメタデータ、参照整合性制約
  - 再利用可能: ベースモデル、メタデータパターン、ステータス管理

**スキーマ層** (`api/models/schemas/`)
- `inquiry.py` - Pydanticスキーマ（CreateInquiryRequest、UpdateInquiryRequest、InquiryResponse）
  - パターン: Fieldバリデーション、日本語エラーメッセージ、ISO datetime、model_config
  - 再利用可能: バリデーションパターン、エラーハンドリング構造

**列挙型** (`api/models/enums/`)
- `inquiry_status.py` - InquiryStatus（Enum、received/processing/task_working/completed/rejected/needs_clarification）
  - パターン: Enumクラス定義、SQLAlchemy統合
  - Story用に新規: StoryStatus（pending_review/approved/rejected）、Priority、StoryCategory

**サービス層** (`api/services/`)
- `inquiry_validator.py` - バリデーションロジック（97%カバレッジ）
- `inquiry_repository.py` - CRUD操作（90%カバレッジ、ページネーション、フィルタリング、ソート）
- `inquiry_query_service.py` - クエリサービス（100%カバレッジ）
- `inquiry_workflow_service.py` - ワークフロー管理（89%カバレッジ、approve/reject、ステータス遷移）
  - パターン: レイヤー分離（Validator/Repository/QueryService/WorkflowService）、依存性注入
  - 再利用可能: 全パターン（StoryValidator、StoryRepository、StoryWorkflowService）

**API層** (`api/routers/`)
- `inquiry.py` - RESTfulエンドポイント（CRUD + approve/reject）
  - パターン: FastAPI router、ページネーション、エラーハンドリング、HTTPステータスコード
  - 再利用可能: ルーティング構造、レスポンスモデル、エラーレスポンス

**テスト** (`api/tests/`)
- 189テスト、高カバレッジ（pytest、hypothesis PBT、httpx TestClient）
  - パターン: conftest.py、フィクスチャ、モック、E2Eテスト
  - 再利用可能: テスト構造、フィクスチャパターン

#### フロントエンド（React/TypeScript）

**型定義** (`web/src/types/`)
- `inquiry.ts` - InquiryStatus、InquiryResponse、CreateInquiryRequest等
  - パターン: バックエンドスキーマとの型整合性
  - Story用に新規: StoryResponse、CreateStoryRequest、StoryStatus等

**APIクライアント** (`web/src/services/`)
- `inquiryApi.ts` - Axios統合、エラーインターセプター（86.11%カバレッジ）
  - パターン: Axiosインスタンス、エラーハンドリング、型安全API
  - 再利用可能: 全パターン（storyApi.ts作成）

**コンポーネント** (`web/src/components/`)
- `InquiryForm.tsx` - React Hook Form + Zod（100% statements）
- `InquiryList.tsx` - TanStack Query、ページネーション、フィルタ（84.21% statements）
- `InquiryDetail.tsx` - 詳細表示、編集、承認/却下（94.64% statements）
  - パターン: React Hook Form + Zod、TanStack Query、楽観的更新、react-hot-toast
  - 再利用可能: 全パターン（StoryForm、StoryList、StoryDetail作成）

**テスト** (`web/src/`)
- 54テスト、91.02%カバレッジ（Jest + React Testing Library）
  - パターン: Axiosモック、ユーザーイベントテスト、非同期処理テスト
  - 再利用可能: 全パターン

### 1.2 統合面

**データベース**
- PostgreSQL 15 + SQLAlchemy 2.0.23 + Alembic 1.12.1
- 外部キー制約、トランザクション管理、マイグレーション管理
- パターン: Alembic revision、CHECK制約、インデックス設定

**開発環境**
- Docker Compose（db、api、web）
- Makefile（46+コマンド）
- .env環境変数管理

**コード品質**
- バックエンド: black + flake8 + mypy + bandit + pytest
- フロントエンド: prettier + eslint + jest + @testing-library/react

### 1.3 欠落・未実装

**バックエンド**
- ❌ Storyモデル（`models/database/story.py`）
- ❌ Storyスキーマ（`models/schemas/story.py`）
- ❌ StoryStatus、Priority、StoryCategoryのEnum定義
- ❌ Storyサービス層（StoryValidator、StoryRepository、StoryQueryService、StoryWorkflowService）
- ❌ StoryルーターとAPIエンドポイント（`routers/story.py`）
- ❌ **AI API統合**（OpenAI/Geminiクライアント、プロンプト管理、エラーハンドリング）
- ❌ Alembicマイグレーション（storiesテーブル作成）

**フロントエンド**
- ❌ Story型定義（`types/story.ts`）
- ❌ Story APIクライアント（`services/storyApi.ts`）
- ❌ Storyコンポーネント（StoryForm、StoryList、StoryDetail）
- ❌ ストーリー生成トリガーボタン（InquiryDetailへの追加）
- ❌ Tailwind CSS設定（部分的）
- ❌ React Router設定（ページルーティング）

---

## 2. 要件実現性分析

### 2.1 技術要件マッピング

#### 要件1: AI変換（10個の受入基準）

| 受入基準 | 技術要件 | 既存アセット | ギャップ | 複雑度 |
|---------|---------|------------|---------|--------|
| 1.1 問い合わせID指定 | APIエンドポイント（POST /api/stories/generate + inquiry_id） | InquiryRouter参考 | 新規エンドポイント | S |
| 1.2 ステータス検証（task_working） | Inquiryステータス確認 | InquiryWorkflowService参考 | Story生成サービス | S |
| 1.3 ステータス変更（processing） | Inquiry更新 | InquiryRepository.update | 既存再利用 | S |
| 1.4 AI APIでストーリー生成 | **OpenAI/Gemini API統合** | ❌ **未経験** | **AI APIクライアント** | M-L |
| 1.5 ストーリーステータス設定（pending_review） | Storyレコード作成 | InquiryRepository参考 | StoryRepository | S |
| 1.6 inquiry_id関連付け | 外部キー | InquiryModel参考 | 外部キー制約 | S |
| 1.7 リトライ処理 | エラーハンドリング | ❌ 未経験（リトライロジック） | **リトライ実装（tenacity等）** | M |
| 1.8 構造検証（必須フィールド） | Pydanticバリデーション | InquiryValidator参考 | StoryValidator | S |
| 1.9 タイトル500文字検証 | Fieldバリデーション | InquirySchema参考 | Pydantic Field | S |
| 1.10 複数AIプロバイダー対応 | **AI API抽象化** | ❌ **未経験** | **AIサービス抽象レイヤー** | M-L |

**ギャップ**: AI API統合（OpenAI/Gemini）、リトライ処理、プロバイダー抽象化
**制約**: OpenAI API 1.3.7は依存関係に存在
**不明点**: 🔍 AI APIレート制限、プロンプトテンプレート管理、生成品質保証手法

#### 要件2: レビューと編集（17個の受入基準）

| 受入基準 | 技術要件 | 既存アセット | ギャップ | 複雑度 |
|---------|---------|------------|---------|--------|
| 2.1 ストーリー一覧API | GET /api/stories | InquiryRouter参考 | StoryRouter | S |
| 2.2 ページネーション | limit/offset | InquiryQueryService | StoryQueryService | S |
| 2.3 フィルタリング（ステータス、優先度、inquiry_id） | SQLAlchemyフィルタ | InquiryQueryService | StoryQueryService | S |
| 2.4 ソート（作成日時、更新日時、優先度、推定工数、担当者、期限） | SQLAlchemyソート | InquiryQueryService | StoryQueryService | S |
| 2.5-2.10 詳細表示・編集・更新 | CRUD操作 | InquiryRepository | StoryRepository | S |
| 2.11-2.14 手動ストーリー作成 | POST /api/stories + inquiry_id=NULL | InquiryRouter参考 | StoryRouter | S |
| 2.15-2.17 削除（確認ダイアログ含む） | DELETE /api/stories/{id} + UI確認 | Inquiry削除未実装 | StoryRepository + UI | S |

**ギャップ**: Storyサービス層全体（Inquiryパターンをほぼ複製）
**制約**: なし
**不明点**: なし（Inquiryパターンで解決可能）

#### 要件3: 承認ワークフロー（11個の受入基準）

| 受入基準 | 技術要件 | 既存アセット | ギャップ | 複雑度 |
|---------|---------|------------|---------|--------|
| 3.1-3.9 承認・却下処理 | POST /api/stories/{id}/approve, POST /api/stories/{id}/reject | InquiryWorkflowService | StoryWorkflowService | S |
| 3.10-3.11 一括承認 | POST /api/stories/batch/approve | ❌ Inquiryにも未実装 | **一括処理ロジック** | M |

**ギャップ**: StoryWorkflowService（Inquiryパターン複製）、一括処理（新規）
**制約**: なし
**不明点**: 一括処理のトランザクション戦略（全成功/部分成功/ロールバック）

#### 要件4: データモデル（13個の受入基準）

| 受入基準 | 技術要件 | 既存アセット | ギャップ | 複雑度 |
|---------|---------|------------|---------|--------|
| 4.1-4.13 Storyモデル | SQLAlchemyモデル、Alembicマイグレーション | InquiryModel | StoryModel + マイグレーション | S |

**ギャップ**: StoryModel、StoryStatus/Priority/StoryCategoryのEnum、Alembicマイグレーション
**制約**: inquiry_idはNULL許可（手動作成ストーリー用）
**不明点**: なし

#### 要件5: Web UI（14個の受入基準）

| 受入基準 | 技術要件 | 既存アセット | ギャップ | 複雑度 |
|---------|---------|------------|---------|--------|
| 5.1-5.14 Story UI | StoryForm、StoryList、StoryDetail | InquiryForm/List/Detail | Storyコンポーネント群 | S-M |
| 5.3 ストーリー生成ボタン（InquiryDetailページ） | UI統合 | InquiryDetail | ボタン追加 + API呼び出し | S |

**ギャップ**: Storyコンポーネント全体（Inquiryパターン複製）、Tailwind CSS完全適用、React Router
**制約**: なし
**不明点**: なし

### 2.2 非機能要件

**セキュリティ**
- API認証（将来実装：python-jose + passlib）
- 入力値サニタイゼーション（Pydanticバリデーション）
- SQLインジェクション対策（SQLAlchemy ORM）

**パフォーマンス**
- ストーリー一覧: < 1秒（要件）
- ストーリー変換: < 30秒（通常 < 10秒）（要件）
- AI API呼び出しのタイムアウト設定が必要

**スケーラビリティ**
- ストーリー数: 10,000件（初期）→ 100,000件（目標）
- AI API呼び出し: 1,000回/日（初期）→ 10,000回/日（目標）
- PostgreSQLインデックス最適化（inquiry_id、created_at、updated_at、status）

**信頼性**
- AI APIエラー時のリトライ（最大3回、指数バックオフ）
- トランザクション管理（SQLAlchemyセッション）
- データ整合性（外部キー制約、CHECK制約）

---

## 3. 実装アプローチオプション

### オプションA: Inquiryパターンを拡張（Storyモジュール追加）

**戦略**: Inquiryと同じアーキテクチャパターンでStoryモジュールを新規作成

**拡張するファイル**:
- ❌ なし（既存ファイルは拡張せず、新規作成のみ）

**新規作成するファイル**:

**バックエンド**:
- `models/database/story.py` - StoryModel
- `models/schemas/story.py` - CreateStoryRequest、UpdateStoryRequest、StoryResponse
- `models/enums/story_status.py` - StoryStatus（pending_review/approved/rejected）
- `models/enums/priority.py` - Priority（low/medium/high/urgent）
- `models/enums/story_category.py` - StoryCategory（development/testing/documentation等）
- `services/story_validator.py` - StoryValidator
- `services/story_repository.py` - StoryRepository
- `services/story_query_service.py` - StoryQueryService
- `services/story_workflow_service.py` - StoryWorkflowService
- `services/ai_service.py` - **AI API統合**（OpenAI/Gemini抽象化）
- `routers/story.py` - StoryRouter
- `tests/test_story_*.py` - Storyテストスイート
- `alembic/versions/xxxx_create_stories_table.py` - マイグレーション

**フロントエンド**:
- `types/story.ts` - Story型定義
- `services/storyApi.ts` - Story APIクライアント
- `components/StoryForm.tsx` - ストーリー作成フォーム
- `components/StoryList.tsx` - ストーリー一覧
- `components/StoryDetail.tsx` - ストーリー詳細・編集
- `components/InquiryDetail.tsx` - **ストーリー生成ボタン追加**（既存ファイル拡張）
- `components/Story*.test.tsx` - Storyテストスイート

**統合ポイント**:
1. StoryModel.inquiry_id → InquiryModel.id（外部キー）
2. InquiryDetailページにストーリー生成ボタン追加
3. AI生成サービス（story_ai_service.py）→ InquiryRepository経由でInquiry取得
4. StoryWorkflowService → InquiryRepository経由でInquiryステータス更新（task_working → processing → completed）

**トレードオフ**:
- ✅ **Inquiryパターン完全再利用**: 既存の成熟したアーキテクチャをそのまま適用
- ✅ **高速開発**: Inquiryコードをテンプレートとして複製・修正
- ✅ **テスト容易性**: Inquiryテストパターンをそのまま適用
- ✅ **保守性**: 同一構造のため、開発者の認知負荷が低い
- ❌ **コード重複**: Inquiry↔Story間で類似コードが増加（ただし、パターン統一により許容範囲）
- ❌ **AI統合の新規性**: AI APIクライアント実装は新規領域（リスク: M）

**複雑度**: M（AI統合部分のみM、その他はS）
**リスク**: M（AI API統合、リトライ処理、プロバイダー抽象化が未経験）

---

### オプションB: 共通基盤を抽象化（Generic CRUD Service）

**戦略**: InquiryとStoryの共通パターンを汎用サービスクラスに抽出

**作成する共通基盤**:
- `services/base_repository.py` - Generic CRUD Repository（Type Parameter）
- `services/base_workflow_service.py` - Generic Workflow Service
- `services/base_query_service.py` - Generic Query Service

**変更が必要な既存ファイル**:
- `services/inquiry_repository.py` - BaseRepositoryを継承
- `services/inquiry_workflow_service.py` - BaseWorkflowServiceを継承
- `services/inquiry_query_service.py` - BaseQueryServiceを継承

**新規作成するファイル**:
- （オプションAと同じStoryモジュール群）
- （ただし、BaseRepositoryを継承するため、コード量は削減）

**統合ポイント**:
- オプションAと同じ

**トレードオフ**:
- ✅ **コード重複削減**: 共通ロジックを1箇所に集約
- ✅ **長期保守性向上**: 将来の追加エンティティ（Template等）にも適用可能
- ❌ **初期開発コスト増**: 共通基盤設計・実装・テストに追加時間
- ❌ **抽象化の複雑性**: Generic型パラメータ、継承構造が複雑化
- ❌ **既存コードへの影響**: Inquiryサービスのリファクタリング必要（リグレッションリスク）

**複雑度**: L（共通基盤設計 + AI統合）
**リスク**: H（既存コードへの影響、抽象化の複雑性）

---

### オプションC: 段階的実装（Minimal MVP → Full Feature）

**戦略**: Phase 1でMinimal Viable Product、Phase 2で完全機能実装

**Phase 1: Minimal MVP（1週間）**
- Storyモデル（基本フィールドのみ）
- StoryRepository（CRUD操作のみ）
- StoryRouter（基本CRUD APIのみ）
- StoryForm、StoryList、StoryDetail（基本UIのみ）
- **AI統合スタブ**（OpenAI APIモック、後でプロダクション実装）

**Phase 2: Full Feature（1週間）**
- AI統合（OpenAI/Gemini）
- ストーリー生成ワークフロー
- 承認・却下ワークフロー
- 一括処理
- フィルタリング・ソート機能強化

**Phase 3: Polish & Optimization（数日）**
- Tailwind CSS完全適用
- React Router統合
- E2Eテスト
- パフォーマンス最適化

**トレードオフ**:
- ✅ **リスク分散**: AI統合を後回しにし、まずCRUD基盤を確立
- ✅ **早期フィードバック**: Phase 1で基本機能を早期リリース
- ✅ **段階的学習**: AI統合の複雑性を後フェーズで集中対応
- ❌ **複数フェーズ管理**: マイグレーション、テスト、デプロイが複数回
- ❌ **モックの廃棄**: Phase 1のAIスタブがPhase 2で不要に

**複雑度**: M（段階的実装のため、各フェーズは単純）
**リスク**: M（フェーズ管理の複雑性）

---

## 4. 未解決・要調査項目

### 4.1 AI API統合

**調査項目**:
1. **OpenAI API 1.3.7の使用方法**
   - プロンプトエンジニアリング手法（ストーリー生成に最適なプロンプト）
   - レート制限とタイムアウト設定
   - エラーハンドリングとリトライ戦略（tenacity、backoff等のライブラリ）

2. **Google Gemini API統合**
   - Google AI Python SDKの使用方法
   - OpenAI APIとの抽象化戦略（共通インターフェース設計）
   - 環境変数での切り替え（AI_PROVIDER=openai/gemini）

3. **生成品質保証**
   - 生成されたストーリーの構造検証（必須フィールド、形式チェック）
   - 不適切コンテンツフィルタリング
   - 生成失敗時のフォールバック戦略

**推奨調査方法**:
- OpenAI Cookbook、Gemini Docsを参照
- プロンプトテンプレートの設計（Jinja2等）
- AI生成結果のPost-processing戦略

### 4.2 一括承認機能

**調査項目**:
1. **トランザクション戦略**
   - 全成功（all-or-nothing）vs 部分成功（best-effort）
   - エラー発生時のロールバック範囲
   - 一括処理のレスポンス形式（成功/失敗の詳細）

2. **パフォーマンス**
   - 大量ストーリー一括処理時のデータベース負荷
   - バルクUPDATE vs ループUPDATEの性能比較

**推奨調査方法**:
- SQLAlchemy bulk_update_mappings()の使用
- プロダクト要件を確認（全成功必須 or 部分成功許容）

### 4.3 React Router統合

**調査項目**:
1. **ルーティング設計**
   - `/inquiries` - InquiryList
   - `/inquiries/:id` - InquiryDetail
   - `/stories` - StoryList
   - `/stories/:id` - StoryDetail

2. **ナビゲーション**
   - InquiryDetail → StoryList（生成後の遷移）
   - StoryDetail ← StoryList（詳細から一覧へ戻る）

**推奨調査方法**:
- React Router DOM 6.18.0のドキュメント参照
- Inquiryページにルーティング追加後、Storyページを追加

---

## 5. 実装複雑度・リスク評価

### 5.1 全体評価

**実装工数**: M-L（2-3週間）
- バックエンド: M（1-1.5週間）- AI統合がM、その他はS
- フロントエンド: M（1-1.5週間）- Inquiryパターン複製
- テスト: S（数日）- 既存パターン適用
- 統合・E2E: S（数日）

**リスク**: M
- **High**: AI API統合（未経験、レート制限、エラーハンドリング）
- **Medium**: 一括処理（トランザクション戦略）、プロバイダー抽象化
- **Low**: その他（Inquiryパターン再利用）

**複雑度の理由**:
- **AI統合がM**: OpenAI/Gemini APIクライアント実装、プロンプト管理、リトライ処理が新規領域
- **その他はS**: Inquiryパターンがほぼそのまま適用可能（モデル、サービス、API、UI全て）

### 5.2 フェーズ別リスク

**Phase 1（基盤構築）**: Low-Medium
- Storyモデル、Repository、Router、UI基盤
- Inquiryパターンをテンプレートとして使用可能

**Phase 2（AI統合）**: Medium-High
- OpenAI/Gemini API統合
- プロンプトエンジニアリング
- エラーハンドリング・リトライ処理

**Phase 3（完成・最適化）**: Low
- 一括処理、フィルタリング強化、UI Polish

---

## 6. 設計フェーズへの推奨事項

### 6.1 推奨アプローチ

**オプションA（Inquiryパターン拡張）を推奨**

**理由**:
1. **既存パターンの成熟度**: Inquiryパターンは189テスト、高カバレッジで実証済み
2. **開発速度**: Inquiryコードをテンプレートとして複製・修正可能（高速開発）
3. **リスク最小化**: 既存コードへの影響なし（新規モジュール作成のみ）
4. **保守性**: 同一構造のため、開発者の認知負荷が低い

**オプションBは将来検討**: 3つ目以降のエンティティ（Template等）追加時に共通基盤を抽出

**オプションCの要素も採用**: AI統合は段階的に実装（スタブ → プロダクション）

### 6.2 設計フェーズで決定すべき事項

**AI統合**:
1. プロンプトテンプレート設計（ストーリー生成の品質を左右）
2. OpenAI/Gemini抽象化戦略（環境変数 vs ファクトリーパターン）
3. リトライ戦略詳細（tenacityライブラリ使用、指数バックオフ設定）
4. タイムアウト設定（30秒、60秒）

**一括処理**:
1. トランザクション戦略（all-or-nothing vs best-effort）
2. エラーレスポンス形式（成功/失敗の詳細）

**データモデル**:
1. StoryModel詳細フィールド設計（inquiry_id NULL制約、JSON metadata構造）
2. Alembicマイグレーション戦略

**UI/UX**:
1. ストーリー生成トリガーUIデザイン（InquiryDetailページのボタン配置）
2. 生成中のローディングUX（進捗表示、タイムアウト表示）
3. React Router統合設計

### 6.3 技術調査項目（設計前に実施）

**必須調査**:
1. OpenAI API 1.3.7 + Gemini APIの使用方法とプロンプトエンジニアリング
2. tenacityライブラリ（リトライ処理）の使用方法
3. React Router DOM 6.18.0のルーティング設計

**推奨調査**:
1. プロンプトテンプレート管理手法（Jinja2、環境変数、設定ファイル）
2. AI生成結果のPost-processing戦略

---

## 次のステップ

**設計フェーズへ進む**: `/kiro:spec-design story`

設計フェーズでは以下を実施:
1. Storyモデル詳細設計（フィールド、外部キー、制約）
2. AI統合アーキテクチャ設計（OpenAI/Gemini抽象化、プロンプト管理）
3. サービス層詳細設計（StoryRepository、StoryWorkflowService、AI Service）
4. API設計（エンドポイント、リクエスト/レスポンスモデル）
5. UI設計（コンポーネント構造、React Router統合）
6. テスト戦略（AI統合のモック戦略、E2Eテスト）

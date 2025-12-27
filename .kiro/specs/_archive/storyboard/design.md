# ストーリーボード機能 技術設計書

## 概要

ストーリーボード機能は、報告者からの自然言語問い合わせを受け付け、AIを活用して構造化されたユーザーストーリーへ変換するシステムである。本機能は問い合わせの作成・管理、AI駆動のストーリー生成、人間によるレビュー・承認という3つの主要フローを提供する。

### 設計目標

- **型安全性**: すべてのインターフェースで明示的な型定義を使用し、`any`型を排除する
- **疎結合**: コンポーネント間の依存関係を最小化し、明確な境界を設定する
- **拡張性**: 将来的な外部システム連携やAIモデル変更に対応できる設計
- **可観測性**: すべての重要な操作でログ記録とエラー追跡を実装する
- **言語対応**: 日本語を主言語として設計し、国際化を考慮する

### 非目標

- リアルタイムコラボレーション機能（将来検討）
- 複数AIプロバイダーの同時使用（Phase 1では単一プロバイダー）
- 問い合わせの自動分類（初期バージョンではAI生成時のみ分類）
- モバイルアプリケーション（WebUIのみ）

## 要件トレーサビリティ

| 要件ID | 要件概要 | 主要コンポーネント | 主要インターフェース | フロー |
|--------|----------|-------------------|---------------------|--------|
| 1.1-1.6 | 問い合わせの作成 | InquiryRepository, InquiryValidator | createInquiry, validateInquiry | 問い合わせ作成フロー |
| 2.1-2.9 | 問い合わせの一覧・検索・編集 | InquiryRepository, InquiryQueryService | listInquiries, getInquiry, updateInquiry | 問い合わせ管理フロー |
| 3.1-3.5 | 問い合わせの承認・却下 | InquiryWorkflowService | approveInquiry, rejectInquiry | ステータス変更フロー |
| 4.1-4.8 | ストーリー生成 | AIStoryGenerator, StoryRepository | generateStory, validateStoryStructure | AI変換フロー |
| 5.1-5.7 | ストーリーの管理・レビュー | StoryRepository, StoryWorkflowService | listStories, updateStory, approveStory | ストーリーレビューフロー |
| 6.1-6.7 | ユーザーインターフェース | InquiryForm, InquiryList, StoryBoard | すべてのUI関連インターフェース | 全UIフロー |

## アーキテクチャ概要

### システムアーキテクチャ図

```mermaid
graph TB
    subgraph クライアント層
        WebUI[Web UI]
    end

    subgraph API層
        InquiryAPI[Inquiry API]
        StoryAPI[Story API]
        HealthAPI[Health API]
    end

    subgraph サービス層
        InquiryService[Inquiry Service]
        StoryService[Story Service]
        AIService[AI Service]
        ValidationService[Validation Service]
        WorkflowService[Workflow Service]
    end

    subgraph データアクセス層
        InquiryRepo[Inquiry Repository]
        StoryRepo[Story Repository]
    end

    subgraph 外部システム
        OpenAI[OpenAI API]
        Database[(PostgreSQL)]
    end

    WebUI --> InquiryAPI
    WebUI --> StoryAPI

    InquiryAPI --> InquiryService
    StoryAPI --> StoryService

    InquiryService --> InquiryRepo
    InquiryService --> ValidationService
    InquiryService --> WorkflowService

    StoryService --> StoryRepo
    StoryService --> AIService
    StoryService --> ValidationService
    StoryService --> WorkflowService

    AIService --> OpenAI

    InquiryRepo --> Database
    StoryRepo --> Database

    InquiryAPI --> HealthAPI
    StoryAPI --> HealthAPI
```

### レイヤー責務

- **クライアント層**: ユーザー入力の受付、データ表示、バリデーションフィードバック
- **API層**: HTTPリクエスト処理、認証・認可、リクエスト/レスポンスのシリアライゼーション
- **サービス層**: ビジネスロジック実装、ワークフロー制御、外部システム統合
- **データアクセス層**: データベースCRUD操作、クエリ最適化、トランザクション管理
- **外部システム**: AI処理、データ永続化

## 技術スタック

### バックエンド

| レイヤー | 技術 | バージョン | 役割 |
|---------|------|-----------|------|
| APIフレームワーク | FastAPI | 0.104.1 | RESTful API提供、OpenAPI自動生成 |
| ASGIサーバー | Uvicorn | 0.24.0 | 非同期リクエスト処理 |
| ORM | SQLAlchemy | 2.0.23 | データベース抽象化レイヤー |
| マイグレーション | Alembic | 1.12.1 | スキーマバージョン管理 |
| バリデーション | Pydantic | 2.5.0 | データ検証・シリアライゼーション |
| AI統合 | OpenAI | 1.3.7 | ストーリー生成エンジン |
| テスト | pytest | 7.4.3 | ユニット・統合テスト |

### フロントエンド

| レイヤー | 技術 | バージョン | 役割 |
|---------|------|-----------|------|
| UIフレームワーク | React | 18.2.0 | コンポーネントベースUI構築 |
| 型システム | TypeScript | 4.9.5 | 静的型チェック |
| 状態管理 | TanStack Query | 5.8.4 | サーバー状態管理・キャッシング |
| フォーム | React Hook Form | 7.43.0 | フォーム状態管理 |
| バリデーション | Zod | 3.22.4 | スキーマバリデーション |
| HTTP | Axios | 1.6.2 | API通信 |
| スタイリング | Tailwind CSS | 3.3.5 | ユーティリティファーストCSS |

### データ層

| レイヤー | 技術 | バージョン | 役割 |
|---------|------|-----------|------|
| データベース | PostgreSQL | 15 | リレーショナルデータ永続化 |
| コンテナ | Docker | latest | 開発環境統一 |

### 新規依存関係

本機能では既存のGhost Squadスタックをそのまま使用し、新規依存関係は追加しない。

## システムフロー

### 問い合わせ作成フロー

```mermaid
sequenceDiagram
    participant Reporter as 報告者
    participant UI as Web UI
    participant API as Inquiry API
    participant Validator as Validation Service
    participant Workflow as Workflow Service
    participant Repo as Inquiry Repository
    participant DB as Database

    Reporter->>UI: 問い合わせ入力
    UI->>UI: クライアント側バリデーション
    UI->>API: POST /api/inquiries
    API->>Validator: validateInquiry

    alt バリデーションエラー
        Validator-->>API: ValidationError
        API-->>UI: 400 Bad Request
        UI-->>Reporter: エラー表示
    else バリデーション成功
        Validator-->>API: Valid
        API->>Workflow: initializeInquiryWorkflow
        Workflow->>Repo: createInquiry
        Repo->>DB: INSERT inquiry
        DB-->>Repo: inquiry_id
        Repo-->>Workflow: InquiryEntity
        Workflow-->>API: InquiryResponse
        API-->>UI: 201 Created
        UI-->>Reporter: 成功メッセージ
    end
```

### AI変換フロー

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant UI as Web UI
    participant API as Story API
    participant Workflow as Workflow Service
    participant AI as AI Service
    participant OpenAI as OpenAI API
    participant Repo as Story Repository
    participant InqRepo as Inquiry Repository
    participant DB as Database

    User->>UI: ストーリー生成要求
    UI->>API: POST /api/stories/generate
    API->>Workflow: initiateStoryGeneration

    Workflow->>InqRepo: updateStatus(processing)
    InqRepo->>DB: UPDATE inquiry

    Workflow->>AI: generateStory
    AI->>OpenAI: API call with prompt

    alt AI処理成功
        OpenAI-->>AI: Generated content
        AI->>AI: validateStoryStructure

        alt 構造検証成功
            AI-->>Workflow: ValidStory
            Workflow->>Repo: createStory
            Repo->>DB: INSERT story
            Workflow->>InqRepo: updateStatus(task_working)
            InqRepo->>DB: UPDATE inquiry
            Workflow-->>API: StoryResponse
            API-->>UI: 201 Created
            UI-->>User: ストーリー表示
        else 構造検証失敗
            AI-->>Workflow: StructureError
            Workflow->>InqRepo: updateStatus(failed)
            Workflow-->>API: 422 Unprocessable Entity
            API-->>UI: エラー応答
            UI-->>User: エラー表示
        end
    else AI処理失敗
        OpenAI-->>AI: API Error
        AI-->>Workflow: AIError
        Workflow->>InqRepo: updateStatus(failed)
        InqRepo->>DB: UPDATE inquiry
        Workflow-->>API: 503 Service Unavailable
        API-->>UI: エラー応答
        UI-->>User: エラー表示
    end
```

### ストーリーレビューフロー

```mermaid
stateDiagram-v2
    [*] --> pending_review: ストーリー生成

    pending_review --> approved: ユーザー承認
    pending_review --> rejected: ユーザー拒否
    pending_review --> pending_review: ユーザー編集

    approved --> exported: 外部連携実行
    approved --> approved: メタデータ更新

    rejected --> [*]: 終了
    exported --> [*]: 終了

    note right of pending_review
        編集可能
        タイトル、説明、受入基準の変更
        優先度、カテゴリの調整
    end note

    note right of approved
        読み取り専用
        エクスポート待機
    end note
```

## コンポーネント設計

### コンポーネント概要

| コンポーネント | ドメイン | 責務 | 要件カバレッジ | 依存関係 |
|--------------|---------|------|--------------|---------|
| InquiryRepository | データアクセス | 問い合わせCRUD | 1.1-1.6, 2.1-2.9 | Database |
| StoryRepository | データアクセス | ストーリーCRUD | 4.1-4.8, 5.1-5.7 | Database |
| InquiryValidator | サービス | 入力検証 | 1.4, 2.8 | - |
| AIStoryGenerator | サービス | AI生成 | 4.1-4.8 | OpenAI API |
| WorkflowService | サービス | ワークフロー制御 | 3.1-3.5, 4.1-4.8, 5.1-5.7 | InquiryRepo, StoryRepo |
| InquiryQueryService | サービス | 検索・ページネーション | 2.1-2.4 | InquiryRepo |
| InquiryAPI | API | 問い合わせエンドポイント | 1.1-3.5 | InquiryService |
| StoryAPI | API | ストーリーエンドポイント | 4.1-5.7 | StoryService |
| InquiryForm | UI | 問い合わせ入力 | 6.1-6.3 | InquiryAPI |
| InquiryList | UI | 問い合わせ一覧 | 6.4-6.5 | InquiryAPI |
| StoryBoard | UI | ストーリー管理 | 6.6-6.7 | StoryAPI |

### 依存関係詳細

| 依存先 | 方向 | 重要度 | 説明 |
|--------|------|--------|------|
| PostgreSQL | External | P0 | データ永続化、全機能がブロックされる |
| OpenAI API | External | P0 | ストーリー生成、AI機能がブロックされる |
| SQLAlchemy | Inbound | P0 | ORM、データアクセス層で必須 |
| FastAPI | Inbound | P0 | APIフレームワーク、全エンドポイントで必須 |
| React | Inbound | P0 | UIフレームワーク、全画面で必須 |
| Pydantic | Inbound | P1 | バリデーション、代替手段あり |
| TanStack Query | Inbound | P1 | 状態管理、代替手段あり |

## データモデル

### ドメインモデル

```mermaid
erDiagram
    INQUIRY ||--o{ STORY : generates

    INQUIRY {
        bigint id PK
        string user_id
        text content
        string source_system
        timestamp timestamp
        enum status
        timestamp created_at
        timestamp updated_at
    }

    STORY {
        bigint id PK
        bigint inquiry_id FK
        string title
        text description
        text acceptance_criteria
        enum category
        enum priority
        timestamp deadline
        string assignee_id
        enum status
        timestamp created_at
        timestamp updated_at
    }
```

#### エンティティ定義

**Inquiry（問い合わせ）**

- **責務**: 報告者からの自然言語問い合わせを表現する
- **集約ルート**: Inquiry自身
- **不変条件**:
  - `content`は空文字列を許可しない
  - `status`はInquiryStatusの有効な値のみ
  - `source_system`は送信元システムを識別する文字列（例: "manual", "email", "chat"）

**Story（ストーリー）**

- **責務**: 構造化されたユーザーストーリーを表現する
- **集約ルート**: Story自身（Inquiryへの参照を持つ）
- **不変条件**:
  - `inquiry_id`は有効なInquiryを参照する
  - `title`は500文字以内
  - `description`と`acceptance_criteria`は空文字列を許可しない

#### 列挙型定義

**InquiryStatus**

```typescript
type InquiryStatus =
  | 'received'              // 受付済み
  | 'processing'            // AI処理中
  | 'needs_clarification'   // 明確化要求
  | 'task_working'          // タスク作業中
  | 'completed'             // 完了
  | 'failed';               // 失敗
```

**StoryStatus**

```typescript
type StoryStatus =
  | 'pending_review'        // レビュー待ち
  | 'approved'              // 承認済み
  | 'rejected'              // 拒否
  | 'exported';             // エクスポート済み
```

**Priority**

```typescript
type Priority =
  | 'low'                   // 低
  | 'medium'                // 中
  | 'high'                  // 高
  | 'urgent';               // 緊急
```

**StoryCategory**

```typescript
type StoryCategory =
  | 'development'           // 開発
  | 'testing'               // テスト
  | 'documentation'         // ドキュメント
  | 'research'              // 調査
  | 'maintenance'           // メンテナンス
  | 'custom';               // カスタム
```

### 論理データモデル

#### インデックス戦略

```sql
-- 問い合わせテーブル
CREATE INDEX ix_inquiries_status ON inquiries(status);
CREATE INDEX ix_inquiries_user_id ON inquiries(user_id);
CREATE INDEX ix_inquiries_created_at ON inquiries(created_at DESC);
CREATE INDEX ix_inquiries_composite ON inquiries(status, created_at DESC);

-- ストーリーテーブル
CREATE INDEX ix_stories_inquiry_id ON stories(inquiry_id);
CREATE INDEX ix_stories_status ON stories(status);
CREATE INDEX ix_stories_priority ON stories(priority);
CREATE INDEX ix_stories_assignee_id ON stories(assignee_id);
CREATE INDEX ix_stories_deadline ON stories(deadline);
CREATE INDEX ix_stories_composite ON stories(status, priority, created_at DESC);

-- 全文検索用（将来）
CREATE INDEX ix_inquiries_content_gin ON inquiries USING gin(to_tsvector('japanese', content));
CREATE INDEX ix_stories_title_gin ON stories USING gin(to_tsvector('japanese', title));
```

#### データ整合性制約

```sql
-- 外部キー制約
ALTER TABLE stories
  ADD CONSTRAINT fk_stories_inquiry
  FOREIGN KEY (inquiry_id)
  REFERENCES inquiries(id)
  ON DELETE CASCADE;

-- チェック制約
ALTER TABLE inquiries
  ADD CONSTRAINT chk_inquiries_content_not_empty
  CHECK (length(trim(content)) > 0);

ALTER TABLE stories
  ADD CONSTRAINT chk_stories_title_length
  CHECK (length(title) <= 500);
```

### データ契約・統合

#### API レスポンス型

**InquiryResponse**

```typescript
interface InquiryResponse {
  id: number;
  user_id: string;
  content: string;
  source_system: string;
  timestamp: string;  // ISO 8601形式
  status: InquiryStatus;
  created_at: string;  // ISO 8601形式
  updated_at: string;  // ISO 8601形式
}
```

**StoryResponse**

```typescript
interface StoryResponse {
  id: number;
  inquiry_id: number;
  title: string;
  description: string;
  acceptance_criteria: string;
  category: StoryCategory;
  priority: Priority;
  deadline: string | null;  // ISO 8601形式
  assignee_id: string | null;
  status: StoryStatus;
  created_at: string;  // ISO 8601形式
  updated_at: string;  // ISO 8601形式
}
```

**PaginatedResponse**

```typescript
interface PaginatedResponse<T> {
  data: T[];
  meta: {
    page: number;
    limit: number;
    total: number;
    has_next: boolean;
  };
  timestamp: string;  // ISO 8601形式
}
```

#### API リクエスト型

**CreateInquiryRequest**

```typescript
interface CreateInquiryRequest {
  user_id: string;
  content: string;
  source_system: string;  // 送信元システム (例: "manual", "email", "chat")
}
```

**UpdateInquiryRequest**

```typescript
interface UpdateInquiryRequest {
  content?: string;
  source_system?: string;
}
```

**GenerateStoryRequest**

```typescript
interface GenerateStoryRequest {
  inquiry_id: number;
  template_id?: number;  // 将来使用
}
```

**UpdateStoryRequest**

```typescript
interface UpdateStoryRequest {
  title?: string;
  description?: string;
  acceptance_criteria?: string;
  category?: StoryCategory;
  priority?: Priority;
  deadline?: string | null;
  assignee_id?: string | null;
}
```

## コンポーネント・インターフェース詳細

### データアクセス層

#### InquiryRepository

**責務**: 問い合わせのCRUD操作とクエリ実行

**契約種別**: Service

**サービスインターフェース**

```typescript
interface InquiryRepository {
  // 作成操作（要件1.1）
  create(data: CreateInquiryData): Promise<InquiryEntity>;

  // 読み取り操作（要件2.3, 2.5）
  findById(id: number): Promise<InquiryEntity | null>;
  findMany(options: FindManyOptions): Promise<InquiryEntity[]>;
  count(filter: InquiryFilter): Promise<number>;

  // 更新操作（要件2.8, 3.1-3.2）
  update(id: number, data: UpdateInquiryData): Promise<InquiryEntity>;
  updateStatus(id: number, status: InquiryStatus): Promise<InquiryEntity>;

  // 削除操作（将来）
  delete(id: number): Promise<void>;
}

interface CreateInquiryData {
  user_id: string;
  content: string;
  source_system: string;
  timestamp: Date;
  status: InquiryStatus;
}

interface UpdateInquiryData {
  content?: string;
  source_system?: string;
}

interface FindManyOptions {
  filter?: InquiryFilter;
  sort?: SortOption[];
  pagination?: PaginationOption;
}

interface InquiryFilter {
  status?: InquiryStatus | InquiryStatus[];
  user_id?: string;
  created_after?: Date;
  created_before?: Date;
}

interface SortOption {
  field: 'created_at' | 'updated_at' | 'status';
  direction: 'asc' | 'desc';
}

interface PaginationOption {
  page: number;      // 1-indexed
  limit: number;     // 1-100
}

interface InquiryEntity {
  id: number;
  user_id: string;
  content: string;
  source_system: string;
  timestamp: Date;
  status: InquiryStatus;
  created_at: Date;
  updated_at: Date;
}
```

**実装ノート**

- SQLAlchemyセッション管理は依存性注入で提供される
- すべての書き込み操作でタイムスタンプを自動更新する
- `findMany`はデフォルトで`created_at DESC`でソートする
- ページネーションの`limit`は1-100の範囲に制限する
- トランザクション境界はサービス層で管理する

**エラーハンドリング**

- `EntityNotFoundError`: 指定されたIDのエンティティが存在しない
- `DatabaseError`: データベース操作失敗
- `ValidationError`: データ検証失敗

#### StoryRepository

**責務**: ストーリーのCRUD操作とクエリ実行

**契約種別**: Service

**サービスインターフェース**

```typescript
interface StoryRepository {
  // 作成操作（要件4.2-4.5）
  create(data: CreateStoryData): Promise<StoryEntity>;

  // 読み取り操作（要件5.1-5.2）
  findById(id: number): Promise<StoryEntity | null>;
  findMany(options: FindManyOptions): Promise<StoryEntity[]>;
  findByInquiryId(inquiryId: number): Promise<StoryEntity[]>;
  count(filter: StoryFilter): Promise<number>;

  // 更新操作（要件5.3-5.5）
  update(id: number, data: UpdateStoryData): Promise<StoryEntity>;
  updateStatus(id: number, status: StoryStatus): Promise<StoryEntity>;

  // 削除操作（将来）
  delete(id: number): Promise<void>;
}

interface CreateStoryData {
  inquiry_id: number;
  title: string;
  description: string;
  acceptance_criteria: string;
  category: StoryCategory;
  priority: Priority;
  deadline?: Date | null;
  assignee_id?: string | null;
  status: StoryStatus;
}

interface UpdateStoryData {
  title?: string;
  description?: string;
  acceptance_criteria?: string;
  category?: StoryCategory;
  priority?: Priority;
  deadline?: Date | null;
  assignee_id?: string | null;
}

interface StoryFilter {
  status?: StoryStatus | StoryStatus[];
  priority?: Priority | Priority[];
  category?: StoryCategory | StoryCategory[];
  assignee_id?: string;
  deadline_before?: Date;
  deadline_after?: Date;
}

interface StoryEntity {
  id: number;
  inquiry_id: number;
  title: string;
  description: string;
  acceptance_criteria: string;
  category: StoryCategory;
  priority: Priority;
  deadline: Date | null;
  assignee_id: string | null;
  status: StoryStatus;
  created_at: Date;
  updated_at: Date;
}
```

**実装ノート**

- `findByInquiryId`は関連ストーリーの一括取得に使用する
- デフォルトソートは`priority DESC, created_at DESC`

**エラーハンドリング**

- `EntityNotFoundError`: 指定されたIDのエンティティが存在しない
- `DatabaseError`: データベース操作失敗
- `ValidationError`: データ検証失敗

### サービス層

#### InquiryValidator

**責務**: 問い合わせデータのバリデーション

**契約種別**: Service

**サービスインターフェース**

```typescript
interface InquiryValidator {
  // 作成時検証（要件1.4）
  validateCreate(data: CreateInquiryRequest): ValidationResult;

  // 更新時検証（要件2.8）
  validateUpdate(data: UpdateInquiryRequest): ValidationResult;

  // コンテンツ検証
  validateContent(content: string): ValidationResult;
}

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

interface ValidationError {
  field: string;
  message: string;
  code: string;  // GS-xxx形式
}
```

**バリデーションルール**

- `content`: 空文字列禁止、最大長10,000文字
- `user_id`: 必須、英数字とアンダースコアのみ、最大50文字
- `source_system`: 必須、送信元システムを識別する文字列（例: "manual", "email", "chat"）、最大50文字

**実装ノート**

- すべてのエラーメッセージは日本語で提供する
- エラーコードは`GS-001`から開始する一意のコード体系
- クライアント側とサーバー側で同じルールを共有する

#### AIStoryGenerator

**責務**: OpenAI APIを使用したストーリー生成

**契約種別**: Service, API

**サービスインターフェース**

```typescript
interface AIStoryGenerator {
  // ストーリー生成（要件4.1-4.3）
  generateStory(request: GenerationRequest): Promise<GeneratedStory>;

  // 生成結果検証（要件4.7）
  validateStructure(story: GeneratedStory): ValidationResult;
}

interface GenerationRequest {
  inquiry_content: string;
  template_content?: string;  // 将来使用
  generation_config?: GenerationConfig;
}

interface GenerationConfig {
  model: string;          // デフォルト: "gpt-4"
  temperature: number;    // デフォルト: 0.7
  max_tokens: number;     // デフォルト: 2000
}

interface GeneratedStory {
  title: string;
  description: string;
  acceptance_criteria: string;
  category: StoryCategory;
  priority: Priority;
}
```

**API契約（OpenAI）**

- **エンドポイント**: `https://api.openai.com/v1/chat/completions`
- **認証**: Bearer Token（環境変数`OPENAI_API_KEY`）
- **レート制限**: 3,500 RPM（tier dependent）
- **タイムアウト**: 30秒
- **リトライ戦略**: 指数バックオフ、最大3回

**プロンプト構造**

```
以下の問い合わせから、アジャイル開発で使用するユーザーストーリーを生成してください。

問い合わせ内容：
{inquiry_content}

出力形式（JSON）：
{
  "title": "簡潔なタイトル（最大100文字）",
  "description": "As a [ユーザー], I want [機能] so that [価値]",
  "acceptance_criteria": "- 具体的な基準1\n- 具体的な基準2\n- 具体的な基準3",
  "category": "development|testing|documentation|research|maintenance|custom",
  "priority": "low|medium|high|urgent"
}

制約：
- タイトルは100文字以内
- 説明はユーザーストーリー形式
- 受入基準は3-5項目
- カテゴリは6種類から選択
- 優先度は4段階から選択
```

**実装ノート**

- AI生成中は`inquiry.status = 'processing'`に設定する（要件4.8）
- 生成失敗時は`inquiry.status = 'failed'`に設定する（要件4.6）
- レスポンスのJSON構造を検証し、必須フィールドの存在を確認する
- タイムアウト、ネットワークエラー、APIエラーを適切にハンドリングする

**エラーハンドリング**

- `AIServiceUnavailableError`: OpenAI APIへの接続失敗
- `AIGenerationTimeoutError`: 生成処理タイムアウト
- `InvalidResponseFormatError`: レスポンス形式が不正
- `AIQuotaExceededError`: APIクォータ超過

#### WorkflowService

**責務**: 問い合わせとストーリーのワークフロー制御

**契約種別**: Service

**サービスインターフェース**

```typescript
interface WorkflowService {
  // 問い合わせワークフロー（要件3.1-3.5）
  approveInquiry(inquiryId: number): Promise<InquiryEntity>;
  rejectInquiry(inquiryId: number): Promise<InquiryEntity>;

  // ストーリーワークフロー（要件5.4-5.5）
  approveStory(storyId: number): Promise<StoryEntity>;
  rejectStory(storyId: number): Promise<StoryEntity>;

  // ストーリー生成ワークフロー（要件4.1-4.8）
  initiateStoryGeneration(inquiryId: number): Promise<StoryEntity>;
}
```

**ワークフロールール**

問い合わせステータス遷移:
- `received` → `processing`: ストーリー生成開始時
- `processing` → `task_working`: ストーリー生成成功時
- `processing` → `failed`: ストーリー生成失敗時
- `task_working` → `completed`: すべてのストーリーが完了時

ストーリーステータス遷移:
- 初期状態: `pending_review`（要件4.4）
- `pending_review` → `approved`: ユーザー承認時
- `pending_review` → `rejected`: ユーザー拒否時
- `approved` → `exported`: 外部システムエクスポート時（将来）

**実装ノート**

- すべてのステータス変更で`updated_at`タイムスタンプを更新する（要件3.3）
- 無効なステータス遷移は`InvalidStateTransitionError`を発生させる
- ワークフロー実行はトランザクション内で行う

**エラーハンドリング**

- `InvalidStateTransitionError`: 無効なステータス遷移
- `InquiryNotFoundError`: 問い合わせが存在しない
- `StoryNotFoundError`: ストーリーが存在しない

#### InquiryQueryService

**責務**: 問い合わせの検索とページネーション

**契約種別**: Service

**サービスインターフェース**

```typescript
interface InquiryQueryService {
  // 一覧取得（要件2.1-2.3）
  listInquiries(request: ListInquiriesRequest): Promise<PaginatedInquiries>;

  // 詳細取得（要件2.5）
  getInquiry(id: number): Promise<InquiryEntity>;
}

interface ListInquiriesRequest {
  page?: number;          // デフォルト: 1
  limit?: number;         // デフォルト: 20、範囲: 1-100（要件2.2）
  status?: InquiryStatus | InquiryStatus[];
  user_id?: string;
  sort_by?: 'created_at' | 'updated_at';
  sort_order?: 'asc' | 'desc';  // デフォルト: 'desc'（要件2.3）
}

interface PaginatedInquiries {
  data: InquiryEntity[];
  meta: {
    page: number;
    limit: number;
    total: number;
    has_next: boolean;
  };
}
```

**実装ノート**

- デフォルトソートは`created_at DESC`（要件2.3）
- ページネーションは1-indexed
- `limit`の範囲検証を実施し、範囲外の値は最大値にクランプする
- `getInquiry`で存在しないIDは404エラー（要件2.6）

**エラーハンドリング**

- `InquiryNotFoundError`: 指定されたIDの問い合わせが存在しない（要件2.6）
- `InvalidPaginationError`: ページネーションパラメータが不正

### API層

#### InquiryAPI

**責務**: 問い合わせ関連のHTTPエンドポイント

**契約種別**: API

**APIエンドポイント**

```typescript
// 問い合わせ作成（要件1.1-1.6）
POST /api/inquiries
Request: CreateInquiryRequest
Response: 201 Created, InquiryResponse
Errors: 400 Bad Request, 500 Internal Server Error

// 問い合わせ一覧（要件2.1-2.4）
GET /api/inquiries?page=1&limit=20&status=received&sort_by=created_at&sort_order=desc
Response: 200 OK, PaginatedResponse<InquiryResponse>
Errors: 400 Bad Request, 500 Internal Server Error

// 問い合わせ詳細（要件2.5-2.6）
GET /api/inquiries/{id}
Response: 200 OK, InquiryResponse
Errors: 404 Not Found, 500 Internal Server Error

// 問い合わせ更新（要件2.8-2.9）
PUT /api/inquiries/{id}
Request: UpdateInquiryRequest
Response: 200 OK, InquiryResponse
Errors: 400 Bad Request, 404 Not Found, 500 Internal Server Error

// 問い合わせ承認（要件3.1）
POST /api/inquiries/{id}/approve
Response: 200 OK, InquiryResponse
Errors: 404 Not Found, 409 Conflict, 500 Internal Server Error

// 問い合わせ却下（要件3.2）
POST /api/inquiries/{id}/reject
Response: 200 OK, InquiryResponse
Errors: 404 Not Found, 409 Conflict, 500 Internal Server Error
```

**実装ノート**

- すべてのエンドポイントでJSONシリアライゼーション/デシリアライゼーションを実施
- バリデーションエラーは400 Bad Requestで日本語エラーメッセージを返す（要件1.3）
- タイムスタンプはISO 8601形式で返す
- CORS設定は開発環境で`http://localhost:3000`を許可
- エラーレスポンスは統一フォーマット

**エラーレスポンス形式**

```typescript
interface ErrorResponse {
  errors: Array<{
    code: string;      // GS-xxx形式
    message: string;   // 日本語メッセージ
    field?: string;    // バリデーションエラー時のフィールド名
  }>;
  timestamp: string;   // ISO 8601形式
}
```

#### StoryAPI

**責務**: ストーリー関連のHTTPエンドポイント

**契約種別**: API

**APIエンドポイント**

```typescript
// ストーリー生成（要件4.1-4.8）
POST /api/stories/generate
Request: GenerateStoryRequest
Response: 201 Created, StoryResponse
Errors: 400 Bad Request, 404 Not Found, 422 Unprocessable Entity, 503 Service Unavailable

// ストーリー一覧（要件5.1）
GET /api/stories?page=1&limit=20&status=pending_review&priority=high
Response: 200 OK, PaginatedResponse<StoryResponse>
Errors: 400 Bad Request, 500 Internal Server Error

// ストーリー詳細（要件5.2）
GET /api/stories/{id}
Response: 200 OK, StoryResponse
Errors: 404 Not Found, 500 Internal Server Error

// ストーリー更新（要件5.3）
PUT /api/stories/{id}
Request: UpdateStoryRequest
Response: 200 OK, StoryResponse
Errors: 400 Bad Request, 404 Not Found, 500 Internal Server Error

// ストーリー承認（要件5.4）
POST /api/stories/{id}/approve
Response: 200 OK, StoryResponse
Errors: 404 Not Found, 409 Conflict, 500 Internal Server Error

// ストーリー拒否（要件5.5）
POST /api/stories/{id}/reject
Response: 200 OK, StoryResponse
Errors: 404 Not Found, 409 Conflict, 500 Internal Server Error
```

**実装ノート**

- `/generate`エンドポイントはAI処理のため最大30秒のタイムアウト
- AI処理失敗時は503 Service Unavailableを返す（要件4.6）
- 構造検証失敗時は422 Unprocessable Entityを返す（要件4.7）
- ストーリー生成中の問い合わせは`processing`ステータス（要件4.8）

### UI層

#### InquiryForm

**責務**: 問い合わせ入力フォーム

**契約種別**: UI

**プロパティ**

```typescript
interface InquiryFormProps {
  onSubmit: (inquiry: CreateInquiryRequest) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
  initialData?: Partial<CreateInquiryRequest>;
}
```

**実装ノート（要件6.1-6.3）**

- React Hook Formでフォーム状態を管理
- Zodスキーマでクライアント側バリデーションを実施
- バリデーションエラーはフィールド直下に日本語で表示
- 送信中は送信ボタンを無効化し、ローディング状態を表示
- 成功時はreact-hot-toastで成功メッセージを表示
- サーバーエラーはフォーム上部にエラーバナーで表示

**バリデーションルール**

- `content`: 必須、最大10,000文字
- `user_id`: 必須、英数字とアンダースコア、最大50文字

#### InquiryList

**責務**: 問い合わせ一覧表示

**契約種別**: UI

**プロパティ**

```typescript
interface InquiryListProps {
  onInquiryClick: (inquiryId: number) => void;
  onApprove?: (inquiryId: number) => Promise<void>;
  onReject?: (inquiryId: number) => Promise<void>;
  statusFilter?: InquiryStatus[];
}
```

**実装ノート（要件6.4-6.5）**

- TanStack Queryでページネーションとキャッシュを管理
- デフォルトページサイズは20件
- 各行に問い合わせID、内容（省略表示）、ステータス、タイムスタンプを表示（要件2.4）
- ステータスフィルタードロップダウンを提供
- 行クリックで詳細ページへ遷移
- ページネーションコントロール（前へ/次へ/ページ番号）

#### InquiryDetail

**責務**: 問い合わせ詳細表示・編集

**契約種別**: UI

**プロパティ**

```typescript
interface InquiryDetailProps {
  inquiryId: number;
  onUpdate: (data: UpdateInquiryRequest) => Promise<void>;
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
  onGenerateStory: () => Promise<void>;
}
```

**実装ノート（要件6.5）**

- 読み取りモードと編集モードを切り替え可能
- 編集モードではインライン編集をサポート
- 承認/却下/ストーリー生成ボタンを提供（要件3.4, 4.1）
- 関連ストーリーがある場合はリンクを表示
- 更新履歴を時系列で表示（`updated_at`タイムスタンプ）

#### StoryBoard

**責務**: ストーリー一覧・詳細表示

**契約種別**: UI

**プロパティ**

```typescript
interface StoryBoardProps {
  onStoryClick: (storyId: number) => void;
  statusFilter?: StoryStatus[];
  priorityFilter?: Priority[];
}
```

**実装ノート（要件6.6-6.7）**

- カンバンボード形式でストーリーをステータス別に表示
- 各カードにタイトル、優先度、担当者IDを表示（要件5.2）
- ドラッグ&ドロップでステータス変更（将来機能）
- フィルタリング機能（ステータス、優先度、カテゴリ、担当者ID）
- ソート機能（優先度、期限、作成日時）

#### StoryDetail

**責務**: ストーリー詳細表示・編集

**契約種別**: UI

**プロパティ**

```typescript
interface StoryDetailProps {
  storyId: number;
  onUpdate: (data: UpdateStoryRequest) => Promise<void>;
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
}
```

**実装ノート（要件5.3-5.5）**

- 全フィールドの詳細表示（タイトル、説明、受入基準、カテゴリ、優先度、期限）
- 編集モードでインライン編集をサポート
- 承認/拒否ボタンを提供
- 元の問い合わせへのリンクを表示
- 担当者ID・期限の設定UI（要件5.7）

## エラーハンドリング

### エラー分類

| エラータイプ | HTTPステータス | 説明 | ユーザーアクション |
|------------|--------------|------|------------------|
| ValidationError | 400 | 入力値検証失敗 | 入力値を修正して再送信 |
| EntityNotFoundError | 404 | リソースが存在しない | URLを確認 |
| InvalidStateTransitionError | 409 | 不正な状態遷移 | 現在の状態を確認 |
| InvalidResponseFormatError | 422 | AI生成結果が不正 | 再試行 |
| AIServiceUnavailableError | 503 | OpenAI API接続失敗 | しばらく待って再試行 |
| DatabaseError | 500 | データベースエラー | サポートに連絡 |

### エラーコード体系

```
GS-001: 問い合わせ内容が空です
GS-002: 問い合わせ内容が長すぎます（最大10,000文字）
GS-003: ユーザーIDが不正です
GS-004: 言語コードが不正です
GS-005: 指定された問い合わせが見つかりません
GS-006: 指定されたストーリーが見つかりません
GS-007: 不正なステータス遷移です
GS-008: AI生成処理に失敗しました
GS-009: AI生成結果の構造が不正です
GS-010: データベース操作に失敗しました
GS-011: ページネーションパラメータが不正です
GS-012: ストーリーに循環依存が検出されました
GS-013: AI APIへの接続に失敗しました
GS-014: AI APIのクォータを超過しました
GS-015: 処理がタイムアウトしました
```

### エラーログ戦略

**構造化ログ形式**

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "ERROR",
  "message": "AI generation failed",
  "error_code": "GS-008",
  "context": {
    "inquiry_id": 123,
    "user_id": "user_001",
    "ai_model": "gpt-4",
    "error_details": "Connection timeout"
  },
  "stack_trace": "..."
}
```

**ログレベル**

- `DEBUG`: 開発環境のみ、詳細なデバッグ情報
- `INFO`: 通常の操作ログ（問い合わせ作成、ストーリー生成開始など）
- `WARNING`: 警告（リトライ実行、パフォーマンス低下など）
- `ERROR`: エラー（バリデーション失敗、AI生成失敗など）
- `CRITICAL`: 致命的エラー（データベース接続失敗など）

**監視対象メトリクス**

- AI生成成功率（目標: 95%以上）
- AI生成平均時間（目標: 10秒以内）
- API応答時間P95（目標: 500ms以内）
- エラー発生率（目標: 1%未満）

## テスト戦略

### テスト範囲

| レイヤー | テスト種別 | カバレッジ目標 | ツール |
|---------|----------|--------------|--------|
| データアクセス | ユニットテスト | 90% | pytest + SQLite |
| サービス層 | ユニットテスト | 85% | pytest + Mock |
| API層 | 統合テスト | 80% | pytest + TestClient |
| UI層 | コンポーネントテスト | 70% | Jest + RTL |
| E2E | E2Eテスト | 主要フロー | Playwright（将来） |

### テストケース優先度

**P0（必須）**
- 問い合わせ作成フロー全体（要件1.1-1.6）
- AI生成フロー全体（要件4.1-4.8）
- ステータス遷移ロジック（要件3.1-3.5, 5.4-5.5）
- バリデーションルール（要件1.4, 2.8）

**P1（高優先度）**
- ページネーション機能（要件2.1-2.3）
- エラーハンドリング全般
- データ整合性制約
- 依存関係の循環検出

**P2（中優先度）**
- UI コンポーネント個別機能
- ソート・フィルタリング
- メタデータ処理

### テスト例

**ユニットテスト例: InquiryValidator**

```python
def test_validate_create_with_empty_content():
    validator = InquiryValidator()
    data = CreateInquiryRequest(
        user_id="test_user",
        content="",
        source_system="manual"
    )
    result = validator.validate_create(data)

    assert result.valid is False
    assert len(result.errors) == 1
    assert result.errors[0].code == "GS-001"
    assert "空です" in result.errors[0].message
```

**統合テスト例: Story Generation API**

```python
@pytest.mark.asyncio
async def test_generate_story_success(client, db_session, mock_openai):
    # Arrange
    inquiry = create_test_inquiry(db_session, content="ログイン機能が欲しい")
    mock_openai.return_value = {
        "title": "ログイン機能の実装",
        "description": "As a user, I want to log in...",
        "acceptance_criteria": "- ユーザー名とパスワードで認証できる",
        "category": "development",
        "priority": "high"
    }

    # Act
    response = await client.post(
        "/api/stories/generate",
        json={"inquiry_id": inquiry.id}
    )

    # Assert
    assert response.status_code == 201
    story = response.json()
    assert story["title"] == "ログイン機能の実装"
    assert story["status"] == "pending_review"

    # Verify inquiry status updated
    updated_inquiry = db_session.get(Inquiry, inquiry.id)
    assert updated_inquiry.status == "task_working"
```

**コンポーネントテスト例: InquiryForm**

```typescript
test('displays validation error for empty content', async () => {
  const mockSubmit = jest.fn();
  render(<InquiryForm onSubmit={mockSubmit} />);

  const submitButton = screen.getByRole('button', { name: /送信/ });
  fireEvent.click(submitButton);

  await waitFor(() => {
    expect(screen.getByText(/問い合わせ内容が空です/)).toBeInTheDocument();
  });

  expect(mockSubmit).not.toHaveBeenCalled();
});
```

### プロパティベーステスト

```python
from hypothesis import given, strategies as st

@given(
    content=st.text(min_size=1, max_size=10000),
    user_id=st.text(min_size=1, max_size=50)
)
def test_inquiry_creation_properties(content, user_id):
    """Test that valid inputs always create valid inquiries"""
    data = CreateInquiryData(
        user_id=user_id,
        content=content,
        source_system="manual",
        timestamp=datetime.now(),
        status=InquiryStatus.RECEIVED
    )

    # Should not raise exception
    inquiry = InquiryRepository().create(data)

    # Invariants
    assert inquiry.id > 0
    assert inquiry.content == content
    assert inquiry.status == InquiryStatus.RECEIVED
```

## 未解決事項

### 技術的課題

1. **AI生成品質の評価**: 生成されたストーリーの品質をどのように評価するか（将来検討）
2. **長時間処理の対応**: AI生成が30秒を超える場合の非同期処理化（Phase 2で検討）
3. **全文検索**: PostgreSQLの全文検索機能 vs Elasticsearch導入の判断

### ビジネス要件

1. **外部連携の優先順位**: Trello、Jira、GitHub Projectsのどれを優先実装するか
2. **テンプレート機能の詳細**: テンプレートの作成・管理UI仕様
3. **通知機能**: ストーリー生成完了時の通知方法（メール、Slack、Webhook）
4. **監査ログの範囲**: どこまで詳細なログを保存するか

### オープンな設計判断

1. **バッチエクスポート**: 複数ストーリーの一括エクスポート機能の詳細仕様
2. **リアルタイム更新**: WebSocketによるリアルタイム状態同期の必要性
3. **国際化の範囲**: 日本語以外の言語サポートの優先順位

## 付録

### 参照ドキュメント

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0ドキュメント](https://docs.sqlalchemy.org/en/20/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [React公式ドキュメント](https://react.dev/)
- [TanStack Query](https://tanstack.com/query/latest)

### 用語集

- **問い合わせ（Inquiry）**: 報告者からの自然言語による要求
- **ストーリー（Story）**: 構造化されたユーザーストーリー
- **AI生成（AI Generation）**: OpenAI APIを使用した自動ストーリー生成
- **ワークフロー（Workflow）**: ステータス遷移の制御ロジック
- **レビュー（Review）**: 人間によるストーリー確認・編集プロセス
- **エクスポート（Export）**: 外部システムへのデータ連携

### 変更履歴

| 日付 | バージョン | 変更内容 | 承認者 |
|------|----------|---------|-------|
| 2025-12-27 | 1.4 | セキュリティ、パフォーマンス、移行戦略セクション削除（開発フェーズに集中） | - |
| 2025-12-27 | 1.3 | Storyモデル簡素化（dependencies、estimated_effort削除、assignee→assignee_idリネーム） | - |
| 2025-12-27 | 1.2 | タグ機能削除（ユーザーフィードバック対応） | - |
| 2025-12-27 | 1.1 | 設計レビュー対応（dependencies復元、既存実装との統合戦略追加） | - |
| 2025-12-27 | 1.0 | 初版作成（ゼロベース再生成） | - |

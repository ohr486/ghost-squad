# ストーリーボード機能 設計ドキュメント

## 概要

Ghost Squadのストーリーボード機能は、日本語自然言語の問い合わせを構造化されたユーザーストーリーに変換し、既存のカンバンシステム（Trello、Jira、GitHub Projects）に統合するためのWebアプリケーション機能です。システムは問い合わせの受付、OpenAI API駆動のストーリー生成、ユーザーレビュー、外部システム統合の4つの主要フェーズで構成されます。

## アーキテクチャ

Ghost Squadのストーリーボード機能は、以下のレイヤーで構成されるクリーンアーキテクチャを採用します：

```mermaid
graph TB
    subgraph "プレゼンテーション層"
        UI[React TypeScript WebUI]
        API[FastAPI REST API]
    end
    
    subgraph "アプリケーション層"
        IS[問い合わせサービス]
        SS[ストーリーサービス]
        NS[通知サービス]
        ES[エクスポートサービス]
    end
    
    subgraph "ドメイン層"
        SC[ストーリー変換器]
        SM[ストーリーモデル]
        IM[問い合わせモデル]
        PR[パターン認識器]
    end
    
    subgraph "インフラストラクチャ層"
        DB[(PostgreSQL)]
        AI[OpenAI API]
        EXT[外部カンバンAPI]
        NOTIF[通知プロバイダー]
    end
    
    UI --> API
    API --> IS
    API --> SS
    API --> NS
    API --> ES
    
    IS --> SC
    SS --> SM
    SS --> PR
    
    SC --> AI
    SM --> DB
    IM --> DB
    ES --> EXT
    NS --> NOTIF
```

## コンポーネントとインターフェース

### 1. 問い合わせサービス (InquiryService)

**責任**: 問い合わせの受付、検証、保存

```typescript
interface InquiryService {
  submitInquiry(inquiry: string, userId: string): Promise<InquiryResult>
  getInquiryHistory(userId: string): Promise<Inquiry[]>
  requestClarification(inquiryId: number, questions: string[]): Promise<void>
  updateInquiryStatus(inquiryId: number): Promise<void>
  checkTaskCompletion(inquiryId: number): Promise<boolean>
}

interface InquiryResult {
  inquiryId: number
  status: 'processing' | 'needs_clarification' | 'story_working' | 'completed'
  generatedStories?: Story[]
  clarificationQuestions?: string[]
}
```

### 2. ストーリー変換器 (StoryConverter)

**責任**: AI APIを使用した問い合わせのストーリー変換

```typescript
interface StoryConverter {
  convertToStories(inquiry: Inquiry): Promise<Story[]>
  extractDeadlines(inquiry: string): Promise<Date | null>
  categorizeStory(storyDescription: string): Promise<StoryCategory>
  estimateEffort(storyDescription: string): Promise<number>
}

interface Story {
  id: number
  title: string
  description: string
  category: StoryCategory
  priority: Priority
  estimatedEffort: number
  deadline?: Date
  status: StoryStatus
  metadata: StoryMetadata
}
```

### 3. パターン認識器 (PatternRecognizer)

**責任**: ストーリーパターンの識別とテンプレート適用

```typescript
interface PatternRecognizer {
  identifyPattern(storyDescription: string): Promise<StoryPattern>
  applyTemplate(pattern: StoryPattern, story: Story): Promise<Story>
  learnFromHistory(stories: Story[]): Promise<void>
}

enum StoryPattern {
  BUG_FIX = 'bug_fix',
  FEATURE_ADDITION = 'feature_addition',
  INVESTIGATION = 'investigation',
  REVIEW = 'review',
  MAINTENANCE = 'maintenance'
}
```

### 4. ストーリーサービス (StoryService)

**責任**: ストーリーのCRUD操作、レビュー管理

```typescript
interface StoryService {
  getPendingStories(userId: string): Promise<Story[]>
  updateStory(storyId: number, updates: Partial<Story>): Promise<Story>
  approveStory(storyId: number): Promise<void>
  rejectStory(storyId: number, reason?: string): Promise<void>
  batchApprove(storyIds: number[]): Promise<void>
  getStoryHistory(storyId: number): Promise<StoryVersion[]>
}
```

### 5. エクスポートサービス (ExportService)

**責任**: 外部カンバンシステムへのストーリー出力

```typescript
interface ExportService {
  exportToKanban(stories: Story[], targetSystem: KanbanSystem): Promise<ExportResult>
  getSupportedSystems(): KanbanSystem[]
  trackSyncStatus(storyId: number): Promise<SyncStatus>
}

interface KanbanSystem {
  name: string
  apiEndpoint: string
  authConfig: AuthConfig
  fieldMapping: FieldMapping
}
```

### 6. 通知サービス (NotificationService)

**責任**: ユーザー通知の管理

```typescript
interface NotificationService {
  sendStoryCompletionNotification(userId: string, stories: Story[]): Promise<void>
  sendErrorAlert(userId: string, error: Error): Promise<void>
  sendDeadlineReminder(userId: string, stories: Story[]): Promise<void>
  configureNotificationSettings(userId: string, settings: NotificationSettings): Promise<void>
}
```

## データモデル

### ID型について

**重要な設計決定**: Ghost Squadのすべてのエンティティ（Inquiry、Story、StoryTemplate）のIDフィールドは、パフォーマンスと外部システム統合を考慮してBigInteger（64ビット整数）を使用します。

- **利点**:
  - データベースインデックスの効率性向上
  - 結合処理の高速化
  - ストレージ効率の改善（16バイト → 8バイト）
  - 順序性の保証（作成順序の把握が容易）
  - 外部システムとの統合の簡素化

- **自動インクリメント**: すべてのIDは自動的に生成され、1から開始
- **範囲**: 1から9,223,372,036,854,775,807まで（実用上無制限）

### 問い合わせモデル

```typescript
interface Inquiry {
  id: number
  userId: string
  content: string
  language: 'ja' | 'en'
  timestamp: Date
  status: InquiryStatus
  metadata: {
    source: string
    processingTime?: number
    aiModel?: string
  }
}

enum InquiryStatus {
  RECEIVED = 'received',
  PROCESSING = 'processing',
  NEEDS_CLARIFICATION = 'needs_clarification',
  STORY_WORKING = 'story_working',
  COMPLETED = 'completed',
  FAILED = 'failed'
}
```

### ストーリーモデル

```typescript
interface Story {
  id: number
  inquiryId: number
  title: string
  description: string
  category: StoryCategory
  priority: Priority
  estimatedEffort: number // 時間単位
  deadline?: Date
  status: StoryStatus
  assignee?: string
  tags: string[]
  dependencies: number[] // 他のストーリーID
  metadata: StoryMetadata
  createdAt: Date
  updatedAt: Date
}

enum StoryCategory {
  DEVELOPMENT = 'development',
  TESTING = 'testing',
  DOCUMENTATION = 'documentation',
  RESEARCH = 'research',
  MAINTENANCE = 'maintenance',
  CUSTOM = 'custom'
}

enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

enum StoryStatus {
  PENDING_REVIEW = 'pending_review',
  APPROVED = 'approved',
  EXPORTED = 'exported',
  REJECTED = 'rejected'
}

interface StoryMetadata {
  originalInquiry: string
  generationLog: string[]
  appliedTemplate?: string
  confidence: number // 0-1
  reviewNotes?: string[]
}
```

### テンプレートモデル

```typescript
interface StoryTemplate {
  id: number
  name: string
  pattern: StoryPattern
  fields: TemplateField[]
  checklist: string[]
  defaultEstimate: number
  isCustom: boolean
  userId?: string // カスタムテンプレートの場合
}

interface TemplateField {
  name: string
  type: 'text' | 'number' | 'date' | 'select'
  required: boolean
  defaultValue?: any
  options?: string[] // select型の場合
}
```

## 正確性プロパティ

*プロパティとは、システムのすべての有効な実行において真であるべき特性や動作のことです。これらは人間が読める仕様と機械で検証可能な正確性保証の橋渡しとなります。*

### プロパティ1: 問い合わせ受付と保存
*任意の*有効な問い合わせに対して、システムが受け付けた場合、その問い合わせはデータベースに永続化され、一意のIDが割り当てられる
**検証: 要件 1.1, 6.1, 9.1**

### プロパティ2: ストーリー変換の完全性
*任意の*受け付けられた問い合わせに対して、ストーリー変換器は少なくとも1つの実行可能なストーリーを抽出するか、明確化要求を生成する
**検証: 要件 1.2, 1.4**

### プロパティ3: 複数ストーリー分離
*任意の*複数のストーリーを含む問い合わせに対して、システムは各ストーリーに対して個別のストーリー項目を作成し、それぞれに一意のIDを割り当てる
**検証: 要件 1.3**

### プロパティ4: 日本語サポート
*任意の*日本語の問い合わせに対して、システムは適切に処理し、日本語のUIで結果を表示する
**検証: 要件 1.5, 8.6**

### プロパティ5: 自動分類の一貫性
*任意の*作成されたストーリーに対して、システムは有効なカテゴリ、優先度レベル、推定工数を割り当てる
**検証: 要件 2.1, 2.2**

### プロパティ6: 緊急キーワード検出
*任意の*緊急キーワード（緊急、至急、ASAP）を含むストーリーに対して、システムは高優先度を割り当てる
**検証: 要件 2.3**

### プロパティ7: カスタムカテゴリサポート
*任意の*ユーザー定義カスタムカテゴリに対して、システムはそれを有効なカテゴリとして認識し、タスクに割り当て可能にする
**検証: 要件 2.4**

### プロパティ8: 依存関係自動識別
*任意の*関連するストーリーセットに対して、システムは適切な依存関係を識別し、循環依存を作成しない
**検証: 要件 2.5**

### プロパティ9: ストーリー初期状態
*任意の*生成されたストーリーに対して、システムは初期状態を「レビュー待ち」に設定し、必要なメタデータを含める
**検証: 要件 3.1, 6.1**

### プロパティ10: レビューデータ完全性
*任意の*レビュー対象ストーリーに対して、システムはタイトル、説明、カテゴリ、優先度、推定工数、期限のすべてのフィールドを編集可能な形式で表示する
**検証: 要件 3.2**

### プロパティ11: 変更履歴保持
*任意の*ストーリー修正に対して、システムは変更前後の状態を記録し、変更履歴を維持する
**検証: 要件 3.3, 6.5**

### プロパティ12: 状態遷移の正確性
*任意の*ストーリーに対して、承認時は「送信待ち」状態に、拒否時は「拒否」状態または削除状態に遷移する
**検証: 要件 3.4, 3.5**

### プロパティ13: 一括処理の原子性
*任意の*一括操作に対して、すべてのストーリーが成功するか、すべてが失敗するかのいずれかになる（部分的成功はない）
**検証: 要件 3.6**

### プロパティ14: 出力データ完全性
*任意の*出力されるストーリーに対して、タイトル、説明、カテゴリ、優先度、推定工数、期限（設定されている場合）のすべての情報が含まれる
**検証: 要件 4.2, 10.3**

### プロパティ15: 外部システム統合
*任意の*サポートされるカンバンシステムに対して、タスクが正常に出力され、追跡IDが生成される
**検証: 要件 4.3, 4.4, 4.5**

### プロパティ16: パターン認識とテンプレート適用
*任意の*認識されたストーリーパターンに対して、システムは対応するテンプレートを適用し、テンプレートの必須フィールドを設定する
**検証: 要件 5.1, 5.2, 5.4**

### プロパティ17: カスタムテンプレート管理
*任意の*ユーザー定義テンプレートに対して、システムはそれを保存し、適切なパターンに対して適用可能にする
**検証: 要件 5.3**

### プロパティ18: 生成ログ記録
*任意の*ストーリー生成プロセスに対して、システムは分析ステップ、適用されたルール、使用されたテンプレートをログとして記録する
**検証: 要件 6.2, 6.3**

### プロパティ19: コメント機能
*任意の*ストーリーに対して、ユーザーが追加したコメントやメモは適切に保存され、ストーリーと関連付けられる
**検証: 要件 6.4**

### プロパティ20: 通知配信
*任意の*通知イベント（完了、エラー、確認要求）に対して、システムは設定された通知チャネルを通じて適切な通知を送信する
**検証: 要件 7.1, 7.2, 7.3, 7.4**

### プロパティ21: 通知設定適用
*任意の*ユーザー通知設定に対して、システムはその設定に従って通知の送信/非送信を決定する
**検証: 要件 7.5**

### プロパティ22: 検索機能
*任意の*検索クエリに対して、システムは関連する問い合わせとストーリーを適切にフィルタリングして返す
**検証: 要件 8.4**

### プロパティ23: 進捗状況更新
*任意の*ストーリー生成またはレビュープロセスに対して、システムはリアルタイムで進捗状況を更新し、UIに反映する
**検証: 要件 8.5**

### プロパティ24: データ復元
*任意の*システム再起動に対して、永続ストレージからすべてのデータが適切に復元され、データ損失が発生しない
**検証: 要件 9.3**

### プロパティ25: バックアップ実行
*任意の*データ変更に対して、システムは定期的な自動バックアップを実行し、バックアップの成功/失敗を記録する
**検証: 要件 9.4**

### プロパティ26: 同期状態追跡
*任意の*外部システムへのストーリー出力に対して、システムは同期状態を追跡し、同期の成功/失敗を記録する
**検証: 要件 9.5**

### プロパティ27: 期限自動設定
*任意の*期限情報を含む問い合わせに対して、システムは自然言語から適切な日付を抽出し、ストーリーの期限として設定する
**検証: 要件 10.2**

### プロパティ28: 期限通知
*任意の*期限が設定されたストーリーに対して、期限が近づいた時（設定可能な日数前）にユーザーに通知を送信する
**検証: 要件 10.4**

### プロパティ29: 期限による優先度調整
*任意の*期限が設定されたストーリーに対して、期限までの残り時間に基づいて優先度を自動的に調整する
**検証: 要件 10.5**

### プロパティ30: 問い合わせステータス管理
*任意の*問い合わせに対して、関連するすべてのストーリーが完了状態（exported）になった場合はステータスを「completed」に、未完了のストーリーがある場合は「story_working」に設定する
**検証: 要件 1.1, 3.4**

### プロパティ31: データベーススキーマの整合性
*任意の*JSONカラムに対して、nullable=Falseの場合は適切なデフォルト値が設定され、データ挿入時にエラーが発生しない
**検証: 要件 11.1, 11.2, 11.3, 11.4**
## データベーススキーマ整合性の設計

### 問題の特定

現在のデータベーススキーマには以下の問題があります：

1. **story_metadata カラム**: `nullable=False` だが、サーバーレベルのデフォルト値が設定されていない
2. **他のJSONカラムの潜在的問題**: `fields`、`checklist` カラム（story_templates テーブル）も同様の問題を抱える可能性

### 解決方針

#### 1. サーバーデフォルト値の追加
- `story_metadata` カラムに `server_default='{}' ` を設定
- 既存データに影響を与えない安全なマイグレーション

#### 2. SQLAlchemyモデルの更新
- Python レベルでのデフォルト値も設定（`default=dict`）
- 二重の保護により確実なデータ整合性を確保

#### 3. 他のJSONカラムの検証
- `story_templates.fields` と `story_templates.checklist` の設定確認
- 必要に応じて同様の修正を適用

### マイグレーション戦略

```python
# 安全なマイグレーション手順
def upgrade():
    # 1. 既存のnullable=Falseカラムにserver_defaultを追加
    op.alter_column('stories', 'story_metadata',
                   server_default='{}')
    
    # 2. 他のJSONカラムも同様に処理（必要に応じて）
    op.alter_column('story_templates', 'fields',
                   server_default='[]')
    op.alter_column('story_templates', 'checklist', 
                   server_default='[]')
```

### 検証方法

1. **マイグレーション前後のデータ整合性確認**
2. **新規データ挿入テスト**（値なしでの挿入）
3. **既存データの保持確認**
4. **ロールバックテスト**

### エラー分類

1. **入力エラー**
   - 無効な問い合わせ形式
   - サポートされていない言語
   - 空の問い合わせ

2. **処理エラー**
   - AI API接続失敗
   - タスク変換失敗
   - パターン認識失敗

3. **システムエラー**
   - データベース接続失敗
   - 外部API接続失敗
   - 認証エラー

4. **ビジネスロジックエラー**
   - 循環依存の検出
   - 無効なテンプレート
   - 権限不足

### エラー処理戦略

```typescript
interface ErrorHandler {
  handleInputError(error: InputError): ErrorResponse
  handleProcessingError(error: ProcessingError): ErrorResponse
  handleSystemError(error: SystemError): ErrorResponse
  handleBusinessLogicError(error: BusinessLogicError): ErrorResponse
}

interface ErrorResponse {
  errorCode: string
  message: string
  userMessage: string
  retryable: boolean
  suggestedActions: string[]
}
```

### 回復戦略

- **自動リトライ**: 一時的なネットワークエラーやAPI制限
- **フォールバック**: AI APIが利用できない場合のルールベース処理
- **グレースフルデグラデーション**: 一部機能が利用できない場合の代替処理
- **ユーザー通知**: 回復不可能なエラーの場合の適切な通知

## テスト戦略

### 二重テストアプローチ

システムは**ユニットテスト**と**プロパティベーステスト**の両方を使用して包括的なカバレッジを実現します：

- **ユニットテスト**: 特定の例、エッジケース、エラー条件を検証
- **プロパティテスト**: すべての入力にわたる普遍的なプロパティを検証
- 両方のテストは相補的であり、包括的なカバレッジに必要です

### プロパティベーステスト設定

- **テストライブラリ**: fast-check (TypeScript/JavaScript)
- **最小実行回数**: 各プロパティテストあたり100回の反復
- **タグ形式**: **Feature: storyboard, Property {number}: {property_text}**
- 各正確性プロパティは単一のプロパティベーステストで実装される

### テストカテゴリ

1. **統合テスト**
   - エンドツーエンドのワークフロー
   - 外部システム統合
   - UI操作フロー

2. **ユニットテスト**
   - 個別コンポーネントの動作
   - エラーケースの処理
   - 境界値テスト

3. **プロパティテスト**
   - 普遍的な正確性プロパティ
   - ランダム入力での動作検証
   - 不変条件の維持

### テスト環境

- **開発環境**: 高速フィードバックのための軽量テスト
- **ステージング環境**: 本番類似環境での統合テスト
- **本番環境**: 監視とアラートによる継続的検証
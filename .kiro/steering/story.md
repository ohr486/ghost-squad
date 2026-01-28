---
inclusion: always
updated_at: 2026-01-28
---

# Story機能 開発ガイドライン

Story（ストーリー）機能は、問い合わせから構造化されたユーザーストーリーを生成・管理するコアサブシステムです。AI自動生成と手動作成の両方に対応し、承認ワークフローを提供します。

## アーキテクチャパターン

### レイヤードアーキテクチャ + AI統合

Storyは**API層 → サービス層（5つ） → リポジトリ層 → モデル層**の構造に加え、**AI生成サービス**を統合。

```
API層 (routers/story.py)
    │
    ├── StoryQueryService（読み取り操作）
    │       └── StoryRepository
    │
    ├── StoryWorkflowService（状態遷移操作）
    │       ├── StoryValidator
    │       └── StoryRepository
    │
    └── StoryGenerationService（AI生成）
            ├── OpenAI API
            ├── StoryValidator
            └── StoryRepository
```

**設計意図**: AI生成ロジックの分離、読み取り/書き込み/生成の責務分離。

### 問い合わせとの連携パターン

StoryはInquiryに依存し、生成時にInquiryのステータスも遷移させる。

```
Inquiry (task_working) ──→ StoryGenerationService ──→ Story (waiting_review)
        │                          │
        └─→ (processing)           └─→ (completed)
```

**トランザクション境界**: Inquiry更新とStory作成は同一トランザクション内で実行。

### ステータス遷移パターン

```
WAITING_REVIEW ──┬─→ APPROVED
                 │
                 └─→ REJECTED（理由必須）
```

**ビジネスルール**:
- 生成時は必ず `waiting_review` 状態で作成
- 承認（approve）: `waiting_review` → `approved`
- 却下（reject）: `waiting_review` → `rejected`（理由必須）
- 一括承認: 複数ストーリーの同時承認に対応

## コンポーネント構成

### バックエンド サービス層 (`services/`)

| ファイル | 役割 | 契約 |
|---------|------|------|
| `story_validator.py` | 入力検証、AI生成結果検証 | GS-2xxエラーコード体系 |
| `story_repository.py` | CRUD操作、フィルタリング・ソート | トランザクション境界管理 |
| `story_query_service.py` | 一覧取得、検索、ページネーション | 読み取り専用操作 |
| `story_workflow_service.py` | 承認・却下・一括承認 | 状態整合性保証 |
| `story_generation_service.py` | OpenAI API統合、AI生成 | リトライ戦略、ロールバック |

### スキーマ層 (`models/schemas/story.py`)

APIリクエスト/レスポンス用Pydanticスキーマを提供。
- `CreateStoryRequest` - ストーリー作成リクエスト（手動作成用）
- `UpdateStoryRequest` - ストーリー更新リクエスト（全フィールドオプション）
- `StoryResponse` - ストーリーレスポンス（ISO 8601 datetime）
- `ApproveStoryRequest` - 承認リクエスト
- `RejectStoryRequest` - 却下リクエスト（reason必須）
- `BatchApproveRequest` - 一括承認リクエスト
- `StoryMetadata` - メタデータ構造（ApprovalMetadata、RejectionMetadata）

### モデル層

| ファイル | 役割 |
|---------|------|
| `models/database/story.py` | SQLAlchemy ORMモデル（StoryModel） |
| `models/enums/story_status.py` | StoryStatus列挙型 |
| `models/enums/priority.py` | Priority列挙型 |

### API層 (`routers/story.py`)

| エンドポイント | メソッド | 概要 |
|---------------|----------|------|
| `/api/inquiries/{inquiry_id}/stories` | POST | ストーリー作成（AI自動生成 or 手動） |
| `/api/stories` | GET | ストーリー一覧（フィルタ・ソート・ページネーション） |
| `/api/stories/{id}` | GET | ストーリー詳細取得 |
| `/api/inquiries/{inquiry_id}/stories` | GET | 問い合わせ別ストーリー一覧 |
| `/api/stories/{id}` | PUT | ストーリー更新 |
| `/api/stories/{id}` | DELETE | ストーリー削除 |
| `/api/stories/{id}/approve` | POST | ストーリー承認 |
| `/api/stories/{id}/reject` | POST | ストーリー却下（reason必須） |
| `/api/stories/batch-approve` | POST | 一括承認 |

### フロントエンド

| ファイル | 役割 | カバレッジ |
|---------|------|-----------|
| `types/story.ts` | TypeScript型定義（バックエンドと整合） | - |
| `services/storyApi.ts` | APIクライアント（Axios） | 82.45% |
| `components/StoryList.tsx` | 一覧表示・フィルタ・ソート・ページネーション | 95.83% statements |
| `components/StoryForm.tsx` | 作成フォーム（モーダル、問い合わせ選択） | - |
| `components/StoryDetail.tsx` | 詳細・編集・承認/却下/削除 | 93.85% statements |
| `components/StoryIntegration.test.tsx` | E2E統合テスト | - |

## AI生成パターン

### OpenAI API統合

```python
class StoryGenerationService:
    def __init__(self, session: Session):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4")

    def generate_story(self, inquiry_id: int) -> StoryModel:
        # 1. Inquiryステータス検証（task_working必須）
        # 2. Inquiryステータス更新（task_working → processing）
        # 3. OpenAI API呼び出し（リトライ戦略付き）
        # 4. 生成結果の構造検証
        # 5. ストーリー作成
        # 6. Inquiryステータス更新（processing → completed）
        # 7. エラー時ロールバック
```

### リトライ戦略

- **最大試行回数**: 3回
- **バックオフ**: 指数バックオフ（1s → 2s → 4s）
- **タイムアウト**: 30秒
- **ロールバック**: AI生成失敗時はInquiryステータスを元に戻す

### API呼び出しパターン

```python
# 空ボディ → AI自動生成
POST /api/inquiries/{inquiry_id}/stories
Content-Type: application/json
{}

# ボディあり → 手動作成
POST /api/inquiries/{inquiry_id}/stories
Content-Type: application/json
{
  "title": "タイトル",
  "description": "説明",
  "priority": "medium"
}
```

## エラーコード体系

| 範囲 | カテゴリ | 説明 |
|------|----------|------|
| GS-201〜GS-204 | 入力検証 | タイトル長、必須フィールド、inquiry_id存在確認 |
| GS-205 | 状態遷移 | Inquiryステータス不正（task_working以外） |
| GS-206 | AI生成 | OpenAI API呼び出し失敗 |
| GS-210〜GS-219 | ワークフロー | 無効なステータス遷移、却下理由欠落等 |

## データモデル

### StoryModel フィールド

```python
id: int                    # BigInteger、自動インクリメント
inquiry_id: int            # 問い合わせID（外部キー、必須）
title: str                 # タイトル（必須、最大500文字）
description: str           # 説明（必須）
priority: Priority         # 優先度（LOW/MEDIUM/HIGH/URGENT）
status: StoryStatus        # ステータス（WAITING_REVIEW/APPROVED/REJECTED）
estimated_effort: float    # 推定工数（オプション）
deadline: datetime         # 期限（オプション）
assignee: str              # 担当者（オプション、最大50文字）
story_metadata: dict       # メタデータ（JSON）
created_at: datetime       # 作成日時（UTC）
updated_at: datetime       # 更新日時（UTC）
```

### story_metadata 構造

```python
{
    "approval": {
        "approved_at": "2026-01-28T10:00:00Z",
        "approved_by": "user_id"
    },
    "rejection": {
        "rejected_at": "2026-01-28T10:00:00Z",
        "reason": "却下理由"
    },
    "status_history": [
        {"from": "waiting_review", "to": "approved", "at": "..."}
    ],
    "ai_generation": {
        "model": "gpt-4",
        "generated_at": "2026-01-28T09:00:00Z",
        "prompt_tokens": 150,
        "completion_tokens": 200
    }
}
```

## フロントエンド実装パターン

### ストーリー生成トリガー（InquiryDetailから）

```typescript
// InquiryDetail.tsx内
const generateMutation = useMutation({
  mutationFn: () => generateStory(inquiry.id),
  onSuccess: () => {
    queryClient.invalidateQueries(['inquiries']);
    queryClient.invalidateQueries(['stories']);
    toast.success('ストーリーを生成しました');
  },
});

// task_working ステータス時のみボタン表示
{inquiry.status === 'task_working' && (
  <button onClick={() => generateMutation.mutate()}>
    ストーリー生成
  </button>
)}
```

### フィルタリング・ソートパターン

```typescript
const { data } = useQuery({
  queryKey: ['stories', { page, status, priority, sortBy, sortOrder }],
  queryFn: () => listStories({
    page,
    limit: 20,
    status,
    priority,
    sort_by: sortBy,      // created_at, updated_at, priority, estimated_effort
    sort_order: sortOrder, // asc, desc
  }),
});
```

## テストパターン

### AI生成サービスモック

```python
@pytest.fixture
def mock_openai():
    with patch.object(OpenAI, '__init__', return_value=None):
        with patch.object(OpenAI, 'chat') as mock_chat:
            mock_chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content=json.dumps({
                    "title": "生成タイトル",
                    "description": "生成説明",
                    "priority": "medium"
                })))]
            )
            yield mock_chat
```

### E2E統合テスト

```typescript
// StoryIntegration.test.tsx
test('問い合わせからストーリー生成', async () => {
  // 1. 問い合わせ詳細表示
  // 2. 承認してtask_workingに遷移
  // 3. ストーリー生成ボタンクリック
  // 4. ストーリー一覧に表示確認
});
```

## 実装状況

- ✅ StoryModel（SQLAlchemy ORM、inquiry_id外部キー）
- ✅ StoryStatus列挙型（WAITING_REVIEW/APPROVED/REJECTED）
- ✅ Priority列挙型（LOW/MEDIUM/HIGH/URGENT）
- ✅ Alembicマイグレーション（storiesテーブル、外部キー、インデックス）
- ✅ StoryValidator（入力検証・AI生成結果検証、95%カバレッジ）
- ✅ StoryRepository（CRUD・フィルタリング・ソート・ページネーション、86%カバレッジ）
- ✅ StoryQueryService（読み取り操作、100%カバレッジ）
- ✅ StoryWorkflowService（承認・却下・一括承認、100%カバレッジ）
- ✅ StoryGenerationService（OpenAI統合・リトライ・ロールバック、88%カバレッジ）
- ✅ Pydanticスキーマ（100%カバレッジ）
- ✅ API層（routers/story.py - 9エンドポイント完全実装）
- ✅ フロントエンド型定義（types/story.ts）
- ✅ フロントエンドAPIクライアント（services/storyApi.ts、82.45%カバレッジ）
- ✅ StoryListコンポーネント（95.83% statements）
- ✅ StoryFormコンポーネント（23テスト）
- ✅ StoryDetailコンポーネント（93.85% statements）
- ✅ StoryIntegration E2Eテスト（10テスト）

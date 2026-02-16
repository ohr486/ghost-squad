---
inclusion: always
updated_at: 2026-02-16
---

# Inquiry機能 開発ガイドライン

Inquiry（問い合わせ）機能は、ユーザーからの自然言語入力を受け付け、構造化されたストーリーへの変換を管理するコアサブシステムです。

## アーキテクチャパターン

### レイヤードアーキテクチャ

Inquiryは**API層 → サービス層 → リポジトリ層 → モデル層**の4層構造を採用。

```
API層 (routers/inquiry.py)
    │
    ├── InquiryQueryService（読み取り操作）
    │       └── InquiryRepository
    │
    └── InquiryWorkflowService（状態遷移操作）
            ├── InquiryValidator
            └── InquiryRepository
```

**設計意図**: 読み取り/書き込み操作の分離（CQRS的アプローチ）、ワークフローロジックの集約。

### ステータス遷移パターン

状態遷移は一方向で、ワークフローサービスが管理。

```
RECEIVED ──┬─→ TASK_WORKING ──→ PROCESSING ──→ COMPLETED
           │
           └─→ REJECTED
           │
           └─→ NEEDS_CLARIFICATION ──→ RECEIVED（将来実装）
```

**ビジネスルール**:
- 承認（approve）: `received` → `task_working`
- 却下（reject）: `received` → `rejected`（理由必須）
- AI変換開始: `task_working` → `processing`（StoryGenerationServiceで遷移）
- 完了: `processing` → `completed`（ストーリー生成完了時）

## コンポーネント構成

### バックエンド サービス層 (`services/`)

| ファイル | 役割 | 契約 |
|---------|------|------|
| `inquiry_validator.py` | 入力検証、エラーコード生成 | GS-1xxエラーコード体系 |
| `inquiry_repository.py` | CRUD操作、フィルタリング・ソート | トランザクション境界管理 |
| `inquiry_query_service.py` | 一覧取得、検索、ページネーション | 読み取り専用操作 |
| `inquiry_workflow_service.py` | 承認・却下、ステータス遷移 | 状態整合性保証 |

### スキーマ層 (`models/schemas/inquiry.py`)

APIリクエスト/レスポンス用Pydanticスキーマを提供。
- `CreateInquiryRequest` - 問い合わせ作成リクエスト
- `UpdateInquiryRequest` - 問い合わせ更新リクエスト
- `InquiryResponse` - 問い合わせレスポンス（ISO 8601 datetime）
- `RejectInquiryRequest` - 却下リクエスト（reason必須）
- `ErrorResponse` - エラーレスポンス（code, message, details）

### モデル層

| ファイル | 役割 |
|---------|------|
| `models/database/inquiry.py` | SQLAlchemy ORMモデル（InquiryModel） |
| `models/enums/inquiry_status.py` | InquiryStatus列挙型 |

### API層 (`routers/inquiry.py`)

| エンドポイント | メソッド | 概要 |
|---------------|----------|------|
| `/api/inquiries` | POST | 問い合わせ作成 |
| `/api/inquiries` | GET | 問い合わせ一覧（ページネーション・フィルタ・ソート） |
| `/api/inquiries/{id}` | GET | 問い合わせ詳細取得 |
| `/api/inquiries/{id}` | PUT | 問い合わせ更新 |
| `/api/inquiries/{id}/approve` | POST | 承認処理（received → task_working） |
| `/api/inquiries/{id}/reject` | POST | 却下処理（reason必須） |

### フロントエンド

| ファイル | 役割 | カバレッジ |
|---------|------|-----------|
| `types/inquiry.ts` | TypeScript型定義（バックエンドと整合） | - |
| `services/inquiryApi.ts` | APIクライアント（Axios） | 86.11% |
| `components/InquiryForm.tsx` | 問い合わせ入力フォーム | 100% statements |
| `components/InquiryList.tsx` | 一覧表示・フィルタ・ページネーション・メールインポート情報表示 | 84.21% statements |
| `components/InquiryDetail.tsx` | 詳細・編集・承認/却下 | 94.64% statements |

## エラーコード体系

| 範囲 | カテゴリ | 説明 |
|------|----------|------|
| GS-101〜GS-109 | 入力検証 | 必須フィールド、文字数、フォーマット等 |
| GS-110〜GS-119 | 状態遷移 | 無効なステータス遷移、重複操作等 |
| GS-120〜GS-129 | データアクセス | 存在しないID、更新競合等 |

## データモデル

### InquiryModel フィールド

```python
id: int                    # BigInteger、自動インクリメント
user_id: str               # ユーザー識別子
content: str               # 問い合わせ内容（必須）
language: str = "ja"       # 言語コード（デフォルト日本語）
timestamp: datetime        # 問い合わせ日時
status: InquiryStatus      # ステータス（列挙型）
inquiry_metadata: dict     # メタデータ（JSON）
created_at: datetime       # 作成日時（UTC）
updated_at: datetime       # 更新日時（UTC）
```

### inquiry_metadata 構造

```python
{
    "rejection": {
        "rejected_at": "2026-01-28T10:00:00Z",
        "reason": "却下理由"
    },
    "status_history": [
        {"from": "received", "to": "task_working", "at": "..."}
    ],
    "importer": { ... }  # Importer経由の場合
}
```

## フロントエンド実装パターン

### TanStack React Query 使用パターン

```typescript
// 一覧取得
const { data, isLoading, error } = useQuery({
  queryKey: ['inquiries', { page, status }],
  queryFn: () => listInquiries({ page, limit, status }),
});

// 承認 mutation
const approveMutation = useMutation({
  mutationFn: (id: number) => approveInquiry(id),
  onSuccess: () => queryClient.invalidateQueries(['inquiries']),
});
```

### React Hook Form + Zod パターン

```typescript
const schema = z.object({
  content: z.string().min(1, '内容は必須です').max(10000),
  user_id: z.string().min(1, 'ユーザーIDは必須です'),
});

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(schema),
});
```

## Importer連携パターン

InquiryListでは、メールインポート経由の問い合わせに対してメタデータを表示する。

```typescript
// InquiryList.tsx - メールインポート判定パターン
const isEmailImport = (inquiry: InquiryResponse): boolean => {
  return (
    inquiry.source_system === "importer:email" ||
    inquiry.inquiry_metadata?.importer?.source_type === "email"
  );
};

// タイトル・送信者列を条件付き表示
{isEmailImport(inquiry) ? (
  <span>{inquiry.inquiry_metadata?.importer?.original_subject}</span>
) : (
  <span className="text-gray-400">-</span>
)}
```

**型定義**: `types/inquiry.ts`の`ImporterMetadata`インターフェースで`InquiryMetadata.importer`フィールドを型安全に参照。

## テストパターン

### バックエンド

```python
# リポジトリテストフィクスチャ
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

# ワークフローサービステスト
def test_approve_inquiry(db_session):
    repo = InquiryRepository(db_session)
    service = InquiryWorkflowService(repo, InquiryValidator())
    # テストロジック
```

### フロントエンド

```typescript
// MSWモック + Testing Library
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('問い合わせ送信成功', async () => {
  render(<InquiryForm />);
  await userEvent.type(screen.getByLabelText('内容'), 'テスト内容');
  await userEvent.click(screen.getByRole('button', { name: '送信' }));
  await waitFor(() => expect(screen.getByText('送信しました')).toBeInTheDocument());
});
```

## 実装状況

- ✅ InquiryModel（SQLAlchemy ORM、BigInteger ID）
- ✅ InquiryStatus列挙型（RECEIVED/TASK_WORKING/PROCESSING/COMPLETED/REJECTED/NEEDS_CLARIFICATION）
- ✅ Alembicマイグレーション（inquiriesテーブル）
- ✅ InquiryValidator（入力検証、97%カバレッジ）
- ✅ InquiryRepository（CRUD・フィルタリング・ソート・ページネーション、90%カバレッジ）
- ✅ InquiryQueryService（読み取り操作、100%カバレッジ）
- ✅ InquiryWorkflowService（承認・却下・ステータス遷移、89%カバレッジ）
- ✅ Pydanticスキーマ（CreateInquiryRequest、UpdateInquiryRequest、InquiryResponse）
- ✅ API層（routers/inquiry.py - 6エンドポイント完全実装）
- ✅ E2Eフローテスト（test_e2e_inquiry_flow.py）
- ✅ フロントエンド型定義（types/inquiry.ts）
- ✅ フロントエンドAPIクライアント（services/inquiryApi.ts、86.11%カバレッジ）
- ✅ InquiryFormコンポーネント（100% statements、94.28% branches）
- ✅ InquiryListコンポーネント（84.21% statements）
- ✅ InquiryDetailコンポーネント（94.64% statements、86.36% branches）

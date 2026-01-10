# Ghost Squad API仕様

Ghost SquadのREST API仕様とエンドポイント詳細を記載します。

## 概要

Ghost Squad APIは、自然言語での問い合わせを構造化されたユーザーストーリーに変換するためのRESTful APIを提供します。

**API文書の確認**
- 開発サーバー起動時: http://localhost:8000/docs (OpenAPI/Swagger UI)
- バックエンドAPI: http://localhost:8000

## 現在実装済みのエンドポイント

### 問い合わせ管理API

#### `POST /api/inquiries`
問い合わせを作成します。

**リクエスト例**
```json
{
  "user_id": "user123",
  "content": "ユーザーがログインできる機能が欲しい",
  "source_system": "manual"
}
```

**レスポンス例**
```json
{
  "id": 1,
  "user_id": "user123",
  "content": "ユーザーがログインできる機能が欲しい",
  "source_system": "manual",
  "status": "received",
  "timestamp": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "inquiry_metadata": {}
}
```

#### `GET /api/inquiries`
問い合わせ一覧を取得します（ページネーション・フィルタリング対応）。

**クエリパラメータ**
- `page`: ページ番号（デフォルト: 1）
- `limit`: 1ページあたりの件数（デフォルト: 20）
- `status`: ステータスフィルタ（オプション）
- `user_id`: ユーザーIDフィルタ（オプション）

**レスポンス例**
```json
{
  "data": [
    {
      "id": 1,
      "user_id": "user123",
      "content": "ユーザーがログインできる機能が欲しい",
      "source_system": "manual",
      "status": "received",
      "timestamp": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "inquiry_metadata": {}
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "has_next": true
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### `GET /api/inquiries/{id}`
特定の問い合わせを取得します。

**パスパラメータ**
- `id`: 問い合わせID

**レスポンス例**
```json
{
  "id": 1,
  "user_id": "user123",
  "content": "ユーザーがログインできる機能が欲しい",
  "source_system": "manual",
  "status": "received",
  "timestamp": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "inquiry_metadata": {}
}
```

#### `PUT /api/inquiries/{id}`
問い合わせを更新します。

**パスパラメータ**
- `id`: 問い合わせID

**リクエスト例**
```json
{
  "content": "更新された問い合わせ内容",
  "source_system": "email"
}
```

**レスポンス例**
```json
{
  "id": 1,
  "user_id": "user123",
  "content": "更新された問い合わせ内容",
  "source_system": "email",
  "status": "received",
  "timestamp": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:10:00Z",
  "inquiry_metadata": {}
}
```

#### `POST /api/inquiries/{id}/approve`
問い合わせを承認します（ステータスを`processing`に変更）。

**パスパラメータ**
- `id`: 問い合わせID

**リクエストボディ**
なし

**レスポンス例**
```json
{
  "id": 1,
  "user_id": "user123",
  "content": "ユーザーがログインできる機能が欲しい",
  "source_system": "manual",
  "status": "processing",
  "timestamp": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z",
  "inquiry_metadata": {
    "approved_at": "2024-01-01T00:05:00Z"
  }
}
```

#### `POST /api/inquiries/{id}/reject`
問い合わせを却下します（ステータスを`failed`に変更）。

**パスパラメータ**
- `id`: 問い合わせID

**リクエスト例**
```json
{
  "reason": "要件が不明確です"
}
```

**レスポンス例**
```json
{
  "id": 1,
  "user_id": "user123",
  "content": "ユーザーがログインできる機能が欲しい",
  "source_system": "manual",
  "status": "failed",
  "timestamp": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z",
  "inquiry_metadata": {
    "rejected_at": "2024-01-01T00:05:00Z",
    "rejection_reason": "要件が不明確です"
  }
}
```

#### `POST /api/inquiries/{id}/request-clarification`
問い合わせに明確化を要求します（ステータスを`needs_clarification`に変更）。

**パスパラメータ**
- `id`: 問い合わせID

**リクエスト例**
```json
{
  "reason": "具体的なユースケースを教えてください"
}
```

**レスポンス例**
```json
{
  "id": 1,
  "user_id": "user123",
  "content": "ユーザーがログインできる機能が欲しい",
  "source_system": "manual",
  "status": "needs_clarification",
  "timestamp": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z",
  "inquiry_metadata": {
    "clarification_requested_at": "2024-01-01T00:05:00Z",
    "clarification_reason": "具体的なユースケースを教えてください"
  }
}
```

#### `POST /api/inquiries/{id}/complete-clarification`
明確化を完了してreceivedステータスに戻します。

**パスパラメータ**
- `id`: 問い合わせID

**リクエストボディ**
なし

**レスポンス例**
```json
{
  "id": 1,
  "user_id": "user123",
  "content": "ユーザーがログインできる機能が欲しい",
  "source_system": "manual",
  "status": "received",
  "timestamp": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:10:00Z",
  "inquiry_metadata": {
    "clarification_requested_at": "2024-01-01T00:05:00Z",
    "clarification_reason": "具体的なユースケースを教えてください",
    "clarification_completed_at": "2024-01-01T00:10:00Z"
  }
}
```

### システム情報API

#### `GET /api/info`
API情報を取得します。

**レスポンス例**
```json
{
  "name": "Ghost Squad API",
  "version": "1.0.0",
  "status": "running"
}
```

#### `GET /api/db-test`
データベース接続をテストします。

**レスポンス例**
```json
{
  "status": "ok",
  "database": "connected"
}
```

#### `GET /health`
ヘルスチェックエンドポイント。

**レスポンス例**
```json
{
  "status": "healthy"
}
```

### ストーリー管理API

#### `POST /api/inquiries/{id}/generate-stories`
問い合わせからAIを使用してストーリーを生成します。

**パスパラメータ**
- `id`: 問い合わせID

**リクエスト例**
```json
{
  "template_id": 1,
  "options": {
    "detailed": true
  }
}
```

**レスポンス例**
```json
{
  "id": 1,
  "inquiry_id": 1,
  "title": "ユーザーログイン機能",
  "description": "As a user, I want to login so that I can access my account",
  "category": "development",
  "priority": "high",
  "status": "waiting_review",
  "estimated_effort": 5.0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### `GET /api/stories`
ストーリー一覧を取得します。

**クエリパラメータ**
- `page`: ページ番号（デフォルト: 1）
- `limit`: 1ページあたりの件数（デフォルト: 20）
- `status`: ステータスフィルタ（オプション）
- `priority`: 優先度フィルタ（オプション）
- `category`: カテゴリフィルタ（オプション）

**レスポンス例**
```json
{
  "data": [
    {
      "id": 1,
      "inquiry_id": 1,
      "title": "ユーザーログイン機能",
      "description": "As a user, I want to login so that I can access my account",
      "category": "development",
      "priority": "high",
      "status": "waiting_review",
      "estimated_effort": 5.0,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "has_next": true
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### `GET /api/stories/{id}`
特定のストーリーを取得します。

**パスパラメータ**
- `id`: ストーリーID

**レスポンス例**
```json
{
  "id": 1,
  "inquiry_id": 1,
  "title": "ユーザーログイン機能",
  "description": "As a user, I want to login so that I can access my account",
  "category": "development",
  "priority": "high",
  "status": "waiting_review",
  "estimated_effort": 5.0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### `PUT /api/stories/{id}`
ストーリーを更新します。

**パスパラメータ**
- `id`: ストーリーID

**リクエスト例**
```json
{
  "title": "ユーザーログイン機能",
  "description": "As a user, I want to login so that I can access my account",
  "priority": "high",
  "estimated_effort": 5
}
```

**レスポンス例**
```json
{
  "id": 1,
  "inquiry_id": 1,
  "title": "ユーザーログイン機能",
  "description": "As a user, I want to login so that I can access my account",
  "category": "development",
  "priority": "high",
  "status": "waiting_review",
  "estimated_effort": 5.0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z"
}
```

#### `POST /api/stories/{id}/approve`
ストーリーを承認します（ステータスを`approved`に変更）。

**パスパラメータ**
- `id`: ストーリーID

**リクエストボディ**
なし

**レスポンス例**
```json
{
  "id": 1,
  "inquiry_id": 1,
  "title": "ユーザーログイン機能",
  "description": "As a user, I want to login so that I can access my account",
  "category": "development",
  "priority": "high",
  "status": "approved",
  "estimated_effort": 5.0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:10:00Z"
}
```

#### `POST /api/stories/{id}/reject`
ストーリーを却下します（ステータスを`rejected`に変更）。

**パスパラメータ**
- `id`: ストーリーID

**リクエスト例**
```json
{
  "reason": "要件が不明確です"
}
```

**レスポンス例**
```json
{
  "id": 1,
  "inquiry_id": 1,
  "title": "ユーザーログイン機能",
  "description": "As a user, I want to login so that I can access my account",
  "category": "development",
  "priority": "high",
  "status": "rejected",
  "estimated_effort": 5.0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:10:00Z",
  "story_metadata": {
    "rejected_at": "2024-01-01T00:10:00Z",
    "rejection_reason": "要件が不明確です"
  }
}
```

## 将来のAPI拡張

Ghost Squadの機能拡張に伴い、以下のAPIエンドポイントが追加予定です：

### テンプレート管理API
- `GET /api/templates` - テンプレート一覧
- `POST /api/templates` - カスタムテンプレート作成
- `GET /api/templates/{id}` - テンプレート詳細
- `PUT /api/templates/{id}` - テンプレート更新

### 分析API
- `GET /api/analytics/stories` - ストーリー分析
- `GET /api/analytics/predictions` - プロジェクト進捗予測
- `GET /api/analytics/productivity` - チーム生産性分析

### 一括操作API
- `POST /api/stories/batch` - ストーリー一括操作（承認・拒否）
- `POST /api/inquiries/batch` - 問い合わせ一括操作

## レスポンス標準化

すべてのAPIレスポンスは以下の標準形式に従います：

### 成功レスポンス
```json
{
  "data": {},           // 実際のデータ
  "meta": {             // メタデータ（ページネーション時）
    "page": 1,
    "limit": 20,
    "total": 100,
    "has_next": true
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### エラーレスポンス
```json
{
  "errors": [
    {
      "code": "GS-001",
      "message": "問い合わせが見つかりません",
      "field": "id",
      "details": "ID 123 の問い合わせは存在しません"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## HTTPステータスコード

Ghost Squad APIは以下のHTTPステータスコードを使用します：

- **200 OK** - リクエスト成功
- **201 Created** - リソース作成成功
- **400 Bad Request** - リクエストパラメータエラー
- **401 Unauthorized** - 認証エラー
- **403 Forbidden** - 権限エラー
- **404 Not Found** - リソースが見つからない
- **422 Unprocessable Entity** - バリデーションエラー
- **500 Internal Server Error** - サーバーエラー
- **503 Service Unavailable** - サービス利用不可（メンテナンス等）

## エラーコード体系

エラーコードは `GS-XXX` 形式で定義されています：

- **GS-001 ~ GS-099**: 問い合わせ関連エラー
- **GS-100 ~ GS-199**: ストーリー関連エラー
- **GS-200 ~ GS-299**: テンプレート関連エラー
- **GS-400 ~ GS-499**: 認証・認可エラー
- **GS-500 ~ GS-599**: AI統合エラー
- **GS-900 ~ GS-999**: システムエラー

## API使用例

### cURLでの問い合わせ作成
```bash
curl -X POST http://localhost:8000/api/inquiries \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "content": "ユーザーがログインできる機能が欲しい",
    "language": "ja"
  }'
```

### Pythonでの問い合わせ一覧取得
```python
import requests

response = requests.get(
    "http://localhost:8000/api/inquiries",
    params={"page": 1, "limit": 20}
)
data = response.json()
print(data)
```

### TypeScript/Axiosでの問い合わせ取得
```typescript
import axios from 'axios';

const response = await axios.get(
  `http://localhost:8000/api/inquiries/${inquiryId}`
);
console.log(response.data);
```

## トラブルシューティング

### OpenAI APIエラー

**問題**: AI機能使用時にエラーが発生する

**解決方法**:
1. `.env`ファイルの`OPENAI_API_KEY`が正しく設定されているか確認
2. APIキーの使用制限・残高を確認
3. OpenAIのステータスページを確認: https://status.openai.com/

```bash
# 環境変数の確認
cat .env | grep OPENAI_API_KEY

# サーバーログでエラー詳細を確認
make logs-backend
```

### CORS エラー

**問題**: フロントエンドからAPIへのアクセス時にCORSエラーが発生

**解決方法**:
1. `.env`ファイルの`CORS_ORIGINS`設定を確認
2. フロントエンドのURLが含まれているか確認

```bash
# .envファイルに以下を追加
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# サーバー再起動
make restart
```

### APIレスポンスが遅い

**問題**: APIのレスポンスが遅い

**解決方法**:
1. データベース接続を確認
2. ログでクエリパフォーマンスを確認
3. AI API呼び出しのタイムアウト設定を確認

```bash
# データベースの状態確認
make db-status

# ログでボトルネックを特定
make logs-backend | grep -i "slow\|timeout"
```

## セキュリティ

### API認証（将来実装予定）

JWT（JSON Web Token）を使用した認証を実装予定です：

```bash
# ログイン
POST /api/auth/login
{
  "username": "user123",
  "password": "password"
}

# レスポンス
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}

# 認証が必要なエンドポイント
GET /api/inquiries
Authorization: Bearer eyJhbGc...
```

### レート制限（将来実装予定）

API使用量を制限するレート制限を実装予定です：

- **制限**: 100リクエスト/分/ユーザー
- **AI API**: 10リクエスト/分/ユーザー
- **レスポンスヘッダー**:
  - `X-RateLimit-Limit`: 制限値
  - `X-RateLimit-Remaining`: 残りリクエスト数
  - `X-RateLimit-Reset`: リセット時刻

## 関連ドキュメント

- [データベース管理ガイド](DATABASE.md)
- [Spec-Driven Development](SDD.md)
- [README](../README.md)

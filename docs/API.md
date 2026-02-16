# Ghost Squad API仕様

Ghost SquadのREST API仕様とエンドポイント詳細を記載します。

## 概要

Ghost Squad APIは、自然言語での問い合わせを構造化されたユーザーストーリーに変換するためのRESTful APIを提供します。

**API文書の確認**
- 開発サーバー起動時: http://localhost:8000/docs (OpenAPI/Swagger UI)
- バックエンドAPI: http://localhost:8000

## システムエンドポイント

### `GET /`
ルートエンドポイント。API情報を取得します。

**レスポンス例**
```json
{
  "name": "Ghost Squad API",
  "version": "0.1.0",
  "description": "AI-Driven Task Management Platform"
}
```

### `GET /health`
ヘルスチェックエンドポイント。

**レスポンス例**
```json
{
  "status": "healthy"
}
```

## 問い合わせ管理API

### `POST /api/inquiries`
問い合わせを作成します。

**リクエスト例**
```json
{
  "user_id": "user123",
  "content": "ユーザーがログインできる機能が欲しい",
  "source_system": "manual"
}
```

**レスポンス例** (201 Created)
```json
{
  "id": 1,
  "user_id": "user123",
  "content": "ユーザーがログインできる機能が欲しい",
  "source_system": "manual",
  "status": "received",
  "timestamp": "2026-01-01T00:00:00Z",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "inquiry_metadata": {}
}
```

### `GET /api/inquiries`
問い合わせ一覧を取得します（ページネーション・フィルタリング・ソート対応）。

**クエリパラメータ**
| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `page` | int | 1 | ページ番号（1以上） |
| `limit` | int | 20 | 1ページあたりの件数（1〜100） |
| `status` | string | - | ステータスフィルタ（カンマ区切りで複数指定可） |
| `user_id` | string | - | ユーザーIDフィルタ |
| `sort_by` | string | created_at | ソートフィールド（created_at, updated_at） |
| `sort_order` | string | desc | ソート順（asc, desc） |

**レスポンス例** (200 OK)
```json
{
  "data": [
    {
      "id": 1,
      "user_id": "user123",
      "content": "ユーザーがログインできる機能が欲しい",
      "source_system": "manual",
      "status": "received",
      "timestamp": "2026-01-01T00:00:00Z",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z",
      "inquiry_metadata": {}
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "has_next": true
  },
  "timestamp": "2026-01-01T00:00:00Z"
}
```

### `GET /api/inquiries/{inquiry_id}`
特定の問い合わせを取得します。

**パスパラメータ**
- `inquiry_id`: 問い合わせID

**レスポンス**: `InquiryResponse`（200 OK）または `ErrorResponse`（404）

### `PUT /api/inquiries/{inquiry_id}`
問い合わせを更新します。

**パスパラメータ**
- `inquiry_id`: 問い合わせID

**リクエスト例**（全フィールドオプション）
```json
{
  "content": "更新された問い合わせ内容",
  "source_system": "email"
}
```

**レスポンス**: `InquiryResponse`（200 OK）または `ErrorResponse`（400, 404）

### `POST /api/inquiries/{inquiry_id}/approve`
問い合わせを承認します（ステータスを `received` → `task_working` に変更）。

**パスパラメータ**
- `inquiry_id`: 問い合わせID

**リクエストボディ**: なし

**レスポンス例** (200 OK)
```json
{
  "id": 1,
  "user_id": "user123",
  "content": "ユーザーがログインできる機能が欲しい",
  "source_system": "manual",
  "status": "task_working",
  "timestamp": "2026-01-01T00:00:00Z",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:05:00Z",
  "inquiry_metadata": {
    "status_history": [
      {"from": "received", "to": "task_working", "at": "2026-01-01T00:05:00Z"}
    ]
  }
}
```

**エラー**: 409 Conflict（ステータスが `received` 以外の場合）

### `POST /api/inquiries/{inquiry_id}/reject`
問い合わせを却下します（ステータスを `received` → `rejected` に変更）。

**パスパラメータ**
- `inquiry_id`: 問い合わせID

**リクエスト例**
```json
{
  "reason": "要件が不明確です"
}
```

**レスポンス例** (200 OK)
```json
{
  "id": 1,
  "status": "rejected",
  "inquiry_metadata": {
    "rejection": {
      "rejected_at": "2026-01-01T00:05:00Z",
      "reason": "要件が不明確です"
    }
  }
}
```

**エラー**: 409 Conflict（ステータスが `received` 以外の場合）

### `POST /api/inquiries/{inquiry_id}/request-clarification`
問い合わせに明確化を要求します（ステータスを `received` → `needs_clarification` に変更）。

**リクエスト例**
```json
{
  "reason": "具体的なユースケースを教えてください"
}
```

### `POST /api/inquiries/{inquiry_id}/complete-clarification`
明確化を完了して `received` ステータスに戻します。

**リクエストボディ**: なし

## ストーリー管理API

### `POST /api/inquiries/{inquiry_id}/stories`
ストーリーを作成します。リクエストボディが空の場合はAI自動生成、ボディがある場合は手動作成となります。

**パスパラメータ**
- `inquiry_id`: 問い合わせID

**リクエスト例（手動作成）**
```json
{
  "title": "ユーザーログイン機能",
  "description": "As a user, I want to login so that I can access my account",
  "priority": "high",
  "estimated_effort": 5.0,
  "deadline": "2026-03-01T00:00:00Z",
  "assignee": "dev01"
}
```

**リクエスト例（AI自動生成）**
```json
{}
```

**レスポンス例** (201 Created)
```json
{
  "id": 1,
  "inquiry_id": 1,
  "title": "ユーザーログイン機能",
  "description": "As a user, I want to login so that I can access my account",
  "priority": "high",
  "status": "waiting_review",
  "estimated_effort": 5.0,
  "deadline": "2026-03-01T00:00:00Z",
  "assignee": "dev01",
  "story_metadata": {},
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**エラー**: 400（バリデーション）, 404（問い合わせ不在）, 422（AI生成時のInquiryステータス不正）

### `GET /api/stories`
ストーリー一覧を取得します。

**クエリパラメータ**
| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `page` | int | 1 | ページ番号 |
| `limit` | int | 20 | 1ページあたりの件数（1〜100） |
| `status` | StoryStatus | - | ステータスフィルタ（waiting_review, approved, rejected） |
| `priority` | Priority | - | 優先度フィルタ（low, medium, high, urgent） |
| `inquiry_id` | int | - | 問い合わせIDフィルタ |
| `sort_by` | string | created_at | ソートフィールド（created_at, updated_at, priority, estimated_effort, assignee, deadline） |
| `sort_order` | string | desc | ソート順（asc, desc） |

**レスポンス**: `PaginatedStoriesResponse`

### `GET /api/inquiries/{inquiry_id}/stories`
特定の問い合わせに紐づくストーリー一覧を取得します。

**パスパラメータ**
- `inquiry_id`: 問い合わせID

**クエリパラメータ**: `GET /api/stories` と同様（inquiry_idは自動設定）

### `GET /api/stories/{id}`
特定のストーリーを取得します。

**レスポンス**: `StoryResponse`（200 OK）または `ErrorResponse`（404）

### `PUT /api/stories/{id}`
ストーリーを更新します（全フィールドオプション）。

**リクエスト例**
```json
{
  "title": "ユーザーログイン機能（改訂版）",
  "priority": "urgent",
  "estimated_effort": 8.0,
  "assignee": "dev02"
}
```

### `DELETE /api/stories/{id}`
ストーリーを削除します。

**レスポンス例** (200 OK)
```json
{
  "success": true
}
```

### `POST /api/stories/{id}/approve`
ストーリーを承認します（ステータスを `waiting_review` → `approved` に変更）。

**リクエスト例**
```json
{
  "approver": "pm01"
}
```

**レスポンス**: `StoryResponse`（200 OK）

**エラー**: 422（ステータスが `waiting_review` 以外の場合）

### `POST /api/stories/{id}/reject`
ストーリーを却下します（ステータスを `waiting_review` → `rejected` に変更）。

**リクエスト例**
```json
{
  "rejector": "pm01",
  "reason": "要件が不明確です"
}
```

**レスポンス**: `StoryResponse`（200 OK）

**エラー**: 422（ステータスが `waiting_review` 以外、または理由未指定の場合）

### `POST /api/stories/batch-approve`
複数のストーリーを一括承認します。

**リクエスト例**
```json
{
  "story_ids": [1, 2, 3],
  "approver": "pm01"
}
```

**レスポンス例** (200 OK)
```json
{
  "results": [
    {"id": 1, "success": true, "error": null},
    {"id": 2, "success": true, "error": null},
    {"id": 3, "success": false, "error": "ストーリーが見つかりません"}
  ]
}
```

## インポーターAPI

外部データソースから問い合わせを自動取り込みするためのAPIです。

### `GET /api/plugins`
登録済みのデータソースプラグイン一覧を取得します。

**レスポンス例** (200 OK)
```json
{
  "data": [
    {
      "plugin_type": "email",
      "enabled": true,
      "initialized": true,
      "error_message": null
    }
  ],
  "timestamp": "2026-01-01T00:00:00Z"
}
```

### `POST /api/plugins/{plugin_type}/enable`
プラグインを有効化します。

**パスパラメータ**
- `plugin_type`: プラグイン種別（例: `email`）

**レスポンス**: `PluginStatusResponse`

### `POST /api/plugins/{plugin_type}/disable`
プラグインを無効化します。

### `GET /api/ai-providers`
登録済みのAIプロバイダー一覧を取得します。

**レスポンス例** (200 OK)
```json
{
  "data": [
    {
      "provider_type": "openai",
      "enabled": true,
      "initialized": true,
      "is_default": true,
      "model": "gpt-4",
      "error_message": null
    },
    {
      "provider_type": "anthropic",
      "enabled": false,
      "initialized": false,
      "is_default": false,
      "model": "claude-3-sonnet-20240229",
      "error_message": null
    }
  ],
  "timestamp": "2026-01-01T00:00:00Z"
}
```

### `POST /api/ai-providers/{provider_type}/set-default`
デフォルトのAIプロバイダーを設定します。

**パスパラメータ**
- `provider_type`: プロバイダー種別（`openai`, `anthropic`）

### `POST /api/importers/execute`
インポートを実行します。

**リクエスト例**
```json
{
  "plugin_type": "email",
  "ai_provider_type": "openai"
}
```

**レスポンス例** (200 OK)
```json
{
  "total_fetched": 5,
  "total_imported": 3,
  "total_skipped": 1,
  "total_failed": 1,
  "imported_inquiry_ids": [10, 11, 12],
  "errors": [
    {
      "source_id": "msg-123",
      "error_code": "GS-304",
      "error_message": "AI解析に失敗しました"
    }
  ],
  "timestamp": "2026-01-01T00:00:00Z"
}
```

### `POST /api/importers/retry`
失敗したインポートをリトライします。

**リクエスト例**
```json
{
  "plugin_type": "email",
  "source_ids": ["msg-123", "msg-456"],
  "ai_provider_type": "openai"
}
```

### `GET /api/importers/stats`
エラー統計を取得します。

**クエリパラメータ**
- `plugin_type`（オプション）: プラグイン種別でフィルタ

**レスポンス例** (200 OK)
```json
{
  "data": [
    {
      "error_code": "GS-304",
      "count": 3,
      "last_occurred": "2026-01-01T10:00:00Z"
    }
  ],
  "timestamp": "2026-01-01T00:00:00Z"
}
```

## レスポンス標準化

### 成功レスポンス（一覧取得時）
```json
{
  "data": [],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "has_next": true
  },
  "timestamp": "2026-01-01T00:00:00Z"
}
```

### エラーレスポンス
```json
{
  "errors": [
    {
      "code": "GS-001",
      "message": "問い合わせが見つかりません",
      "field": "id"
    }
  ],
  "timestamp": "2026-01-01T00:00:00Z"
}
```

## HTTPステータスコード

- **200 OK** - リクエスト成功
- **201 Created** - リソース作成成功
- **400 Bad Request** - リクエストパラメータエラー
- **404 Not Found** - リソースが見つからない
- **409 Conflict** - ステータス遷移の競合
- **422 Unprocessable Entity** - バリデーションエラー
- **500 Internal Server Error** - サーバーエラー

## エラーコード体系

エラーコードは `GS-XXX` 形式で定義されています：

| 範囲 | カテゴリ | 説明 |
|------|----------|------|
| GS-001〜GS-011 | 問い合わせ | 入力検証、状態遷移、データアクセス |
| GS-101〜GS-129 | 問い合わせ詳細 | 必須フィールド、文字数、フォーマット、ステータス遷移 |
| GS-201〜GS-219 | ストーリー | 入力検証、状態遷移、AI生成、ワークフロー |
| GS-301〜GS-309 | インポーター管理 | プラグイン未検出、初期化失敗 |
| GS-310〜GS-319 | メール設定 | 必須フィールド、ポート範囲 |
| GS-320〜GS-329 | メール接続 | IMAP接続、認証 |
| GS-999 | システム | 汎用サーバーエラー |

## API使用例

### cURLでの問い合わせ作成
```bash
curl -X POST http://localhost:8000/api/inquiries \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "content": "ユーザーがログインできる機能が欲しい",
    "source_system": "manual"
  }'
```

### cURLでのストーリーAI自動生成
```bash
curl -X POST http://localhost:8000/api/inquiries/1/stories \
  -H "Content-Type: application/json" \
  -d '{}'
```

### cURLでのインポート実行
```bash
curl -X POST http://localhost:8000/api/importers/execute \
  -H "Content-Type: application/json" \
  -d '{"plugin_type": "email"}'
```

## 将来のAPI拡張

- `GET /api/templates` - テンプレート一覧
- `POST /api/templates` - カスタムテンプレート作成
- `POST /api/auth/login` - JWT認証
- `GET /api/analytics/stories` - ストーリー分析

## 関連ドキュメント

- [データベース管理ガイド](DATABASE.md)
- [開発コマンドリファレンス](COMMAND.md)
- [トラブルシューティング](DEBUG.md)
- [Spec-Driven Development](SDD.md)
- [README](../README.md)

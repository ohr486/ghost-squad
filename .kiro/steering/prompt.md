---
inclusion: always
updated_at: 2026-02-26
---

# Prompt管理機能 開発ガイドライン

Prompt管理機能は、AIプロンプトの一元管理・編集・テスト実行を提供するサブシステムです。従来ハードコードされていたプロンプトをDB管理化し、WebUI経由で編集可能にします。

## アーキテクチャパターン

### レイヤードアーキテクチャ + キャッシュ層

Promptは**API層 → サービス層 → キャッシュ層 → リポジトリ層 → モデル層**の構造を採用。

```
API層 (routers/prompt.py)
    │
    └── PromptService（統括サービス）
            ├── PromptCache（TTLキャッシュ、DBフォールバック）
            ├── PromptValidator（入力検証）
            ├── PromptRepository（CRUD操作）
            └── AIProviderRegistry（テスト実行）
```

**設計意図**: キャッシュ層によるDB負荷軽減、プレースホルダー検証による安全なテンプレート管理。

### 新規パターン

**TTLキャッシュ + DBフォールバック** (`prompt_cache.py`)
- 60秒TTLのインメモリキャッシュ
- DB障害時はTTL期限切れエントリをフォールバックとして返却（graceful degradation）
- `time.monotonic()`でTTL計測（システム時計変更の影響を受けない）

**編集ロック** (`prompt_service.py`)
- 楽観的排他制御パターン（editing_by + editing_since）
- 30分タイムアウトで自動解放
- GS-405エラーコードで競合検出

**デュアルコンテンツトラッキング**
- `content`: 現在のプロンプト内容（編集可能）
- `default_content`: システムデフォルト（不変、リセット用）
- `is_modified`: content != default_content を自動追跡

**シーダーパターン** (`prompt_seeder.py`)
- アプリ起動時にデフォルトプロンプトを自動投入
- 冪等性保証（既存レコードを上書きしない）
- `main.py`のlifespanで実行

## コンポーネント構成

### バックエンド サービス層 (`services/`)

| ファイル | 役割 | 契約 |
|---------|------|------|
| `prompt_service.py` | 統括サービス（CRUD、テスト実行、編集ロック） | キャッシュ→DB→フォールバック |
| `prompt_validator.py` | 入力検証（内容、プレースホルダー構文、カテゴリ） | GS-4xxエラーコード体系 |
| `prompt_repository.py` | CRUD操作、編集ロック管理 | トランザクション境界管理 |
| `prompt_cache.py` | TTLキャッシュ、DBフォールバック | 60秒TTL |
| `prompt_seeder.py` | デフォルトプロンプト投入 | 冪等性保証 |
| `prompt_defaults.py` | システムデフォルト定義 | 3種のデフォルトプロンプト |

### API層 (`routers/prompt.py`)

| エンドポイント | メソッド | 概要 |
|---------------|----------|------|
| `/api/prompts` | GET | プロンプト一覧（カテゴリフィルタ） |
| `/api/prompts/{key}` | GET | プロンプト詳細取得 |
| `/api/prompts/{key}` | PUT | プロンプト内容更新 |
| `/api/prompts/{key}/reset` | POST | デフォルトにリセット |
| `/api/prompts/{key}/lock` | POST | 編集ロック取得 |
| `/api/prompts/{key}/lock` | DELETE | 編集ロック解放 |
| `/api/prompts/test` | POST | AIプロバイダーでテスト実行 |

### フロントエンド

| ファイル | 役割 |
|---------|------|
| `types/prompt.ts` | TypeScript型定義（バックエンドと整合） |
| `services/promptApi.ts` | APIクライアント（Axios） |
| `components/PromptList.tsx` | 一覧表示・カテゴリフィルタ |
| `components/PromptDetail.tsx` | 詳細・編集・テスト実行・リセット |

## エラーコード体系

| 範囲 | カテゴリ | 説明 |
|------|----------|------|
| GS-401 | 入力検証 | プロンプト内容が空 |
| GS-402 | 入力検証 | プレースホルダー構文エラー |
| GS-403 | 入力検証 | 無効なカテゴリ |
| GS-404 | データアクセス | プロンプト未検出 |
| GS-405 | 排他制御 | 編集ロック競合 |
| GS-406 | テスト実行 | タイムアウト（30秒） |
| GS-407 | テスト実行 | AIプロバイダー利用不可 |

## データモデル

### PromptModel フィールド

```python
id: int                    # BigInteger、自動インクリメント
key: str                   # 一意キー（100文字、ユニーク索引）
name: str                  # 表示名（200文字）
description: str           # 説明（オプション）
category: PromptCategory   # カテゴリ（story_generation/import_analysis/general）
content: str               # 現在のプロンプト内容（編集可能）
default_content: str       # システムデフォルト（不変）
variables: list            # プレースホルダー変数リスト（JSON）
is_modified: bool          # 編集済みフラグ（自動計算）
editing_by: str            # 編集中ユーザーID（オプション）
editing_since: datetime    # 編集ロック取得日時（オプション）
created_at: datetime       # 作成日時
updated_at: datetime       # 更新日時
```

### デフォルトプロンプト

| キー | カテゴリ | 用途 |
|------|----------|------|
| `story_generation_system` | story_generation | ストーリー生成システムロール |
| `story_generation_user` | story_generation | ストーリー生成ユーザーテンプレート |
| `import_analysis_system` | import_analysis | インポート解析システムロール |

## テスト実行パターン

```python
# プレースホルダー置換 → AIプロバイダー呼び出し
POST /api/prompts/test
{
  "content": "問い合わせ内容：{inquiry_content}\nストーリーを生成してください。",
  "variables": {"inquiry_content": "ログイン機能を実装したい"},
  "provider": "openai"  # オプション（デフォルトはレジストリのデフォルト）
}
```

- `ThreadPoolExecutor`による30秒タイムアウト付き実行
- 結果にprovider名、model名、elapsed_msを含む

## 実装状況

- `.kiro/specs/prompt-management/` - Phase: tasks-generated（全承認済み）
- バックエンド: 全サービス層・API層実装完了（225テスト）
- フロントエンド: 型定義・APIクライアント・コンポーネント実装完了
- App.tsx: 「プロンプト管理」タブ統合済み

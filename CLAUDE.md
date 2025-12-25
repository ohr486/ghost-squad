# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

Ghost Squadは、自然言語での問い合わせを構造化されたユーザーストーリーに変換し、カンバンシステムと統合するAI駆動のタスク管理ツールです。OpenAI APIを使用してAI駆動のストーリー生成を行います。

**技術スタック:**
- バックエンド: Python FastAPI + SQLAlchemy ORM + Alembic マイグレーション
- フロントエンド: React TypeScript + TailwindCSS
- データベース: PostgreSQL
- AI: OpenAI API
- コンテナ化: Docker Compose

## 開発コマンド

### 環境セットアップ
```bash
make setup          # 初期環境構築（コンテナビルド、マイグレーション実行、データシード）
make dev            # 開発サーバーをバックグラウンドで起動
make stop           # 全サービスを停止
make restart        # 全サービスを再起動
make clean          # 環境クリーンアップ（コンテナ、ボリューム、キャッシュを削除）
make clean-deep     # 徹底的なクリーンアップ（node_modules含む、再インストール必要）
```

### テスト
```bash
make test                # 全テスト実行（バックエンド + フロントエンド）
make test-backend        # バックエンドテスト実行（pytestでカバレッジ有効）
make test-frontend       # フロントエンドテスト実行（Jestでカバレッジ有効）
```

### コード品質
```bash
make lint                # 全linting実行（バックエンド + フロントエンド）
make lint-backend        # バックエンドでflake8、mypy、banditを実行
make lint-frontend       # ESLintとTypeScript型チェックを実行
make format              # 全コードをフォーマット
make format-backend      # バックエンドでblackとisortを実行
make format-frontend     # prettierとESLint --fixを実行
```

### データベース管理
```bash
make db-migrate          # データベースマイグレーション実行
make db-revision         # 新しいマイグレーション作成（メッセージ入力を求められる）
make db-status           # データベースとマイグレーションの状態確認
make db-seed             # テストデータ投入（問い合わせ4件、ストーリー3件、テンプレート3件）
make db-reset            # データベースリセット（破壊的操作 - 全データ削除）
make db-connect          # psqlでデータベースに接続
make db-tables           # 全テーブルと構造を一覧表示
make db-data             # 全テーブルのデータを表示
```

### モニタリング
```bash
make status              # サービス状態と接続性を確認
make logs                # 全サービスのログを表示（follow モード）
make logs-backend        # バックエンドログのみ表示
make logs-frontend       # フロントエンドログのみ表示
make logs-db             # データベースログのみ表示
```

### 個別テストの実行
```bash
# バックエンド - 単一テストファイル
docker-compose run --rm backend python -m pytest tests/test_inquiry_api.py -v

# バックエンド - 単一テスト関数
docker-compose run --rm backend python -m pytest tests/test_inquiry_api.py::test_create_inquiry -v

# フロントエンド - 単一テストファイル
docker-compose run --rm frontend npm test -- HomePage.test.tsx

# フロントエンド - 特定ファイルのwatchモード
docker-compose run --rm frontend npm test -- HomePage.test.tsx --watch
```

## アーキテクチャ

### バックエンド構造

バックエンドは関心の分離が明確なレイヤードアーキテクチャに従っています：

**APIレイヤー** (`backend/api/`):
- HTTPリクエストを処理するFastAPIルーター
- 現在実装済み: `inquiries.py`（POST、GETリスト、IDでGET）
- 計画中: Stories API、Templates API、AI生成エンドポイント

**モデル構成** (`backend/models/`):
- `database/` - SQLAlchemy ORMモデル（InquiryModel、StoryModel、StoryTemplateModel）
- `schemas/` - ドメイン検証用のPydanticスキーマ
- `api/` - APIコントラクト用のリクエスト/レスポンスモデル
- `enums/` - 共有列挙型（InquiryStatus、StoryStatus、Priorityなど）
- `export/` - 外部システム統合モデル（Kanbanエクスポート）
- `protocols/` - サービスインターフェースのプロトコル定義

**データベースレイヤー** (`backend/database.py`):
- 一元化されたデータベース接続管理
- 接続文字列の優先順位: DATABASE_URL環境変数 → 個別のDATABASE_*変数 → デフォルト値
- 組み込みヘルスチェックとリトライロジック
- 接続プーリング付きSQLAlchemyエンジン（pool_pre_ping、pool_recycle）

**データモデル**:
全モデルは、より良いパフォーマンスと外部統合の簡素化のため、**BigInteger ID**（UUIDではない）を使用します。全タイムスタンプはUTCタイムゾーン対応のdatetimeを使用します。

### フロントエンド構造

コンポーネントベースアーキテクチャのReact TypeScriptアプリケーション：

**Pages** (`frontend/src/pages/`):
- トップレベルのルートコンポーネント（HomePage、InquiriesPage、TasksPage）
- 各ページが独自のデータ取得と状態を管理

**Components** (`frontend/src/components/`):
- `forms/` - react-hook-form + zod検証を使用したフォームコンポーネント
- `layout/` - レイアウトコンポーネント（ヘッダー、ナビゲーション、コンテナ）

**Services** (`frontend/src/services/`):
- `apiClient.ts` - 基本設定を持つAxiosベースのHTTPクライアント
- `inquiryService.ts` - 問い合わせ固有のAPI呼び出し
- package.jsonのプロキシ設定が`/api`リクエストをバックエンドにルーティング

**型システム** (`frontend/src/types/`):
- `models/` - バックエンドスキーマと一致するドメインモデル（Inquiry、Story、Template）
- `enums/` - バックエンドの列挙型と一致する列挙型
- `api/` - APIリクエスト/レスポンス型
- `export/` - エクスポート形式の型

### データベースアーキテクチャ

**接続の優先順位**:
1. `DATABASE_URL` 環境変数（完全な接続文字列）
2. 個別の `DATABASE_*` 変数（`DATABASE_HOST`、`DATABASE_PORT`、`DATABASE_NAME`、`DATABASE_USER`、`DATABASE_PASSWORD`）
3. Dockerデフォルト: `postgresql://gs_user:gs_password@db:5432/gs_db`

**マイグレーション管理**:
- Alembicがスキーママイグレーションを処理
- 現在の状態: BigInteger IDを持つ統合初期マイグレーション（`initial_schema_for_storyboard.py`）
- 全データベースコマンドは起動時の競合状態を処理するための自動リトライロジック（10回試行、2秒間隔）を含む

**主要テーブル**:
- `inquiries` - 状態追跡付きユーザー問い合わせ（RECEIVED、PROCESSING、COMPLETED）
- `stories` - 問い合わせにリンクされた生成されたユーザーストーリー
- `story_templates` - ストーリー生成用のパターンベーステンプレート

### Dockerアーキテクチャ

**サービス**:
- `db` - PostgreSQL 15 Alpine（ポート5432）
- `backend` - uvicorn付きFastAPI（ポート8000）
- `frontend` - React開発サーバー（ポート3000）

**ボリュームマウント**:
- ホットリロード用にバックエンド/フロントエンドのソースコードをマウント
- データベース永続化用の`postgres_data`ボリューム
- ホストとの競合を防ぐため、フロントエンドのnode_modulesを匿名ボリュームに配置

**ネットワーク**:
- コンテナ間通信用の`gs-network`ブリッジネットワーク上の全サービス

## 重要な開発パターン

### バックエンドパターン

**データベースセッション**:
データベースセッションには常に依存性注入を使用してください：
```python
from database import get_db
from sqlalchemy.orm import Session

@router.get("/endpoint")
async def handler(db: Session = Depends(get_db)):
    # ここでdbを使用 - 自動的にクローズされます
```

**モデルレイヤーの分離**:
- SQLAlchemyモデルは`models/database/`に配置（永続化）
- Pydanticスキーマは`models/schemas/`に配置（ドメイン検証）
- APIモデルは`models/api/`に配置（HTTPコントラクト）

これらの関心事を混在させないでください - レイヤー間で明示的に変換してください。

**エラーハンドリング**:
全APIエンドポイントはSQLAlchemyErrorをキャッチし、適切なHTTP例外を返す必要があります：
```python
try:
    db.add(model)
    db.commit()
    db.refresh(model)
except SQLAlchemyError as e:
    db.rollback()
    raise HTTPException(status_code=500, detail=str(e))
```

**列挙型の使用**:
列挙型はデータベースに文字列値として保存されます。代入時は常に`.value`を使用してください：
```python
inquiry.status = InquiryStatus.RECEIVED.value  # InquiryStatus.RECEIVEDではない
```

### フロントエンドパターン

**API統合**:
全API呼び出しにはサービスレイヤーを使用してください：
```typescript
import { inquiryService } from '@/services';

const inquiry = await inquiryService.create(data);
```

**型安全性**:
一元化された型ディレクトリから型をインポートしてください：
```typescript
import { Inquiry, InquiryStatus } from '@/types';
```

**フォーム検証**:
全フォームにreact-hook-formとzodスキーマを使用してください：
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({ content: z.string().min(1) });
const { register, handleSubmit } = useForm({
  resolver: zodResolver(schema)
});
```

## 環境変数

必要な環境変数（完全なリストは`.env.example`を参照）：

**データベース**（どちらかのアプローチを選択）:
```bash
# オプション1: 完全な接続文字列
DATABASE_URL=postgresql://user:password@host:port/database

# オプション2: 個別変数
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_NAME=gs_db
DATABASE_USER=gs_user
DATABASE_PASSWORD=gs_password
```

**AI統合**:
```bash
OPENAI_API_KEY=your_openai_api_key  # ストーリー生成に必要
```

**セキュリティ**（本番環境では変更）:
```bash
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
```

## 一般的なワークフロー

### 新しいデータベースモデルの追加

1. `backend/models/database/`にSQLAlchemyモデルを作成
2. `backend/models/schemas/`にPydanticスキーマを追加
3. `backend/models/api/`にAPIリクエスト/レスポンスモデルを作成
4. マイグレーション作成: `make db-revision`
5. マイグレーション適用: `make db-migrate`
6. `frontend/src/types/models/`に対応するTypeScript型を追加

### 新しいAPIエンドポイントの追加

1. `backend/api/`の適切なルーターにルートハンドラーを追加
2. `models/api/`から適切なリクエスト/レスポンスモデルを使用
3. `frontend/src/services/`に対応するサービスメソッドを追加
4. `make test-backend`と`make test-frontend`でテスト

### データベーススキーマの変更

1. `backend/models/database/`のモデルを修正
2. マイグレーション作成: `make db-revision`（説明的なメッセージを入力）
3. `backend/alembic/versions/`の生成されたマイグレーションを確認
4. マイグレーション適用: `make db-migrate`
5. 必要に応じて`backend/seed_data.py`のシードデータを更新
6. `make db-reset && make db-seed`でテスト

## テストに関する考慮事項

**バックエンドテスト**:
- pytestとpytest-covを使用したカバレッジ測定
- データベーステストは`tests/conftest.py`のfixtureを使用する必要があります
- 最低40%のカバレッジを目指してください（requirementsで設定済み）

**フロントエンドテスト**:
- JestとReact Testing Libraryを使用
- カバレッジ閾値: 40%（分岐、関数、行、ステートメント）
- サービスレイヤーを使用してAPI呼び出しをモック

## 既知の設定詳細

**バックエンド**:
- FastAPIは開発時にポート8000でauto-reloadを有効にして実行
- localhost:3000とfrontend:3000に対してCORSを有効化
- API文書はhttp://localhost:8000/docsで利用可能

**フロントエンド**:
- ポート3000のReact開発サーバーでホットリロード
- プロキシ設定が`/api`リクエストをバックエンドにルーティング
- Dockerとの互換性のため、ファイル監視はポーリングを使用（CHOKIDAR_USEPOLLING）

**データベース**:
- docker-composeでPostgreSQLのタイムゾーンをAsia/Tokyoに設定
- 全アプリケーションのタイムスタンプはUTCで保存
- プリピングヘルスチェック付きの接続プーリング
- 起動時の競合状態を処理する自動リトライロジック

## トラブルシューティング

**データベース接続の問題**:
```bash
make logs-db           # データベースログを確認
make db-status         # データベース状態を確認
make db-connect        # 直接接続をテスト
```

**マイグレーションの問題**:
```bash
make db-status         # 現在のマイグレーション状態を確認
make db-reset          # 最終手段: すべてリセット（破壊的操作）
```

**コンテナの問題**:
```bash
make status            # 全サービスを確認
make clean && make setup  # クリーンな再ビルド
```

**ポート競合**:
`make dev`を実行する前に、ポート3000、8000、または5432が既に使用されているかどうかを確認し、競合するサービスを停止してください。

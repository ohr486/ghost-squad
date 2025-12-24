# Ghost Squad

AIエージェントによるタスク管理ツールです。自然言語での問い合わせを理解し、様々なタスク管理機能を提供します。

## 概要

Ghost Squadは、AIエージェントを活用した包括的なタスク管理プラットフォームです。自然言語での問い合わせを構造化されたユーザーストーリーに変換し、既存のカンバンシステムに統合します。

### 🎯 ストーリーボード機能（現在実装済み）
- 🗣️ **自然言語問い合わせ**: 日本語での問い合わせ入力・保存・履歴管理
- 📊 **REST API**: 問い合わせの作成・取得・管理のためのAPIエンドポイント
- 🗄️ **データ永続化**: PostgreSQL + SQLAlchemy による信頼性の高いデータ管理
- 🔧 **開発環境**: Docker Compose + Makefileによる統合開発環境

### 🚧 開発中の機能
- 🤖 **AI駆動ストーリー生成**: OpenAI APIを使用した自動ストーリー変換
- 📝 **ストーリーレビュー**: 生成されたストーリーの確認・編集機能
- 🌐 **React WebUI**: TypeScriptによるモダンなフロントエンド
- 🔗 **外部システム統合**: Trello、Jira、GitHub Projectsとの連携

### 🚀 将来の機能拡張
- AI駆動ストーリー生成の完全実装
- React TypeScript WebUIの実装
- タスクの自動優先度付け
- プロジェクト進捗の予測分析
- チーム生産性の最適化提案
- 多言語対応のタスク管理
- カスタムワークフローの自動化

## アーキテクチャ

Ghost Squadは以下の技術スタックで構築されています：

- **バックエンド**: Python FastAPI + SQLAlchemy ORM
- **フロントエンド**: React TypeScriptアプリケーション
- **データベース**: PostgreSQL + Alembicマイグレーション
- **AI統合**: OpenAI APIによるストーリー生成
- **コンテナ化**: Docker Composeによる開発環境

## 開発環境セットアップ

### 前提条件

以下のソフトウェアがインストールされている必要があります：

- [Docker](https://docs.docker.com/get-docker/) (20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (2.0+)
- [Make](https://www.gnu.org/software/make/) (GNU Make 4.0+)
- [Git](https://git-scm.com/) (2.30+)

### クイックスタート

1. **リポジトリのクローン**
   ```bash
   git clone <repository-url>
   cd ghost-squad
   ```

2. **環境変数の設定**
   ```bash
   cp .env.example .env
   # .envファイルを編集して実際の値を設定
   ```

3. **開発環境の初期化**
   ```bash
   make setup
   ```

4. **開発サーバーの起動**
   ```bash
   make dev
   ```

5. **アプリケーションへのアクセス**
   - フロントエンド: http://localhost:3000
   - バックエンドAPI: http://localhost:8000
   - API文書: http://localhost:8000/docs

### 環境変数設定

`.env`ファイルで以下の重要な設定を行ってください：

#### 必須設定

```bash
# OpenAI API（ストーリー生成に必要）
OPENAI_API_KEY=your_openai_api_key_here

# データベース（デフォルト値で動作しますが、本番環境では変更推奨）
DATABASE_PASSWORD=secure_password_here

# セキュリティ（本番環境では必ず変更）
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
```

#### オプション設定

```bash
# 外部カンバンシステム統合（使用する場合）
TRELLO_API_KEY=your_trello_api_key
JIRA_API_TOKEN=your_jira_api_token
GITHUB_TOKEN=your_github_token

# 通知機能（使用する場合）
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## 開発コマンド

### 基本操作

```bash
# 開発環境の初期セットアップ
make setup

# 開発サーバー起動（バックグラウンド）
make dev

# 開発サーバー停止
make stop

# 開発サーバー再起動
make restart

# 環境のクリーンアップ
make clean

# 開発環境の状態確認
make status
```

### テスト実行

```bash
# 全テスト実行
make test

# バックエンドテストのみ
make test-backend

# フロントエンドテストのみ
make test-frontend
```

### コード品質

```bash
# コード品質チェック（全体）
make lint

# コードフォーマット（全体）
make format

# バックエンドのみ
make lint-backend
make format-backend

# フロントエンドのみ
make lint-frontend
make format-frontend
```

### データベース管理

```bash
# データベースマイグレーション実行
make db-migrate

# 新しいマイグレーション作成
make db-revision

# データベース状態確認
make db-status

# テストデータ投入
make db-seed

# データベースリセット（注意：全データ削除）
make db-reset

# データベースに直接接続
make db-connect

# データベーステーブル一覧表示
make db-tables

# データベース内のデータ表示
make db-data
```

### ログ確認

```bash
# 全サービスのログ表示
make logs

# 個別サービスのログ
make logs-backend
make logs-frontend
make logs-db
```

## プロジェクト構造

```
ghost-squad/
├── backend/                 # Python FastAPIバックエンド
│   ├── main.py             # FastAPIアプリケーション
│   ├── database.py         # データベース接続管理
│   ├── manage_db.py        # データベース管理スクリプト
│   ├── seed_data.py        # テストデータシーディング
│   ├── models/             # データモデル
│   │   ├── database/       # SQLAlchemyモデル
│   │   ├── enums/          # 列挙型定義
│   │   └── schemas/        # Pydanticスキーマ
│   ├── alembic/            # データベースマイグレーション
│   ├── tests/              # バックエンドテスト
│   └── requirements.txt    # Python依存関係
├── frontend/               # React TypeScriptフロントエンド
│   ├── src/                # ソースコード
│   ├── public/             # 静的ファイル
│   ├── package.json        # Node.js依存関係
│   └── tsconfig.json       # TypeScript設定
├── docs/                   # プロジェクトドキュメント
│   └── DATABASE.md         # データベース管理ガイド
├── .kiro/                  # Kiro仕様ファイル
│   └── specs/              # 機能仕様
│       └── storyboard/     # ストーリーボード機能仕様
├── docker-compose.yml      # Docker Compose設定
├── Makefile               # 開発タスク自動化
├── .env.example           # 環境変数テンプレート
└── README.md              # このファイル
```

## データベース管理

Ghost Squadは PostgreSQL データベースを使用し、SQLAlchemy ORM と Alembic によるマイグレーション管理を行います。

### データベースの初期化

```bash
# 初回セットアップ時（make setupに含まれます）
make db-migrate
make db-seed
```

### 日常的なデータベース操作

```bash
# データベースの状態確認
make db-status

# データの確認
make db-data

# テーブル構造の確認
make db-tables

# インタラクティブなデータベース接続
make db-connect
```

### 開発時のデータベース操作

```bash
# モデル変更後の新しいマイグレーション作成
make db-revision

# マイグレーションの適用
make db-migrate

# 開発用データの再投入
make db-seed
```

詳細なデータベース管理については、[データベース管理ガイド](docs/DATABASE.md) を参照してください。

## API仕様

### 現在実装済みのエンドポイント

**問い合わせ管理API**
- `POST /api/inquiries` - 問い合わせ作成
- `GET /api/inquiries` - 問い合わせ一覧取得（ページネーション・フィルタリング対応）
- `GET /api/inquiries/{id}` - 特定の問い合わせ取得

**システム情報API**
- `GET /api/info` - API情報取得
- `GET /api/db-test` - データベース接続テスト
- `GET /health` - ヘルスチェック

### 開発中のエンドポイント

**ストーリー管理API**
- `POST /api/inquiries/{id}/generate-stories` - ストーリー生成
- `GET /api/stories` - ストーリー一覧取得
- `PUT /api/stories/{id}` - ストーリー更新
- `POST /api/stories/{id}/approve` - ストーリー承認

詳細なAPI仕様は http://localhost:8000/docs で確認できます。

### 将来のAPI拡張
Ghost Squadの機能拡張に伴い、以下のAPIエンドポイントが追加予定です：
- ストーリー生成・管理API
- タスク自動優先度付けAPI
- プロジェクト進捗予測API
- チーム生産性分析API

## 開発ワークフロー

### 1. 現在実装済みの機能

**問い合わせ管理**
1. WebUIまたはAPIで問い合わせを入力
2. システムが問い合わせを受け付けて保存
3. 問い合わせ履歴の確認・検索

**データベース管理**
- PostgreSQL + SQLAlchemy による永続化
- Alembic によるマイグレーション管理
- テストデータのシーディング機能

### 2. 開発中の機能

**ストーリー生成ワークフロー**
1. 問い合わせからAIを使用してストーリーを生成
2. 生成されたストーリーをレビュー・編集
3. 承認後、外部カンバンシステムに出力

**ストーリー管理**
- ストーリーの一覧表示・検索
- 個別ストーリーの詳細編集
- 一括操作（承認・拒否）
- 変更履歴の確認

### 3. 将来実装予定の機能

**外部システム統合**
- Trello、Jira、GitHub Projectsとの連携
- カスタムフォーマットでのエクスポート
- 同期状態の追跡

## トラブルシューティング

### よくある問題

#### 1. Docker関連

**問題**: `make dev`でコンテナが起動しない
```bash
# 解決方法
make clean
make setup
make dev
```

**問題**: ポートが既に使用されている
```bash
# 使用中のポートを確認
lsof -i :3000  # フロントエンド
lsof -i :8000  # バックエンド
lsof -i :5432  # PostgreSQL

# プロセスを停止してから再実行
make stop
make dev
```

#### 2. データベース関連

**問題**: マイグレーションエラー
```bash
# データベース状態確認
make db-status

# データベースリセット（注意：データが削除されます）
make db-reset
make db-migrate
```

**問題**: 接続エラー
```bash
# データベースコンテナの状態確認
make status
make logs-db

# データベース接続テスト
make db-connect
```

**問題**: データが表示されない
```bash
# データベース内のデータ確認
make db-data

# テーブル構造確認
make db-tables

# テストデータの再投入
make db-seed
```

#### 3. API関連

**問題**: OpenAI APIエラー
- `.env`ファイルの`OPENAI_API_KEY`が正しく設定されているか確認
- APIキーの使用制限・残高を確認

**問題**: CORS エラー
- `.env`ファイルの`CORS_ORIGINS`設定を確認
- フロントエンドのURLが含まれているか確認

### ログの確認方法

```bash
# 全体のログ
make logs

# 特定のサービス
make logs-backend
make logs-frontend
make logs-db

# リアルタイムでログを監視
docker-compose logs -f backend
```

### 開発環境のリセット

完全に環境をリセットしたい場合：

```bash
# 全コンテナ・ボリューム・ネットワークを削除
make clean

# 再セットアップ
make setup
make dev
```

## 貢献

1. フィーチャーブランチを作成
2. 変更を実装
3. テストを実行: `make test`
4. コード品質チェック: `make lint`
5. プルリクエストを作成

## ライセンス

[ライセンス情報をここに記載]

## サポート

Ghost Squadに関する問題や質問がある場合は、以下の方法でサポートを受けられます：

- GitHub Issues: [リンク]
- ドキュメント: 
  - [データベース管理ガイド](docs/DATABASE.md)
  - ストーリーボード機能の開発者ガイド: `.kiro/specs/storyboard/`

### 開発者向けリソース

- **データベース管理**: `docs/DATABASE.md` - データベースのセットアップ、マイグレーション、トラブルシューティング
- **機能仕様**: `.kiro/specs/storyboard/` - ストーリーボード機能の要件、設計、実装計画
- **API仕様**: http://localhost:8000/docs - 開発サーバー起動時に利用可能

---

**注意**: 本番環境にデプロイする前に、セキュリティ設定（パスワード、APIキー等）を必ず変更してください。
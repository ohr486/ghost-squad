# Ghost Squad

AIエージェントによるタスク管理ツールです。自然言語での問い合わせを理解し、様々なタスク管理機能を提供します。

## 概要

Ghost Squadは、AIエージェントを活用した包括的なタスク管理プラットフォームです。自然言語での問い合わせを構造化されたユーザーストーリーに変換します。

### 🎯 実装済みの機能
- 🗣️ **自然言語問い合わせ**: 日本語での問い合わせ入力・保存・履歴管理・承認/却下ワークフロー
- 📊 **REST API**: 問い合わせ・ストーリー・インポーターの作成・取得・管理のためのAPIエンドポイント
- 🗄️ **データ永続化**: PostgreSQL + SQLAlchemy による信頼性の高いデータ管理
- 🔧 **開発環境**: Docker Compose + Makefileによる統合開発環境
- 🤖 **AI駆動ストーリー生成**: OpenAI APIを使用した自動ストーリー変換
- 📝 **ストーリー管理**: 生成されたストーリーの確認・編集・承認・一括承認機能
- 📧 **外部データインポート**: メール（IMAP）からの問い合わせ自動取り込み・AI解析
- 🔌 **プラグインアーキテクチャ**: データソース（メール等）とAIプロバイダー（OpenAI/Anthropic）の二層拡張構造
- 🌐 **React WebUI**: TypeScriptによるモダンなフロントエンド（問い合わせ・ストーリー・インポーター管理）

### 🚀 将来の機能拡張
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
- **AI統合**: OpenAI API / Anthropic APIによるストーリー生成・データ解析
- **インポーター**: ダブルプラグインアーキテクチャ（データソース + AIプロバイダー）
- **コンテナ化**: Docker Composeによる開発環境
- **開発手法**: Kiro-style Spec-Driven Development (AI-DLC)

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
# Anthropic API（Importer AIプロバイダーとして使用する場合）
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# メールインポート機能（使用する場合）
IMAP_SERVER=your_imap_server
IMAP_USERNAME=your_imap_username
IMAP_PASSWORD=your_imap_password

# 通知機能（使用する場合）
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## 開発コマンド

Ghost SquadはMakefileを使用して開発タスクを自動化しています。

### よく使うコマンド

```bash
# 環境セットアップ
make setup          # 初期環境構築
make dev           # 開発サーバー起動
make stop          # サーバー停止
make status        # 状態確認

# テスト・品質チェック
make test          # 全テスト実行
make lint          # コード品質チェック
make format        # コードフォーマット

# データベース
make db-migrate    # マイグレーション実行
make db-seed       # テストデータ投入
make db-status     # データベース状態確認

# ログ確認
make logs          # 全サービスのログ
make logs-backend  # バックエンドログ
```

**📖 詳細**: [開発コマンドリファレンス](docs/COMMAND.md) - 全コマンドの詳細説明とワークフロー例

## プロジェクト構造

```
ghost-squad/
├── api/                    # Python FastAPIバックエンド
│   ├── main.py            # FastAPIアプリケーション
│   ├── database.py        # データベース接続管理
│   ├── config.py          # 設定管理
│   ├── models/            # データモデル
│   │   ├── database/      # SQLAlchemyモデル（inquiry, story, import_error_log）
│   │   ├── schemas/       # Pydanticスキーマ（inquiry, story, importer）
│   │   └── enums/         # ステータス・優先度列挙型
│   ├── routers/           # APIルーター（inquiry, story, importer）
│   ├── services/          # ビジネスロジック
│   │   ├── *_repository.py     # データアクセス層
│   │   ├── *_validator.py      # バリデーション
│   │   ├── *_query_service.py  # 検索サービス
│   │   ├── *_workflow_service.py # ワークフロー管理
│   │   ├── story_generation_service.py # AI生成
│   │   └── importer/      # インポーター（プラグイン基盤、AIプロバイダー、メールプラグイン）
│   ├── alembic/           # データベースマイグレーション
│   └── tests/             # バックエンドテスト
├── web/                   # React TypeScriptフロントエンド
│   ├── src/
│   │   ├── components/    # UIコンポーネント
│   │   │   ├── InquiryForm.tsx, InquiryList.tsx, InquiryDetail.tsx
│   │   │   ├── StoryForm.tsx, StoryList.tsx, StoryDetail.tsx
│   │   │   └── importer/  # インポーター管理コンポーネント
│   │   ├── services/      # APIクライアント（inquiry, story, importer）
│   │   └── types/         # TypeScript型定義（inquiry, story, importer）
│   ├── public/            # 静的ファイル
│   └── package.json       # Node.js依存関係
├── docs/                  # プロジェクトドキュメント
│   ├── API.md            # API仕様
│   ├── DATABASE.md       # データベース管理ガイド
│   └── SDD.md            # Spec-Driven Development
├── .kiro/                 # Kiro仕様ファイル
│   ├── steering/         # プロジェクト全体のガイドライン
│   └── specs/            # 機能仕様（inquiry, story, importer）
├── docker-compose.yml     # Docker Compose設定
├── Makefile              # 開発タスク自動化
├── .env.example          # 環境変数テンプレート
├── CLAUDE.md             # AI開発アシスタント向けガイド
└── README.md             # このファイル
```

## 開発ワークフロー

Ghost Squadは **Kiro-style Spec-Driven Development** を採用しています。

### 基本的な開発フロー

1. **仕様策定**: 要件定義 → 設計 → タスク分解
2. **実装**: TDD（テスト駆動開発）で実装
3. **検証**: テスト・レビュー・承認

詳細は [Spec-Driven Development ガイド](docs/SDD.md) を参照してください。

### 現在実装済みの機能

**問い合わせ管理**
- WebUIまたはAPIで問い合わせを入力
- メールインポートによる自動取り込み
- システムが問い合わせを受け付けて保存
- 問い合わせ履歴の確認・検索・詳細表示
- 承認・却下ワークフロー
- ステータス管理（RECEIVED → TASK_WORKING → PROCESSING → COMPLETED等）

**ストーリー管理**
- 問い合わせからAIを使用してストーリーを自動生成
- ストーリーの一覧表示・検索・詳細表示
- ストーリーの編集・承認・拒否
- 優先度・カテゴリ管理
- ステータス管理（WAITING_REVIEW → APPROVED / REJECTED）

**インポーター（外部データ取り込み）**
- メール（IMAP）からの問い合わせ自動取り込み
- OpenAI / Anthropic によるAI解析（信頼度判定・レビューフラグ）
- プラグイン管理（有効化/無効化、デフォルトAIプロバイダー設定）
- エラーログ記録・統計・リトライ機能
- 問い合わせ一覧でのメールインポート情報表示（タイトル・送信者）

**データベース管理**
- PostgreSQL + SQLAlchemy による永続化
- Alembic によるマイグレーション管理
- テストデータのシーディング機能

## ドキュメント

Ghost Squadの詳細なドキュメントは `docs/` ディレクトリに整理されています：

### 📚 主要ドキュメント

- **[開発コマンドリファレンス](docs/COMMAND.md)** - Makefileコマンドの詳細説明、ワークフロー例
- **[トラブルシューティングガイド](docs/DEBUG.md)** - 問題解決方法、デバッグテクニック、環境リセット手順
- **[API仕様](docs/API.md)** - RESTful APIエンドポイント、リクエスト/レスポンス形式、エラーハンドリング
- **[データベース管理ガイド](docs/DATABASE.md)** - データベースのセットアップ、マイグレーション、トラブルシューティング
- **[Spec-Driven Development](docs/SDD.md)** - Kiro-style開発手法、仕様策定から実装までのフロー

### 🔧 開発者向けリソース

- **[CLAUDE.md](CLAUDE.md)** - AI開発アシスタント（Claude Code）向けガイド
- **機能仕様**: `.kiro/specs/` - 各機能の要件、設計、実装計画
- **プロジェクトガイドライン**: `.kiro/steering/` - プロダクト、技術、構造のガイドライン

## トラブルシューティング

開発中に問題が発生した場合：

### クイック診断
```bash
make status        # 環境の状態確認
make logs          # エラーログ確認
make disk-usage    # ディスク容量確認
```

### よくある問題

**コンテナが起動しない**:
```bash
make clean && make setup && make dev
```

**ポート競合**:
```bash
lsof -i :3000  # または :8000, :5432
make stop && make dev
```

**データベースエラー**:
```bash
make db-status  # 状態確認
make db-reset   # リセット（データ削除）
```

**API/環境変数エラー**:
```bash
cat .env        # 設定確認
make restart    # 再起動
```

### 環境のリセット

```bash
# レベル1: 再起動
make restart

# レベル2: クリーンアップ
make clean && make setup

# レベル3: 完全リセット
make clean-deep && make setup
```

**📖 詳細**: [トラブルシューティングガイド](docs/DEBUG.md) - 詳細な問題解決方法とデバッグテクニック

## 貢献

1. フィーチャーブランチを作成
2. 変更を実装
3. テストを実行: `make test`
4. コード品質チェック: `make lint`
5. プルリクエストを作成

## ライセンス

[ライセンス情報をここに記載]

## サポート

Ghost Squadに関する問題や質問がある場合は、以下のリソースを参照してください：

### 📖 ドキュメント
- [API仕様](docs/API.md) - APIエンドポイントとレスポンス形式
- [データベース管理](docs/DATABASE.md) - データベースのセットアップとトラブルシューティング
- [Spec-Driven Development](docs/SDD.md) - Kiro開発手法とワークフロー

### 🐛 問題報告
- GitHub Issues: [リンク]

---

**注意**: 本番環境にデプロイする前に、セキュリティ設定（パスワード、APIキー等）を必ず変更してください。

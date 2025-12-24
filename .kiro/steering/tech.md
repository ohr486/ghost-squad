# 技術スタック・ビルドシステム

## 技術スタック

**バックエンド (Python)**
- **フレームワーク**: FastAPI 0.104.1 + Uvicorn ASGIサーバー
- **データベース**: PostgreSQL + SQLAlchemy 2.0.23 ORM
- **マイグレーション**: Alembic 1.12.1によるデータベーススキーマ管理
- **AI統合**: OpenAI API 1.3.7によるストーリー生成
- **認証**: python-jose + cryptographyによるJWTトークン
- **テスト**: pytest + asyncio、mock、coverage、プロパティベーステスト（hypothesis）
- **コード品質**: black、flake8、mypy、isort、banditによるフォーマット・リント

**フロントエンド (TypeScript/React)**
- **フレームワーク**: React 18.2.0 + TypeScript 4.9.5
- **ビルドツール**: Create React App (react-scripts 5.0.1)
- **ルーティング**: React Router DOM 6.18.0
- **状態管理**: TanStack React Query 5.8.4
- **フォーム**: React Hook Form 7.47.0 + Zodバリデーション
- **スタイリング**: Tailwind CSS 3.3.5 + Tailwind Forms
- **HTTPクライアント**: Axios 1.6.2
- **アイコン**: Lucide React 0.294.0
- **テスト**: Jest、React Testing Library、fast-checkプロパティベーステスト

**インフラストラクチャ**
- **コンテナ化**: Docker + Docker Compose
- **データベース**: PostgreSQL 15 Alpine
- **開発環境**: フロントエンド・バックエンド両方でホットリロード有効

## よく使うコマンド

### 環境セットアップ
```bash
make setup          # 初期環境構築
make dev            # 開発サーバー起動（バックグラウンド）
make stop           # 全サービス停止
make restart        # 全サービス再起動
make clean          # 環境クリーンアップ
```

### 開発ワークフロー
```bash
make test           # 全テスト実行
make test-backend   # バックエンドテスト（カバレッジ付き）
make test-frontend  # フロントエンドテスト（カバレッジ付き）
make lint           # コード品質チェック（全体）
make format         # コードフォーマット（全体）
```

### データベース管理
```bash
make db-migrate     # データベースマイグレーション実行
make db-revision    # 新しいマイグレーション作成
make db-seed        # テストデータ投入
make db-reset       # データベースリセット（破壊的操作）
make db-status      # マイグレーション状態確認
make db-connect     # インタラクティブデータベース接続
```

### 監視・デバッグ
```bash
make status         # サービス健全性確認
make logs           # 全サービスログ表示
make logs-backend   # バックエンドログのみ
make logs-db        # データベースログのみ
```

## 開発環境

- **バックエンドポート**: 8000 (API文書は /docs)
- **フロントエンドポート**: 3000
- **データベースポート**: 5432
- **ホットリロード**: フロントエンド・バックエンド両方で有効
- **環境変数**: .envファイルで管理（.env.exampleからコピー）

## コード品質基準

- **Python**: Blackフォーマット、flake8リント、mypy型チェック、banditセキュリティ
- **TypeScript**: ESLint、Prettierフォーマット、厳密なTypeScript設定
- **テスト**: プロパティベーステストサポート付きの包括的テストカバレッジ
- **Pre-commitフック**: 自動品質チェック利用可能
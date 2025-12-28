---
inclusion: always
---

# 技術スタック・開発環境ガイドライン

Ghost Squadプロジェクトの技術スタックと開発環境に関するガイドラインです。新しい依存関係の追加や環境設定を行う際は、この基準に従ってください。

## 技術スタック

**バックエンド (Python 3.11+)**
- **フレームワーク**: FastAPI 0.104.1 + Uvicorn 0.24.0 ASGIサーバー
- **データベース**: PostgreSQL 15 + SQLAlchemy 2.0.23 ORM
- **マイグレーション**: Alembic 1.12.1によるスキーマ管理
- **AI統合**: OpenAI API 1.3.7（GPT-4使用推奨）
- **認証**: python-jose[cryptography] 3.3.0 + passlib[bcrypt] 1.7.4
- **バリデーション**: Pydantic 2.5.0 + pydantic-settings 2.1.0
- **テスト**: pytest 7.4.3 + pytest-asyncio + pytest-cov 4.1.0 + hypothesis 6.92.1（PBT）
- **コード品質**: black 23.11.0 + flake8 6.1.0 + mypy 1.7.1 + isort 5.12.0 + bandit 1.7.5
- **開発支援**: rich 13.7.0 + structlog 23.2.0 + ipdb 0.13.13

**フロントエンド (Node.js 18+)**
- **フレームワーク**: React 18.2.0 + TypeScript 4.9.5
- **ビルドツール**: Create React App (react-scripts 5.0.1)
- **ルーティング**: React Router DOM 6.18.0
- **状態管理**: TanStack React Query 5.8.4（サーバー状態管理）
- **フォーム**: React Hook Form 7.43.0 + Zod 3.22.4 バリデーション
- **スタイリング**: Tailwind CSS 3.3.5 + @tailwindcss/forms 0.5.7
- **HTTPクライアント**: Axios 1.6.2（プロキシ設定済み）
- **UI**: Lucide React 0.294.0 + clsx 2.0.0 + react-hot-toast 2.4.1
- **ユーティリティ**: date-fns 2.30.0
- **テスト**: Jest + React Testing Library + fast-check 3.15.0（PBT）

**インフラストラクチャ**
- **コンテナ化**: Docker + Docker Compose（開発環境）
- **データベース**: PostgreSQL 15 Alpine
- **リバースプロキシ**: 本番環境ではNginx推奨
- **環境変数**: .envファイル管理（12-factor app準拠）

## 開発環境セットアップ

**必須ツール**
- Docker Desktop（最新版）
- Make（コマンド実行用）
- Git（バージョン管理）
- エディタ：VS Code推奨（拡張機能設定あり）

**推奨VS Code拡張機能**
- Python（Microsoft）- バックエンド開発
- TypeScript Importer - インポート自動化
- Tailwind CSS IntelliSense - CSS補完
- ESLint + Prettier - コード品質・フォーマット
- Docker - コンテナ管理
- GitLens - Git統合
- Thunder Client - API テスト（Postman代替）
- SQLTools - データベース管理

## よく使うコマンド

### 環境セットアップ・管理
```bash
make setup          # 初期環境構築（.env作成、依存関係インストール、DB設定）
make dev            # 開発サーバー起動（バックグラウンド）
make stop           # 全サービス停止
make restart        # 全サービス再起動
make clean          # 環境クリーンアップ（ボリューム削除）
make status         # サービス健全性確認
```

### 開発ワークフロー
```bash
make test           # 全テスト実行（カバレッジレポート生成）
make test-api       # バックエンドテスト（pytest + coverage）
make test-web       # フロントエンドテスト（Jest + coverage）
make lint           # コード品質チェック（全体）
make lint-api       # バックエンドリント（flake8 + mypy + bandit）
                    # 対象: models/ services/ tests/ config.py database.py manage_db.py main.py
make lint-web       # フロントエンドリント（ESLint + TypeScript）
make format         # コードフォーマット（black + prettier）
make format-api     # バックエンドフォーマット（black + isort）
                    # 対象: models/ services/ tests/ config.py database.py manage_db.py main.py
make format-web     # フロントエンドフォーマット（prettier + ESLint --fix）
```

### データベース管理
```bash
make db-migrate     # マイグレーション実行
make db-init        # Alembic初期化
make db-revision    # 新しいマイグレーション作成
make db-status      # マイグレーション状態確認
make db-seed        # テストデータ投入
make db-reset       # データベースリセット（破壊的操作）
make db-reset-migrations # マイグレーション履歴リセット
make db-connect     # インタラクティブDB接続（psql）
make db-tables      # データベース内のテーブル一覧表示
make db-data        # データベース内のデータ表示
```

### 監視・デバッグ
```bash
make logs           # 全サービスログ表示
make logs-backend   # バックエンドログのみ
make logs-frontend  # フロントエンドログのみ
make logs-db        # データベースログのみ
make disk-usage     # ディスク容量とDocker使用量確認
make docker-cleanup # Docker不要データ削除
make volume-list    # Dockerボリューム一覧表示
make volume-cleanup # 未使用ボリューム削除
```

## 開発環境設定

**ポート設定**
- **バックエンド**: 8000（API文書: http://localhost:8000/docs）
- **フロントエンド**: 3000（アプリ: http://localhost:3000）
- **データベース**: 5432（外部接続可能）
- **PostgreSQL管理**: psql経由（`make db-connect`）

**環境変数管理**
```bash
# .env.example から .env をコピー
cp .env.example .env

# 必須環境変数
DATABASE_URL=postgresql://gs_user:gs_password@db:5432/gs_db
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_jwt_secret
ENVIRONMENT=development
DEBUG=true
```

**ホットリロード設定**
- バックエンド：Uvicorn `--reload` フラグ（ファイル変更時自動再起動）
- フロントエンド：React Scripts開発サーバー（ホットリロード）
- データベース：ボリュームマウントでデータ永続化
- 型定義：TypeScript watch mode（`npm run type-check`）

## コード品質基準

**Python品質チェック**
```bash
# フォーマット
black api/ --line-length 88
isort api/ --profile black

# リント
flake8 api/ --max-line-length 88
mypy api/ --strict
bandit -r api/ -x tests/

# テスト
pytest api/tests/ --cov=backend --cov-report=html
```

**TypeScript品質チェック**
```bash
# フォーマット
prettier web/src/ --write
eslint web/src/ --fix

# 型チェック
tsc --noEmit

# テスト
npm test -- --coverage --watchAll=false
```

**品質基準**
- **テストカバレッジ**:
  - バックエンド: 現在14+テスト（問い合わせAPI完全カバー）、新機能は80%以上
  - フロントエンド: 最低50%（段階的に70%へ引き上げ予定）、新機能は80%以上
- **型安全性**: TypeScript strict mode、mypy strict mode
- **コードスタイル**: Black（Python）、Prettier（TypeScript）
- **セキュリティ**: Bandit（Python）、ESLint security rules
- **API設計**: RESTful、日本語エラーメッセージ、適切なHTTPステータス

## 依存関係管理

**Python依存関係**
```bash
# 新しい依存関係追加
pip install package_name
pip freeze > requirements.txt

# 開発依存関係（requirements-dev.txt）
pip install -r requirements-dev.txt
```

**Node.js依存関係**
```bash
# 本番依存関係
npm install package_name

# 開発依存関係
npm install --save-dev package_name

# セキュリティ監査
npm audit
npm audit fix
```

**依存関係更新ポリシー**
- セキュリティアップデートは即座に適用
- マイナーバージョンアップは月次レビュー
- メジャーバージョンアップは四半期レビュー
- 破壊的変更は事前にチーム承認

## パフォーマンス・監視

**バックエンド監視**
- FastAPI自動生成メトリクス
- SQLAlchemyクエリログ
- OpenAI API使用量追跡
- レスポンス時間監視

**フロントエンド監視**
- React DevTools Profiler
- Lighthouse CI統合
- Bundle size監視
- Core Web Vitals追跡

**データベース最適化**
- インデックス戦略
- クエリパフォーマンス分析
- 接続プール設定
- 定期的なVACUUM実行

## セキュリティ設定

**バックエンドセキュリティ**
- CORS設定（本番環境では厳格化）
- JWT トークン有効期限管理
- API レート制限
- 入力値サニタイゼーション
- SQLインジェクション対策（SQLAlchemy ORM使用）

**フロントエンドセキュリティ**
- CSP（Content Security Policy）設定
- XSS対策（React標準機能）
- 機密情報の環境変数管理
- HTTPS強制（本番環境）

**開発環境セキュリティ**
- .env ファイルの .gitignore 登録
- 開発用シークレットの分離
- コンテナ間通信の最小権限原則
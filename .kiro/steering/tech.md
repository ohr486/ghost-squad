---
inclusion: always
---

# 技術スタック・開発環境ガイドライン

Ghost Squadプロジェクトの技術スタックと開発環境に関するガイドラインです。新しい依存関係の追加や環境設定を行う際は、この基準に従ってください。

## 技術スタック

**バックエンド (Python 3.11+)**
- **フレームワーク**: FastAPI 0.104.1 + Uvicorn ASGIサーバー
- **データベース**: PostgreSQL 15 + SQLAlchemy 2.0.23 ORM
- **マイグレーション**: Alembic 1.12.1によるスキーマ管理
- **AI統合**: OpenAI API 1.3.7（GPT-4使用推奨）
- **認証**: python-jose + cryptographyによるJWT
- **バリデーション**: Pydantic 2.x（FastAPI統合）
- **テスト**: pytest + asyncio + coverage + hypothesis（PBT）
- **コード品質**: black + flake8 + mypy + isort + bandit

**フロントエンド (Node.js 18+)**
- **フレームワーク**: React 18.2.0 + TypeScript 4.9.5+
- **ビルドツール**: Create React App (react-scripts 5.0.1)
- **ルーティング**: React Router DOM 6.18.0
- **状態管理**: TanStack React Query 5.8.4（サーバー状態）
- **フォーム**: React Hook Form 7.47.0 + Zod バリデーション
- **スタイリング**: Tailwind CSS 3.3.5 + Tailwind Forms
- **HTTPクライアント**: Axios 1.6.2（インターセプター設定済み）
- **アイコン**: Lucide React 0.294.0
- **テスト**: Jest + React Testing Library + fast-check（PBT）

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
- Python（Microsoft）
- TypeScript Importer
- Tailwind CSS IntelliSense
- ESLint + Prettier
- Docker
- GitLens

## よく使うコマンド

### 環境セットアップ・管理
```bash
make setup          # 初期環境構築（.env作成、依存関係インストール）
make dev            # 開発サーバー起動（バックグラウンド）
make stop           # 全サービス停止
make restart        # 全サービス再起動
make clean          # 環境クリーンアップ（ボリューム削除）
make rebuild        # コンテナ再ビルド
```

### 開発ワークフロー
```bash
make test           # 全テスト実行（カバレッジレポート生成）
make test-backend   # バックエンドテスト（pytest + coverage）
make test-frontend  # フロントエンドテスト（Jest + coverage）
make test-watch     # テスト監視モード
make lint           # コード品質チェック（全体）
make format         # コードフォーマット（black + prettier）
make type-check     # 型チェック（mypy + tsc）
```

### データベース管理
```bash
make db-migrate     # マイグレーション実行
make db-revision    # 新しいマイグレーション作成
make db-seed        # テストデータ投入
make db-reset       # データベースリセット（破壊的操作）
make db-status      # マイグレーション状態確認
make db-connect     # インタラクティブDB接続（psql）
make db-backup      # データベースバックアップ
```

### 監視・デバッグ
```bash
make status         # サービス健全性確認
make logs           # 全サービスログ表示
make logs-backend   # バックエンドログのみ
make logs-frontend  # フロントエンドログのみ
make logs-db        # データベースログのみ
make shell-backend  # バックエンドコンテナシェル
make shell-db       # データベースコンテナシェル
```

## 開発環境設定

**ポート設定**
- **バックエンド**: 8000（API文書: http://localhost:8000/docs）
- **フロントエンド**: 3000（アプリ: http://localhost:3000）
- **データベース**: 5432（外部接続可能）
- **Adminer**: 8080（DB管理UI: http://localhost:8080）

**環境変数管理**
```bash
# .env.example から .env をコピー
cp .env.example .env

# 必須環境変数
DATABASE_URL=postgresql://user:password@localhost:5432/ghost_squad
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_jwt_secret
ENVIRONMENT=development
```

**ホットリロード設定**
- バックエンド：Uvicorn `--reload` フラグ
- フロントエンド：React Scripts開発サーバー
- データベース：ボリュームマウントでデータ永続化

## コード品質基準

**Python品質チェック**
```bash
# フォーマット
black backend/ --line-length 88
isort backend/ --profile black

# リント
flake8 backend/ --max-line-length 88
mypy backend/ --strict
bandit -r backend/ -x tests/

# テスト
pytest backend/tests/ --cov=backend --cov-report=html
```

**TypeScript品質チェック**
```bash
# フォーマット
prettier frontend/src/ --write
eslint frontend/src/ --fix

# 型チェック
tsc --noEmit

# テスト
npm test -- --coverage --watchAll=false
```

**品質基準**
- **テストカバレッジ**: 最低80%（重要な機能は90%以上）
- **型安全性**: TypeScript strict mode、mypy strict mode
- **コードスタイル**: Black（Python）、Prettier（TypeScript）
- **セキュリティ**: Bandit（Python）、ESLint security rules

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
# Ghost Squad 開発コマンドリファレンス

Ghost Squadプロジェクトで使用する全ての開発コマンドの詳細リファレンスです。

## 概要

Ghost SquadはMakefileを使用して開発タスクを自動化しています。すべてのコマンドは `make {command}` の形式で実行します。

**コマンド一覧を表示**:
```bash
make help
```

## 環境セットアップコマンド

### `make setup`
初期環境構築を行います。プロジェクトのクローン後、最初に実行するコマンドです。

**実行内容**:
1. 前提条件チェック（Docker, Docker Compose）
2. `.env`ファイルの作成（`.env.example`からコピー）
3. Dockerコンテナのビルド
4. Python依存関係のインストール
5. Node.js依存関係のインストール
6. データベースマイグレーション実行
7. テストデータのシーディング

**使用例**:
```bash
make setup
```

**初回セットアップ後の確認**:
```bash
make status
```

### `make dev`
開発サーバーをバックグラウンドで起動します。

**起動されるサービス**:
- PostgreSQLデータベース (ポート 5432)
- バックエンドAPI (ポート 8000)
- フロントエンド (ポート 3000)

**使用例**:
```bash
make dev

# サービスの状態確認
make status
```

**アクセス先**:
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- API文書: http://localhost:8000/docs

### `make stop`
すべての開発サーバーを停止します。

**使用例**:
```bash
make stop
```

**注意**: データベースのデータは保持されます（ボリュームは削除されません）。

### `make restart`
すべての開発サーバーを再起動します。

**使用例**:
```bash
make restart
```

**用途**:
- 環境変数の変更を反映
- コンテナの設定変更を適用
- サービスのハング時

### `make clean`
開発環境をクリーンアップします（注意：データが削除されます）。

**実行内容**:
1. すべてのコンテナを停止
2. コンテナとネットワークを削除
3. 未使用のDockerイメージを削除
4. 未使用のDockerボリュームを削除
5. Pythonキャッシュファイルを削除（`__pycache__`, `.pytest_cache`, `.mypy_cache`等）
6. Node.jsキャッシュファイルを削除（`node_modules/.cache`等）

**使用例**:
```bash
make clean
```

**警告**: データベースのボリュームも削除されます。重要なデータがある場合は事前にバックアップしてください。

**クリーンアップ後の再セットアップ**:
```bash
make setup
make dev
```

### `make clean-deep`
徹底的なクリーンアップを行います（node_modulesも削除）。

**実行内容**:
- `make clean` の全内容
- `node_modules/` ディレクトリの削除
- `package-lock.json` の削除

**使用例**:
```bash
make clean-deep

# 再セットアップが必要
make setup
```

**用途**:
- Node.js依存関係の問題を解決
- ディスク容量の確保
- 完全なリセット

### `make status`
開発環境の状態を確認します。

**表示内容**:
- Dockerコンテナの状態
- 各サービスの接続状態（Backend API, Frontend, Database）

**使用例**:
```bash
make status
```

**出力例**:
```
📊 Development environment status:

🐳 Docker containers:
NAME       STATUS    PORTS
gs-api     Up        0.0.0.0:8000->8000/tcp
gs-web     Up        0.0.0.0:3000->3000/tcp
gs-db      Up        0.0.0.0:5432->5432/tcp

🌐 Service connectivity:
Backend API:  ✅ Responding
Frontend:     ✅ Responding
Database:     ✅ Ready
```

## テストコマンド

### `make test`
全テスト（バックエンド + フロントエンド）を実行します。

**使用例**:
```bash
make test
```

**実行されるテスト**:
- バックエンド: pytest + coverage
- フロントエンド: Jest + coverage

### `make test-backend`
バックエンドテストのみを実行します。

**実行内容**:
- pytestによるテスト実行
- カバレッジレポート生成（HTML形式）
- カバレッジ結果の表示

**使用例**:
```bash
make test-backend
```

**カバレッジレポート**:
- ターミナル出力: カバレッジ結果が表示されます
- HTMLレポート: `api/htmlcov/index.html`

**特定のテストのみ実行**:
```bash
# Docker コンテナ内で直接実行
docker-compose run --rm api pytest tests/test_specific.py -v
```

### `make test-frontend`
フロントエンドテストのみを実行します。

**実行内容**:
- Jestによるテスト実行
- カバレッジレポート生成

**使用例**:
```bash
make test-frontend
```

**カバレッジレポート**:
- ターミナル出力: カバレッジ結果が表示されます
- HTMLレポート: `web/coverage/lcov-report/index.html`

## コード品質コマンド

### `make lint`
全体のコード品質チェックを実行します。

**実行内容**:
- バックエンド: flake8 + mypy + bandit
- フロントエンド: ESLint + TypeScript type checking

**使用例**:
```bash
make lint
```

### `make lint-backend`
バックエンドのコード品質チェックを実行します。

**実行されるチェック**:
1. **flake8**: PEP 8スタイルガイドチェック
2. **mypy**: 型チェック（strict mode）
3. **bandit**: セキュリティ脆弱性チェック

**使用例**:
```bash
make lint-backend
```

**エラーの修正**:
```bash
# 自動フォーマットでスタイル問題を修正
make format-backend

# 型エラーは手動で修正が必要
```

### `make lint-frontend`
フロントエンドのコード品質チェックを実行します。

**実行されるチェック**:
1. **ESLint**: JavaScriptスタイルとエラーチェック
2. **TypeScript**: 型チェック（strict mode）

**使用例**:
```bash
make lint-frontend
```

**エラーの修正**:
```bash
# 自動修正可能なエラーを修正
make format-frontend
```

### `make format`
全体のコードフォーマットを実行します。

**実行内容**:
- バックエンド: black + isort
- フロントエンド: prettier + ESLint --fix

**使用例**:
```bash
make format
```

### `make format-backend`
バックエンドのコードフォーマットを実行します。

**実行されるフォーマッター**:
1. **black**: Pythonコードフォーマッター（88文字行長）
2. **isort**: インポート文の自動ソート（--profile black）

**使用例**:
```bash
make format-backend
```

**対象ファイル**:
- `api/` ディレクトリ内の全Pythonファイル
- `models/` ディレクトリ内の全Pythonファイル
- ルートディレクトリのPythonファイル（main.py, database.py等）
- `tests/` ディレクトリ内の全Pythonファイル（存在する場合）

### `make format-frontend`
フロントエンドのコードフォーマットを実行します。

**実行されるフォーマッター**:
1. **prettier**: コードフォーマッター（TypeScript, JavaScript, CSS, JSON等）
2. **ESLint --fix**: 自動修正可能なlintエラーを修正

**使用例**:
```bash
make format-frontend
```

**対象ファイル**:
- `src/**/*.{ts,tsx,js,jsx,json,css,md}`

## データベース管理コマンド

データベース関連コマンドの詳細は [DATABASE.md](DATABASE.md) も参照してください。

### `make db-migrate`
データベースマイグレーションを実行します。

**実行内容**:
1. データベースコンテナの起動
2. データベース接続確認（最大10回リトライ）
3. Alembicの初期化確認（未初期化の場合は自動初期化）
4. マイグレーションの実行（`alembic upgrade head`）

**使用例**:
```bash
make db-migrate
```

**注意**: 初回実行時は自動的にAlembicが初期化されます。

### `make db-init`
Alembic設定を初期化します（通常は不要）。

**使用例**:
```bash
make db-init
```

**用途**: Alembic設定を再作成する必要がある場合のみ。

### `make db-revision`
新しいマイグレーションファイルを作成します。

**実行内容**:
1. データベースコンテナの起動
2. マイグレーションメッセージの入力プロンプト表示
3. `alembic revision --autogenerate` によるマイグレーションファイル生成

**使用例**:
```bash
make db-revision
# Enter migration message: Add deadline field to stories
```

**生成されるファイル**:
- `api/alembic/versions/{revision_id}_{message}.py`

**マイグレーション作成後**:
```bash
# 生成されたファイルを確認
cat api/alembic/versions/{revision_id}_*.py

# 必要に応じて手動で編集

# マイグレーションを適用
make db-migrate
```

### `make db-status`
データベースとマイグレーションの状態を確認します。

**表示内容**:
1. Alembic設定の状態（alembic.ini, alembicディレクトリ）
2. 現在適用されているマイグレーション
3. 利用可能なマイグレーション履歴

**使用例**:
```bash
make db-status
```

### `make db-seed`
テストデータを投入します。

**実行内容**:
1. データベースコンテナの起動
2. データベース接続確認
3. `seed_data.py` スクリプトの実行

**使用例**:
```bash
make db-seed
```

**投入されるデータ**:
- サンプル問い合わせデータ
- サンプルストーリーデータ
- デフォルトテンプレートデータ

### `make db-reset`
データベースを完全にリセットします（警告：全データ削除）。

**実行内容**:
1. 5秒間の警告表示（Ctrl+Cでキャンセル可能）
2. データベースコンテナの停止
3. データベースボリュームの削除
4. 新しいデータベースの起動
5. マイグレーションの実行
6. テストデータの投入

**使用例**:
```bash
make db-reset
# ⚠️ This will delete all data. Press Ctrl+C to cancel, or wait 5 seconds to continue...
```

**用途**:
- データベーススキーマの完全な再構築
- マイグレーション履歴のリセット
- 開発環境のクリーンな状態への復元

### `make db-reset-migrations`
マイグレーション履歴をリセットします。

**使用例**:
```bash
make db-reset-migrations
```

**用途**: マイグレーション履歴が不整合になった場合。

### `make db-connect`
PostgreSQLデータベースに直接接続します（psqlインタラクティブモード）。

**使用例**:
```bash
make db-connect
```

**psql内での基本コマンド**:
```sql
-- テーブル一覧表示
\dt

-- テーブル構造確認
\d inquiries

-- データ取得
SELECT * FROM inquiries LIMIT 10;

-- 終了
\q
```

### `make db-tables`
データベース内のテーブル一覧と構造を表示します。

**表示内容**:
- すべてのテーブル一覧
- 各テーブルの詳細構造（カラム、型、制約）

**使用例**:
```bash
make db-tables
```

### `make db-data`
データベース内のデータを表示します。

**表示内容**:
- 問い合わせテーブルのデータ（プレビュー付き）
- ストーリーテーブルのデータ（プレビュー付き）
- テンプレートテーブルのデータ

**使用例**:
```bash
make db-data
```

## 監視・ログコマンド

### `make logs`
全サービスのログをリアルタイムで表示します（follow mode）。

**使用例**:
```bash
make logs
```

**終了**: `Ctrl+C`

### `make logs-backend`
バックエンドAPIのログのみを表示します。

**使用例**:
```bash
make logs-backend
```

**表示内容**:
- FastAPIのリクエスト/レスポンスログ
- アプリケーションログ
- エラーログ

### `make logs-frontend`
フロントエンドのログのみを表示します。

**使用例**:
```bash
make logs-frontend
```

**表示内容**:
- React開発サーバーのログ
- ビルドログ
- ホットリロードログ

### `make logs-db`
データベースのログのみを表示します。

**使用例**:
```bash
make logs-db
```

**表示内容**:
- PostgreSQLの起動ログ
- クエリログ（設定により）
- エラーログ

## ディスク管理コマンド

### `make disk-usage`
ディスク容量とDocker使用量を確認します。

**表示内容**:
1. システムディスク使用量
2. Docker全体の使用量
3. Dockerイメージ一覧（上位10件）
4. コンテナ一覧（上位10件）
5. ボリューム一覧（上位10件）

**使用例**:
```bash
make disk-usage
```

### `make docker-cleanup`
Docker不要データを対話的に削除します。

**クリーンアップレベル**:
1. **Basic cleanup** - 停止コンテナ、未使用ネットワーク、dangling images
2. **Aggressive cleanup** - 上記 + 未使用イメージ
3. **Volume cleanup** - 上記 + 未使用ボリューム（⚠️注意）
4. **Nuclear cleanup** - 上記 + すべてのボリューム（☢️非常に破壊的）

**使用例**:
```bash
make docker-cleanup
# Select cleanup level (1-4) or 'q' to quit:
```

**推奨**: まず Level 1 を試し、必要に応じてより高いレベルを選択。

### `make volume-list`
Dockerボリューム一覧と使用量を表示します。

**使用例**:
```bash
make volume-list
```

**表示内容**:
- ボリューム名
- マウントポイント
- サイズ
- 使用中のコンテナ

### `make volume-cleanup`
未使用ボリュームを削除します（対話的確認あり）。

**使用例**:
```bash
make volume-cleanup
# Continue with volume cleanup? (y/N):
```

### `make volume-cleanup-force`
強制的にボリュームをクリーンアップします（スクリプト使用）。

**使用例**:
```bash
make volume-cleanup-force
```

**注意**: `bin/volume-cleanup-force.sh` スクリプトが必要です。

## Pre-commitフックコマンド

### `make install-hooks`
pre-commitフックをインストールします。

**使用例**:
```bash
make install-hooks
```

**用途**: コミット前に自動的にコード品質チェックを実行。

### `make pre-commit`
すべてのファイルに対してpre-commitを実行します。

**使用例**:
```bash
make pre-commit
```

## よく使うワークフロー

### 初回セットアップ
```bash
# 1. リポジトリクローン
git clone <repository-url>
cd ghost-squad

# 2. 環境変数設定
cp .env.example .env
# .envファイルを編集

# 3. 環境構築
make setup

# 4. 開発サーバー起動
make dev

# 5. 状態確認
make status
```

### 日常的な開発フロー
```bash
# 1. 開発サーバー起動
make dev

# 2. コード変更

# 3. テスト実行
make test-backend  # または make test-frontend

# 4. コード品質チェック
make lint

# 5. フォーマット
make format

# 6. ログ確認
make logs-backend  # または make logs-frontend
```

### データベース変更時
```bash
# 1. モデル変更（api/models/database/ 内のファイル編集）

# 2. マイグレーション作成
make db-revision
# Enter migration message: Add new field

# 3. マイグレーション適用
make db-migrate

# 4. 確認
make db-tables
make db-data
```

### トラブルシューティング
```bash
# 環境がおかしい場合
make clean
make setup
make dev

# データベースがおかしい場合
make db-reset

# Node.js依存関係の問題
make clean-deep
make setup
make dev

# ログでエラー確認
make logs-backend
make logs-db
```

### テスト駆動開発（TDD）
```bash
# 1. テスト作成
# tests/test_new_feature.py を作成

# 2. テスト実行（失敗することを確認）
make test-backend

# 3. 実装

# 4. テスト実行（成功することを確認）
make test-backend

# 5. リファクタリング

# 6. テスト実行（まだ成功することを確認）
make test-backend
```

## トラブルシューティング

### コマンドが失敗する場合

**問題**: `make setup` が失敗する

**確認事項**:
```bash
# Dockerが起動しているか確認
docker ps

# Docker Composeが利用可能か確認
docker-compose --version

# ディスク容量を確認
make disk-usage
```

**解決方法**:
```bash
# Dockerを再起動
# macOS: Docker Desktop を再起動
# Linux: sudo systemctl restart docker

# 再試行
make setup
```

### ポートが使用中の場合

**問題**: ポート 3000, 8000, 5432 が既に使用されている

**確認**:
```bash
lsof -i :3000
lsof -i :8000
lsof -i :5432
```

**解決**:
```bash
# 既存のプロセスを停止
make stop

# または手動でプロセスを終了
kill -9 <PID>
```

### データベース接続エラー

**問題**: データベースに接続できない

**確認**:
```bash
make status
make logs-db
```

**解決**:
```bash
# データベースコンテナを再起動
docker-compose restart db

# または完全リセット
make db-reset
```

### テストが失敗する場合

**問題**: テストが失敗する

**確認**:
```bash
# 詳細なテスト出力を確認
docker-compose run --rm api pytest tests/ -v

# 特定のテストのみ実行
docker-compose run --rm api pytest tests/test_specific.py::test_function -v
```

**解決**:
```bash
# データベースをリセット
make db-reset

# 依存関係を再インストール
make clean
make setup
```

## 関連ドキュメント

- [README.md](../README.md) - プロジェクト概要
- [API仕様](API.md) - APIエンドポイント
- [データベース管理](DATABASE.md) - データベース詳細
- [Spec-Driven Development](SDD.md) - Kiro開発手法
- [CLAUDE.md](../CLAUDE.md) - AI開発アシスタント向けガイド

# データベースセットアップと管理

このドキュメントは、ストーリーボードシステムのデータベースセットアップと管理について説明します。

## 概要

システムはPostgreSQLを主要データベースとして使用し、SQLAlchemy ORMとAlembicによるマイグレーション管理を行います。

## データベースモデル

### コアモデル

1. **InquiryModel** (`inquiries` テーブル)
   - ユーザーからの問い合わせ・リクエストを保存
   - フィールド: id, user_id, content, language, timestamp, status, metadata
   - タイムスタンプ: UTC timezone-aware datetime使用

2. **StoryModel** (`stories` テーブル)
   - 問い合わせから生成されたストーリーを保存
   - フィールド: id, inquiry_id, title, description, category, priority, estimated_effort, deadline, status, assignee, tags, dependencies, metadata, timestamps
   - タイムスタンプ: UTC timezone-aware datetime使用

3. **StoryTemplateModel** (`story_templates` テーブル)
   - パターン認識用のストーリーテンプレートを保存
   - フィールド: id, name, pattern, fields, checklist, default_estimate, is_custom, user_id, timestamps
   - タイムスタンプ: UTC timezone-aware datetime使用

### タイムゾーン対応

すべてのモデルでタイムスタンプフィールドは `datetime.now(timezone.utc)` を使用し、Python 3.12以降の推奨事項に準拠しています。これにより：

- 適切なタイムゾーン処理の保証
- 将来の非推奨警告の回避
- 国際的なアプリケーションでの一貫した時刻管理

## データベース接続

データベース接続は `backend/database.py` で管理されます：

- **接続文字列**: 環境変数から構築（`DATABASE_URL` または個別の `DATABASE_*` 変数）
- **セッション管理**: 依存性注入によるSQLAlchemy SessionLocal
- **ヘルスチェック**: 組み込み接続確認機能

接続文字列の形式: `postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}`

## マイグレーション管理

### Alembicセットアップ

Alembicはモデルと連携するよう設定されています：

- **設定ファイル**: `backend/alembic.ini`
- **環境設定**: `backend/alembic/env.py` (全モデルをインポート)
- **マイグレーション**: `backend/alembic/versions/`

### 利用可能なコマンド

すべてのデータベース操作はMakefileから利用できます：

```bash
# データベース状態確認
make db-status

# マイグレーション実行
make db-migrate

# 新しいマイグレーション作成
make db-revision

# テストデータ投入
make db-seed

# データベースリセット（破壊的操作）
make db-reset

# Alembic初期化（必要に応じて）
make db-init
```

### データベース接続待機機能

すべてのデータベースコマンドは、データベースコンテナの起動を自動的に待機する機能を内蔵しています：

- **初期待機時間**: 3秒
- **最大試行回数**: 10回（db-resetは15回）
- **試行間隔**: 2秒
- **タイムアウト処理**: 接続失敗時にはログ確認のヒントを表示

これにより、データベースコンテナの起動中でも安全にコマンドを実行でき、レースコンディションを回避できます。

**待機ログの例**:
```
⏳ Waiting for database to be ready...
   Attempt 1/10 - Database not ready, waiting 2s...
   Attempt 2/10 - Database not ready, waiting 2s...
✅ Database is ready!
```

## データシーディング

システムには開発用のサンプルデータが含まれています：

- **スクリプト**: `backend/seed_data.py`
- **サンプルデータ**: 問い合わせ3件、ストーリー3件、テンプレート3件
- **管理**: `backend/manage_db.py`

### サンプルデータの内容

1. **問い合わせ**:
   - ユーザー登録機能のリクエスト
   - バグ報告（緊急）
   - パフォーマンス調査リクエスト

2. **ストーリー**:
   - APIエンドポイント実装
   - UIフォーム実装
   - バグ修正タスク

3. **テンプレート**:
   - API開発テンプレート
   - バグ修正テンプレート
   - 調査テンプレート

## データベース管理スクリプト

`backend/manage_db.py` スクリプトは以下の機能を提供します：

- **接続テスト**: データベース接続の確認
- **テーブル管理**: テーブルの作成・削除
- **データシーディング**: サンプルデータの投入
- **状態確認**: データベース状態の検査

### 使用方法

```bash
# 直接使用（コンテナ内）
python manage_db.py check    # 接続とテーブルの確認
python manage_db.py seed     # サンプルデータの投入
python manage_db.py clear    # 全データの削除
python manage_db.py init     # テーブルの初期化
python manage_db.py reset    # データベースのリセット
```

## API統合

データベースはFastAPIと統合されています：

- **ヘルスチェック**: `GET /health` - データベース状態を含む
- **テストエンドポイント**: `GET /api/db-test` - データアクセスの確認
- **依存性注入**: ルート用の `get_db()` 関数

## 開発ワークフロー

1. **初期セットアップ**:
   ```bash
   make setup  # データベースセットアップを含む
   ```

2. **モデル変更時**:
   ```bash
   # モデル修正後
   make db-revision  # マイグレーション作成
   make db-migrate   # マイグレーション適用
   ```

3. **フレッシュスタート**:
   ```bash
   make db-reset  # すべてをリセット
   ```

4. **状態確認**:
   ```bash
   make db-status  # 現在の状態を確認
   ```

## 環境変数

主要なデータベース環境変数（`.env`ファイルで設定）：

```bash
# 完全な接続文字列（優先）
DATABASE_URL=postgresql://username:password@host:port/database

# または個別設定
DATABASE_HOST=db                        # データベースホスト
DATABASE_PORT=5432                      # データベースポート
DATABASE_NAME=your_database_name        # データベース名
DATABASE_USER=your_username             # データベースユーザー
DATABASE_PASSWORD=your_password         # データベースパスワード
```

**セキュリティ注意事項**:
- 本番環境では強力なパスワードを使用してください
- `.env`ファイルは`.gitignore`に含まれており、バージョン管理されません
- 本番環境では環境変数やシークレット管理サービスを使用してください
- 開発用のデフォルト値は`.env.example`を参照してください
- 開発環境のデフォルト認証情報は`docker-compose.yml`で設定されています（本番では変更必須）

## トラブルシューティング

### よくある問題

1. **接続失敗**:
   - データベースコンテナが動作しているか確認: `docker-compose ps`
   - 環境変数の確認: `docker-compose run --rm backend env | grep DATABASE`
   - データベースログの確認: `make logs-db`
   - `.env`ファイルの設定確認（`.env.example`と比較）

2. **マイグレーションエラー**:
   - Alembicの状態確認: `make db-status`
   - `alembic/env.py` でのモデルインポートの確認
   - 必要に応じてリセット: `make db-reset`

3. **シーディングエラー**:
   - モデルとシードデータ間でのenum値の一致確認
   - 外部キー関係の確認
   - クリアして再シード: `make db-reset`

### 便利なコマンド

```bash
# データベースコンテナの確認
make logs-db

# データベースに直接接続
make db-connect

# データベース内のテーブル確認
make db-tables

# データベース内のデータ表示
make db-data
```

### 高度なデータベース操作

直接的なSQLクエリが必要な場合：

```bash
# インタラクティブなデータベース接続
make db-connect

# 接続後に使用できるコマンド例：
# \dt                    # テーブル一覧
# \d inquiries          # inquiriesテーブルの構造表示
# SELECT * FROM inquiries LIMIT 5;  # データの確認
# \q                    # 終了
```

### エラーハンドリングの改善

すべてのデータベースコマンドは適切なエラーハンドリングを行います：

- データベース接続チェックの出力が表示されるため、問題の診断が容易
- 接続失敗時は明確なエラーメッセージと終了コードを返す
- 各コマンドは自動的にデータベースコンテナを起動し、接続を確認してから実行

## セキュリティとクレデンシャル管理

### 開発環境

開発環境では以下のデフォルト認証情報が使用されます：
- データベース名: `gs_db`
- ユーザー名: `gs_user`  
- パスワード: `gs_password`

これらの値は`docker-compose.yml`と`.env.example`で定義されています。

### 本番環境での推奨事項

1. **強力なパスワードの使用**:
   ```bash
   # 例：ランダムパスワード生成
   openssl rand -base64 32
   ```

2. **環境変数での管理**:
   ```bash
   export DATABASE_PASSWORD="$(cat /run/secrets/db_password)"
   ```

3. **シークレット管理サービスの使用**:
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Kubernetes Secrets

4. **接続文字列の保護**:
   - ログファイルに認証情報を出力しない
   - 環境変数の値をマスクする
   - デバッグ出力で認証情報を隠す

### 認証情報の確認方法

開発環境で現在の設定を確認する場合：

```bash
# 環境変数の確認（パスワードはマスクされる）
make status

# データベース接続テスト
make db-status

# 設定ファイルの確認
cat .env.example  # テンプレート
```
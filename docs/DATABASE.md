# データベースセットアップと管理

このドキュメントは、ストーリーボードシステムのデータベースセットアップと管理について説明します。

## 概要

システムはPostgreSQLを主要データベースとして使用し、SQLAlchemy ORMとAlembicによるマイグレーション管理を行います。

## データベースモデル

### コアモデル

1. **InquiryModel** (`inquiries` テーブル)
   - ユーザーからの問い合わせ・リクエストを保存
   - フィールド: id, user_id, content, language, timestamp, status, metadata

2. **StoryModel** (`stories` テーブル)
   - 問い合わせから生成されたストーリーを保存
   - フィールド: id, inquiry_id, title, description, category, priority, estimated_effort, deadline, status, assignee, tags, dependencies, metadata, timestamps

3. **StoryTemplateModel** (`story_templates` テーブル)
   - パターン認識用のストーリーテンプレートを保存
   - フィールド: id, name, pattern, fields, checklist, default_estimate, is_custom, user_id, timestamps

## データベース接続

データベース接続は `backend/database.py` で管理されます：

- **接続文字列**: `postgresql://gs_user:gs_password@db:5432/gs_db`
- **セッション管理**: 依存性注入によるSQLAlchemy SessionLocal
- **ヘルスチェック**: 組み込み接続確認機能

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

主要なデータベース環境変数：

- `DATABASE_URL`: 完全な接続文字列
- `DATABASE_HOST`: データベースホスト（デフォルト: db）
- `DATABASE_PORT`: データベースポート（デフォルト: 5432）
- `DATABASE_NAME`: データベース名（デフォルト: gs_db）
- `DATABASE_USER`: データベースユーザー（デフォルト: gs_user）
- `DATABASE_PASSWORD`: データベースパスワード（デフォルト: gs_password）

## トラブルシューティング

### よくある問題

1. **接続失敗**:
   - データベースコンテナが動作しているか確認: `docker-compose ps`
   - 環境変数の確認: `docker-compose run --rm backend env | grep DATABASE`
   - データベースログの確認: `make logs-db`

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
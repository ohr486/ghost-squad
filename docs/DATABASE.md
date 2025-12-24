# データベースセットアップと管理

このドキュメントは、Ghost Squadのストーリーボードシステムのデータベースセットアップと管理について説明します。

## 概要

システムはPostgreSQLを主要データベースとして使用し、SQLAlchemy ORMとAlembicによるマイグレーション管理を行います。現在、問い合わせ管理機能が実装済みで、ストーリー管理機能は開発中です。

## データベースモデル

### 実装済みコアモデル

1. **InquiryModel** (`inquiries` テーブル) - **実装済み**
   - ユーザーからの問い合わせ・リクエストを保存
   - フィールド: id (BigInteger), user_id, content, language, timestamp, status, inquiry_metadata
   - タイムスタンプ: UTC timezone-aware datetime使用
   - API統合: 完全実装済み（作成・取得・一覧）

2. **StoryModel** (`stories` テーブル) - **実装済み（API開発中）**
   - 問い合わせから生成されたストーリーを保存
   - フィールド: id (BigInteger), inquiry_id (BigInteger), title, description, category, priority, estimated_effort, deadline, status, assignee, tags, dependencies, story_metadata, timestamps
   - タイムスタンプ: UTC timezone-aware datetime使用
   - 関係: InquiryModelとの外部キー関係

3. **StoryTemplateModel** (`story_templates` テーブル) - **実装済み（機能開発中）**
   - パターン認識用のストーリーテンプレートを保存
   - フィールド: id (BigInteger), name, pattern, fields, checklist, default_estimate, is_custom, user_id, timestamps
   - タイムスタンプ: UTC timezone-aware datetime使用

### ID型について

**重要な設計決定**: Ghost Squad 2.0以降、すべてのモデルのIDフィールドはBigInteger（64ビット整数）を使用します。

- **利点**:
  - パフォーマンスの向上（インデックス効率、結合処理の高速化）
  - ストレージ効率の改善（16バイト → 8バイト）
  - 順序性の保証（作成順序の把握が容易）
  - 外部システムとの統合の簡素化

- **自動インクリメント**: すべてのIDフィールドは自動インクリメントされます
- **範囲**: 1から9,223,372,036,854,775,807まで（64ビット符号付き整数）
- **実装状況**: 統合マイグレーション（`initial_schema_for_storyboard.py`）で実装済み

### タイムゾーン対応

すべてのモデルでタイムスタンプフィールドは `datetime.now(timezone.utc)` を使用し、Python 3.12以降の推奨事項に準拠しています。これにより：

- 適切なタイムゾーン処理の保証
- 将来の非推奨警告の回避
- 国際的なアプリケーションでの一貫した時刻管理

## データベース接続

データベース接続は `backend/database.py` で管理されます：

- **接続文字列の優先順位**:
  1. `DATABASE_URL` 環境変数（完全な接続文字列）
  2. 個別の `DATABASE_*` 環境変数から構築
  3. 開発用デフォルト値
- **セッション管理**: 依存性注入によるSQLAlchemy SessionLocal
- **ヘルスチェック**: 組み込み接続確認機能
- **デバッグ情報**: 接続情報の表示機能（パスワードは除く）

### 接続文字列の構築

システムは以下の優先順位で接続文字列を決定します：

1. **完全な接続文字列** (最優先):
   ```bash
   DATABASE_URL=postgresql://username:password@host:port/database
   ```

2. **個別環境変数から構築**:
   ```bash
   DATABASE_HOST=db                        # データベースホスト
   DATABASE_PORT=5432                      # データベースポート  
   DATABASE_NAME=your_database_name        # データベース名
   DATABASE_USER=your_username             # データベースユーザー
   DATABASE_PASSWORD=your_password         # データベースパスワード
   ```
   
   これらの変数から自動的に接続文字列を構築: `postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}`

3. **開発用デフォルト値**:
   - ホスト: `db`
   - ポート: `5432`
   - データベース名: `gs_db`
   - ユーザー名: `gs_user`
   - パスワード: `gs_password`

## マイグレーション管理

### Alembicセットアップ

Alembicはモデルと連携するよう設定されています：

- **設定ファイル**: `backend/alembic.ini`
- **環境設定**: `backend/alembic/env.py` (全モデルをインポート)
- **マイグレーション**: `backend/alembic/versions/`

### 統合マイグレーション

開発段階では、複数のマイグレーションファイルを一つの統合ファイルにまとめています：

- **統合マイグレーション**: `001_initial_schema_with_bigint_ids.py`
- **含まれる変更**:
  - BigInteger IDを使用した初期スキーマ作成
  - 適切なserver_defaultの設定
  - 外部キー制約の設定
  - JSON列のデフォルト値設定

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

# マイグレーション履歴リセット（開発用）
make db-reset-migrations

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

現在のシステムには以下のサンプルデータが含まれています：

1. **問い合わせ（4件）**:
   - ユーザー登録機能のリクエスト（完了済み）
   - バグ報告（緊急・処理中）
   - パフォーマンス調査リクエスト（処理中）
   - 認証機能追加リクエスト（受付済み）

2. **ストーリー（3件）**:
   - APIエンドポイント実装
   - UIフォーム実装
   - バグ修正タスク

3. **テンプレート（3件）**:
   - API開発テンプレート
   - バグ修正テンプレート
   - 調査テンプレート

**データ確認方法**:
```bash
# 現在のデータを確認
make db-data

# 特定のテーブルを確認
make db-connect
# 接続後: SELECT * FROM inquiries;
```

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
- **実装済みAPI**:
  - `POST /api/inquiries` - 問い合わせ作成
  - `GET /api/inquiries` - 問い合わせ一覧（ページネーション対応）
  - `GET /api/inquiries/{id}` - 特定問い合わせ取得

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

データベース接続用の環境変数（`.env`ファイルで設定）：

### 方法1: 完全な接続文字列（推奨）

```bash
# 完全な接続文字列（最優先）
DATABASE_URL=postgresql://username:password@host:port/database
```

### 方法2: 個別設定

```bash
# 個別環境変数（DATABASE_URLが未設定の場合に使用）
DATABASE_HOST=db                        # データベースホスト
DATABASE_PORT=5432                      # データベースポート
DATABASE_NAME=your_database_name        # データベース名
DATABASE_USER=your_username             # データベースユーザー
DATABASE_PASSWORD=your_password         # データベースパスワード
```

### その他のオプション

```bash
# SQLクエリのログ出力（開発用）
DATABASE_ECHO=false                     # true にするとSQLクエリをログ出力
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

## ID型変更に関する重要な注意事項

### 統合マイグレーション

開発段階では、複数のマイグレーションファイルを一つの統合ファイル（`001_initial_schema_with_bigint_ids.py`）にまとめています。これにより：

- **シンプルな管理**: 単一ファイルでスキーマ全体を管理
- **一貫性の保証**: BigInteger IDと適切なデフォルト値を最初から設定
- **開発効率**: 複雑なマイグレーション履歴を避けて開発に集中

### マイグレーション実行前の準備

新しい統合マイグレーションを使用する場合：

1. **既存データベースのリセット**:
   ```bash
   # 完全リセット（データ削除）
   make db-reset
   
   # または、マイグレーション履歴のみリセット
   make db-reset-migrations
   ```

2. **開発環境での確認**:
   ```bash
   # 統合マイグレーションの適用
   make db-migrate
   
   # 新しいID型でサンプルデータを投入
   make db-seed
   ```

### 本番環境への移行

本番環境では、既存のUUIDデータがある場合：

1. **データバックアップ**: 必ず事前にバックアップを取得
2. **段階的移行**: データエクスポート → スキーマ変更 → データインポート
3. **ダウンタイム計画**: ID型変更は破壊的変更のため、メンテナンス時間が必要

### データ移行について

既存のUUIDデータがある場合、以下の方法でデータを移行できます：

1. **データエクスポート**: 既存データをJSON形式でエクスポート
2. **マイグレーション実行**: ID型をBigIntegerに変更
3. **データインポート**: 新しいID型でデータを再インポート

### 外部システムとの統合

外部システム（Kanbanツールなど）との統合がある場合：

- 外部IDマッピングテーブルの更新が必要
- APIクライアントでのID型変更対応
- フロントエンドでの型定義更新（string → number）

### ロールバック手順

問題が発生した場合のロールバック：

```bash
# マイグレーションのロールバック
cd backend
python -m alembic downgrade -1

# または特定のリビジョンまでロールバック
python -m alembic downgrade 88d971444af5
```
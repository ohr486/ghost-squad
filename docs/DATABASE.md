# Ghost Squad データベース管理ガイド

Ghost Squadのデータベース管理に関する詳細ガイドです。

## 概要

Ghost SquadはPostgreSQL 15をデータベースとして使用し、SQLAlchemy ORMとAlembicによるマイグレーション管理を行います。

**データベース接続情報**
- **ホスト**: localhost（開発環境）
- **ポート**: 5432
- **データベース名**: gs_db
- **ユーザー名**: gs_user
- **パスワード**: gs_password（開発環境、本番環境では変更必須）

## データベース管理コマンド

### 基本操作

```bash
# データベースマイグレーション実行
make db-migrate

# 新しいマイグレーション作成（メッセージ入力を求められます）
make db-revision

# データベース状態確認
make db-status

# テストデータ投入
make db-seed

# データベースリセット（注意：全データ削除）
make db-reset

# マイグレーション履歴リセット
make db-reset-migrations

# Alembic初期化（通常は不要、初回セットアップ時のみ）
make db-init
```

### データ確認・操作

```bash
# データベースに直接接続（psqlインタラクティブモード）
make db-connect

# データベーステーブル一覧表示
make db-tables

# データベース内のデータ表示
make db-data
```

### ログ確認

```bash
# データベースログ表示
make logs-db
```

## データベースの初期化

### 初回セットアップ時

`make setup`コマンドに含まれていますが、個別に実行する場合：

```bash
# 1. データベースマイグレーション実行
make db-migrate

# 2. テストデータ投入
make db-seed
```

## 日常的なデータベース操作

### データベースの状態確認

```bash
# マイグレーション状態とAlembic設定を確認
make db-status
```

**出力例**:
```
📊 Checking database and Alembic status...
✅ Database is ready!

📋 Alembic Configuration:
  ✅ alembic.ini exists
  ✅ alembic directory exists

📊 Migration Status:
  Current revision: a1b2c3d4e5f6 (head)

📋 Available migrations:
  a1b2c3d4e5f6 (head) -> Initial migration
```

### データの確認

```bash
# データベース内の全データを表形式で確認
make db-data
```

**出力例**:
```
📋 Inquiries (問い合わせ):
 id | user_id |              content_preview              | source_system | status  |      timestamp
----+---------+-------------------------------------------+---------------+---------+---------------------
  1 | user123 | ユーザーがログインできる機能が欲しい...   | manual        | received| 2024-01-01 00:00:00

📋 Stories (ストーリー):
 id | inquiry_id |              title_preview              | priority | status          | estimated_effort |      created_at
----+------------+-----------------------------------------+----------+-----------------+-----------------+---------------------
  1 |          1 | ユーザーログイン機能...                  | high     | waiting_review  |                5 | 2024-01-01 00:00:00

📋 Import Error Logs (インポートエラーログ):
 id | error_code | plugin_type |           message_preview            | resolved |      occurred_at
----+------------+-------------+--------------------------------------+----------+---------------------
  1 | GS-320     | email       | IMAP接続エラー...                    | f        | 2024-01-01 00:00:00
```

### テーブル構造の確認

```bash
# データベース内のテーブル一覧と構造を確認
make db-tables
```

**出力例**:
```
📊 Database tables:
                 List of relations
 Schema |         Name          | Type  |  Owner
--------+-----------------------+-------+---------
 public | inquiries             | table | gs_user
 public | stories               | table | gs_user
 public | import_error_logs     | table | gs_user
 public | alembic_version       | table | gs_user

📋 Table details:

🔍 Table: inquiries
        Column        |           Type            | Nullable
----------------------+---------------------------+----------
 id                   | bigint                    | not null
 user_id              | character varying(50)     | not null
 content              | text                      | not null
 source_system        | character varying(50)     | not null
 timestamp            | timestamp with time zone  | not null
 status               | character varying         | not null
 inquiry_metadata     | jsonb                     | not null
 created_at           | timestamp with time zone  | not null
 updated_at           | timestamp with time zone  | not null
```

### インタラクティブなデータベース接続

```bash
# psqlで直接接続
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

-- 特定の条件でデータ取得
SELECT * FROM inquiries WHERE status = 'received';

-- 集計
SELECT status, COUNT(*) FROM inquiries GROUP BY status;

-- 終了
\q
```

## 開発時のデータベース操作

### モデル変更時のワークフロー

1. **SQLAlchemyモデルを変更**
   - `api/models/database/` 配下のモデルファイルを編集

2. **新しいマイグレーションを作成**
   ```bash
   make db-revision
   # メッセージ入力例: "Add deadline field to stories"
   ```

3. **マイグレーションファイルを確認**
   - `api/alembic/versions/` に生成されたファイルを確認
   - 必要に応じて手動で修正

4. **マイグレーションを適用**
   ```bash
   make db-migrate
   ```

5. **変更を確認**
   ```bash
   make db-tables
   make db-data
   ```

### 開発用データの再投入

```bash
# 既存データをクリアして新しいテストデータを投入
make db-seed
```

**seed_data.pyの内容**:
- サンプル問い合わせデータ
- サンプルストーリーデータ

## データベーススキーマ

### テーブル定義

#### inquiries（問い合わせ）

| カラム名 | 型 | 説明 | 制約 |
|---------|-----|------|------|
| id | BigInteger | 一意識別子 | PRIMARY KEY, AUTO_INCREMENT |
| user_id | String(50) | ユーザーID | NOT NULL |
| content | Text | 問い合わせ内容 | NOT NULL |
| source_system | String(50) | 送信元システム（例: manual, email, chat） | NOT NULL |
| timestamp | DateTime | タイムスタンプ | NOT NULL |
| status | Enum(InquiryStatus) | ステータス | NOT NULL |
| created_at | DateTime | 作成日時 | NOT NULL |
| updated_at | DateTime | 更新日時 | NOT NULL |
| inquiry_metadata | JSON | メタデータ（却下理由、ステータス履歴等） | NULLABLE |

**ステータス値**:
- `received` - 受付済み（初期状態）
- `task_working` - タスク作業中（承認後）
- `processing` - AI処理中
- `completed` - 完了
- `rejected` - 却下
- `needs_clarification` - 明確化要求
- `failed` - 失敗

**インデックス**:
- `ix_inquiries_user_id` - ユーザーID
- `ix_inquiries_status` - ステータス
- `ix_inquiries_timestamp` - タイムスタンプ

#### stories（ストーリー）

| カラム名 | 型 | 説明 | 制約 |
|---------|-----|------|------|
| id | BigInteger | 一意識別子 | PRIMARY KEY, AUTO_INCREMENT |
| inquiry_id | Integer | 問い合わせID | FOREIGN KEY → inquiries.id (CASCADE) |
| title | String(500) | タイトル | NOT NULL, CHECK(length ≤ 500, trim > 0) |
| description | Text | 説明 | NOT NULL, CHECK(trim > 0) |
| priority | Enum(Priority) | 優先度 | NOT NULL, DEFAULT 'medium' |
| status | Enum(StoryStatus) | ステータス | NOT NULL, DEFAULT 'waiting_review' |
| estimated_effort | Float | 推定工数 | NULLABLE |
| deadline | DateTime(tz) | 期限 | NULLABLE |
| assignee | String(50) | 担当者 | NULLABLE |
| story_metadata | JSON | メタデータ | NOT NULL, DEFAULT '{}' |
| created_at | DateTime(tz) | 作成日時 | NOT NULL |
| updated_at | DateTime(tz) | 更新日時 | NOT NULL |

**優先度値**:
- `low` - 低
- `medium` - 中（デフォルト）
- `high` - 高
- `urgent` - 緊急

**ステータス値**:
- `waiting_review` - レビュー待ち（デフォルト）
- `approved` - 承認済み
- `rejected` - 却下

**チェック制約**:
- `chk_stories_title` - タイトルは500文字以下かつ空白のみ不可
- `chk_stories_description` - 説明は空白のみ不可

**インデックス**:
- `ix_stories_inquiry_id` - 問い合わせID
- `ix_stories_status` - ステータス
- `ix_stories_priority` - 優先度

#### import_error_logs（インポートエラーログ）

| カラム名 | 型 | 説明 | 制約 |
|---------|-----|------|------|
| id | BigInteger | 一意識別子 | PRIMARY KEY, AUTO_INCREMENT |
| error_code | String(10) | エラーコード（GS-301〜GS-399） | NOT NULL |
| plugin_type | String(50) | データソースプラグイン種別 | NOT NULL |
| source_id | String(255) | 外部システムID（Message-ID等） | NULLABLE |
| error_message | String(1000) | エラーメッセージ | NOT NULL |
| occurred_at | DateTime(tz) | エラー発生日時 | NOT NULL |
| resolved | Boolean | 解決済みフラグ | NOT NULL, DEFAULT false |
| created_at | DateTime(tz) | 作成日時 | NOT NULL |
| updated_at | DateTime(tz) | 更新日時 | NOT NULL |

**インデックス**:
- `ix_import_error_logs_code_occurred` - エラーコード + 発生日時（複合）
- `ix_import_error_logs_plugin` - プラグイン種別
- `ix_import_error_logs_resolved` - 解決済みフラグ

## トラブルシューティング

### マイグレーションエラー

**問題**: `make db-migrate`でエラーが発生する

**解決方法**:
```bash
# 1. データベース状態確認
make db-status

# 2. ログでエラー詳細を確認
make logs-db

# 3. データベースリセット（注意：データが削除されます）
make db-reset
make db-migrate
```

**よくあるエラー**:
- **"relation already exists"**: テーブルが既に存在している
  - 解決: `make db-reset` でリセット
- **"column does not exist"**: カラムが存在しない
  - 解決: マイグレーションファイルを確認・修正
- **"syntax error"**: SQL構文エラー
  - 解決: マイグレーションファイルの構文を確認

### 接続エラー

**問題**: データベースに接続できない

**解決方法**:
```bash
# 1. データベースコンテナの状態確認
make status

# 2. データベースログ確認
make logs-db

# 3. データベース接続テスト
make db-connect

# 4. コンテナ再起動
docker-compose restart db

# 5. 完全リセット
make clean
make setup
```

**確認ポイント**:
- Dockerコンテナが起動しているか: `docker ps | grep gs-db`
- ポート5432が使用可能か: `lsof -i :5432`
- 環境変数が正しく設定されているか: `cat .env | grep DATABASE`

### データが表示されない

**問題**: `make db-data`でデータが表示されない

**解決方法**:
```bash
# 1. データベース内のデータ確認
make db-data

# 2. テーブル構造確認
make db-tables

# 3. テストデータの再投入
make db-seed

# 4. 直接SQLで確認
make db-connect
# psql内で
SELECT COUNT(*) FROM inquiries;
SELECT COUNT(*) FROM stories;
```

### マイグレーション履歴の不整合

**問題**: マイグレーション履歴が不整合な状態になっている

**解決方法**:
```bash
# 1. 現在の状態確認
make db-status

# 2. マイグレーション履歴リセット
make db-reset-migrations

# 3. 確認
make db-status
make db-data
```

### ディスク容量不足

**問題**: データベースボリュームがディスク容量を圧迫している

**解決方法**:
```bash
# 1. ディスク使用量確認
make disk-usage

# 2. Dockerボリューム確認
make volume-list

# 3. 未使用ボリューム削除
make volume-cleanup

# 4. 強制クリーンアップ（注意：データが削除されます）
make volume-cleanup-force
```

## データベース最適化

### VACUUM実行

PostgreSQLのVACUUM処理で不要なデータを削除し、パフォーマンスを改善します。

```bash
make db-connect

# psql内で
VACUUM ANALYZE inquiries;
VACUUM ANALYZE stories;
VACUUM ANALYZE import_error_logs;

# 完全VACUUM（時間がかかる）
VACUUM FULL;
```

### インデックスの再構築

```sql
-- psql内で
REINDEX TABLE inquiries;
REINDEX TABLE stories;
REINDEX TABLE import_error_logs;
```

### クエリパフォーマンス分析

```sql
-- psql内で
EXPLAIN ANALYZE SELECT * FROM inquiries WHERE status = 'received';
EXPLAIN ANALYZE SELECT * FROM stories WHERE priority = 'high';
```

## バックアップとリストア

### データベースバックアップ

```bash
# PostgreSQLダンプ作成
docker-compose exec db pg_dump -U gs_user gs_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 圧縮バックアップ
docker-compose exec db pg_dump -U gs_user gs_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### データベースリストア

```bash
# SQLファイルからリストア
cat backup_20240101_120000.sql | docker-compose exec -T db psql -U gs_user gs_db

# 圧縮ファイルからリストア
gunzip -c backup_20240101_120000.sql.gz | docker-compose exec -T db psql -U gs_user gs_db
```

## 本番環境への移行

本番環境でデータベースをセットアップする際の注意点：

1. **環境変数の変更**
   ```bash
   # .envファイルで必ず変更
   DATABASE_PASSWORD=<強固なパスワード>
   SECRET_KEY=<ランダムな文字列>
   ENVIRONMENT=production
   DEBUG=false
   ```

2. **SSL接続の有効化**
   - PostgreSQL設定でSSLを有効化
   - 接続文字列に`?sslmode=require`を追加

3. **バックアップの自動化**
   - cronジョブでバックアップスクリプトを定期実行
   - バックアップファイルの保管場所を設定

4. **監視設定**
   - データベース接続数の監視
   - ディスク使用量の監視
   - クエリパフォーマンスの監視

## 関連ドキュメント

- [API仕様](API.md)
- [Spec-Driven Development](SDD.md)
- [README](../README.md)

# Ghost Squad トラブルシューティング & デバッグガイド

Ghost Squadの開発中に発生する問題の解決方法とデバッグテクニックをまとめたガイドです。

## 概要

このガイドでは、Ghost Squad開発中によくある問題とその解決方法を記載しています。問題に直面した際は、まず該当するセクションを確認してください。

**クイック診断**:
```bash
# 環境の状態確認
make status

# ログで問題を確認
make logs

# ディスク容量確認
make disk-usage
```

## よくある問題と解決方法

### Docker関連の問題

#### 問題1: `make dev` でコンテナが起動しない

**症状**:
```
ERROR: Cannot start service api: ...
ERROR: Cannot start service web: ...
```

**原因**:
- Dockerデーモンが起動していない
- ディスク容量不足
- 以前のコンテナが残っている

**解決方法**:

1. **Dockerの状態確認**
```bash
# Dockerが起動しているか確認
docker ps

# Dockerを再起動
# macOS: Docker Desktop を再起動
# Linux: sudo systemctl restart docker
```

2. **環境のクリーンアップ**
```bash
make clean
make setup
make dev
```

3. **ディスク容量の確認**
```bash
make disk-usage

# 必要に応じてクリーンアップ
make docker-cleanup
```

#### 問題2: ポートが既に使用されている

**症状**:
```
ERROR: for api  Cannot start service api: driver failed programming external connectivity
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**原因**: ポート 3000、8000、5432 が他のプロセスで使用されている

**解決方法**:

1. **使用中のポートを確認**
```bash
# macOS/Linux
lsof -i :3000  # フロントエンド
lsof -i :8000  # バックエンド
lsof -i :5432  # PostgreSQL

# プロセスIDを確認して終了
kill -9 <PID>
```

2. **Ghost Squadのコンテナを停止**
```bash
make stop

# 完全に削除
docker-compose down
```

3. **再起動**
```bash
make dev
```

#### 問題3: Dockerイメージのビルドが失敗する

**症状**:
```
ERROR: failed to solve: failed to compute cache key: ...
```

**原因**:
- Dockerfileの構文エラー
- ネットワーク問題
- キャッシュの問題

**解決方法**:

1. **キャッシュをクリアして再ビルド**
```bash
docker-compose build --no-cache

# または
make clean
make setup
```

2. **ネットワーク接続の確認**
```bash
# インターネット接続を確認
ping google.com
```

#### 問題4: コンテナが頻繁に再起動する

**症状**:
```bash
make status
# STATUS列が "Restarting" になっている
```

**原因**:
- アプリケーションのクラッシュ
- 設定エラー
- メモリ不足

**解決方法**:

1. **ログで原因を確認**
```bash
make logs-backend  # または logs-frontend, logs-db

# リアルタイムで監視
docker-compose logs -f api
```

2. **環境変数の確認**
```bash
cat .env

# .env.exampleと比較
diff .env .env.example
```

3. **Dockerリソースの確認**
```bash
# Docker Desktop設定でメモリ・CPUを確認
# 推奨: メモリ 4GB以上、CPU 2コア以上
```

### データベース関連の問題

データベース関連の詳細なトラブルシューティングは [DATABASE.md](DATABASE.md) も参照してください。

#### 問題5: データベースに接続できない

**症状**:
```
sqlalchemy.exc.OperationalError: could not connect to server
connection refused
```

**原因**:
- データベースコンテナが起動していない
- 環境変数の設定ミス
- ネットワークの問題

**解決方法**:

1. **データベースコンテナの状態確認**
```bash
make status

# データベースログを確認
make logs-db
```

2. **環境変数の確認**
```bash
cat .env | grep DATABASE

# 正しい設定例:
# DATABASE_URL=postgresql://gs_user:gs_password@db:5432/gs_db
```

3. **データベース接続テスト**
```bash
make db-connect

# psqlが起動すれば接続成功
# \q で終了
```

4. **データベースコンテナを再起動**
```bash
docker-compose restart db

# または完全リセット
make db-reset
```

#### 問題6: マイグレーションエラー

**症状**:
```
alembic.util.exc.CommandError: Target database is not up to date
ERROR: relation "table_name" already exists
```

**原因**:
- マイグレーション履歴の不整合
- データベーススキーマの手動変更
- マイグレーションファイルの競合

**解決方法**:

1. **マイグレーション状態を確認**
```bash
make db-status
```

2. **マイグレーション履歴をリセット**
```bash
make db-reset-migrations
```

3. **データベースを完全リセット**（注意：データが削除されます）
```bash
make db-reset
```

4. **マイグレーションファイルの確認**
```bash
ls -la api/alembic/versions/

# 重複や競合がないか確認
```

#### 問題7: データが表示されない

**症状**:
- APIは正常に動作するが、データが返ってこない
- データベースが空

**原因**:
- テストデータが投入されていない
- データベースがリセットされた

**解決方法**:

1. **データの存在確認**
```bash
make db-data

# または
make db-connect
# psql内で
SELECT COUNT(*) FROM inquiries;
SELECT COUNT(*) FROM stories;
```

2. **テストデータを投入**
```bash
make db-seed
```

3. **データを確認**
```bash
make db-data
```

### API関連の問題

API関連の詳細なトラブルシューティングは [API.md](API.md) も参照してください。

#### 問題8: OpenAI APIエラー

**症状**:
```
openai.error.AuthenticationError: Incorrect API key provided
openai.error.RateLimitError: Rate limit exceeded
```

**原因**:
- APIキーが未設定または不正
- レート制限に達した
- 残高不足

**解決方法**:

1. **APIキーの確認**
```bash
cat .env | grep OPENAI_API_KEY

# 正しく設定されているか確認
```

2. **OpenAI アカウントの確認**
- https://platform.openai.com/account/api-keys でキーを確認
- https://platform.openai.com/account/billing で残高を確認
- https://platform.openai.com/account/rate-limits でレート制限を確認

3. **環境変数を更新して再起動**
```bash
# .envファイルを編集
vi .env

# サービスを再起動
make restart
```

#### 問題9: CORS エラー

**症状**:
```
Access to fetch at 'http://localhost:8000/api/...' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**原因**:
- バックエンドのCORS設定が不適切
- フロントエンドのURLが許可されていない

**解決方法**:

1. **環境変数の確認**
```bash
cat .env | grep CORS

# 正しい設定例:
# CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

2. **.envファイルを更新**
```bash
# .envに追加
echo "CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000" >> .env
```

3. **バックエンドを再起動**
```bash
make restart
```

4. **ブラウザのキャッシュをクリア**
```bash
# ブラウザの開発者ツールで
# Application > Clear storage > Clear site data
```

#### 問題10: APIレスポンスが遅い

**症状**:
- APIリクエストに10秒以上かかる
- タイムアウトエラーが発生

**原因**:
- データベースクエリが非効率
- AI API呼び出しのタイムアウト
- ネットワークの問題
- リソース不足

**解決方法**:

1. **ログでボトルネックを特定**
```bash
make logs-backend | grep -i "slow\|timeout\|error"
```

2. **データベースパフォーマンスの確認**
```bash
make db-connect

-- psql内で
EXPLAIN ANALYZE SELECT * FROM inquiries WHERE status = 'received';
```

3. **Dockerリソースの確認**
```bash
docker stats

# メモリやCPU使用率が高い場合、Docker Desktopの設定を調整
```

4. **データベースの最適化**
```bash
make db-connect

-- psql内で
VACUUM ANALYZE inquiries;
VACUUM ANALYZE stories;
```

### ビルド・依存関係の問題

#### 問題11: Python依存関係のインストールエラー

**症状**:
```
ERROR: Could not find a version that satisfies the requirement package_name
ERROR: No matching distribution found for package_name
```

**原因**:
- requirements.txt の記述ミス
- Pythonバージョンの不一致
- ネットワーク問題

**解決方法**:

1. **Pythonバージョンの確認**
```bash
docker-compose run --rm api python --version
# Python 3.11以上が必要
```

2. **依存関係を再インストール**
```bash
docker-compose run --rm api pip install -r requirements.txt

# キャッシュをクリアして再インストール
docker-compose run --rm api pip install --no-cache-dir -r requirements.txt
```

3. **requirements.txtの確認**
```bash
cat api/requirements.txt

# 構文エラーや不正なバージョン指定がないか確認
```

#### 問題12: Node.js依存関係のインストールエラー

**症状**:
```
npm ERR! code ENOENT
npm ERR! Cannot find module 'package-name'
```

**原因**:
- package.json の記述ミス
- node_modules の破損
- ネットワーク問題

**解決方法**:

1. **node_modulesを削除して再インストール**
```bash
make clean-deep
make setup
```

2. **個別に再インストール**
```bash
docker-compose run --rm web npm install

# キャッシュをクリアして再インストール
docker-compose run --rm web npm cache clean --force
docker-compose run --rm web npm install
```

3. **package.jsonの確認**
```bash
cat web/package.json

# 構文エラーがないか確認
```

#### 問題13: TypeScriptコンパイルエラー

**症状**:
```
TS2307: Cannot find module 'module-name'
TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'
```

**原因**:
- 型定義ファイルの不足
- tsconfig.jsonの設定ミス
- 型の不一致

**解決方法**:

1. **型定義をインストール**
```bash
docker-compose run --rm web npm install --save-dev @types/package-name
```

2. **TypeScript設定の確認**
```bash
cat web/tsconfig.json

# strictモードの確認
```

3. **型チェックを実行**
```bash
make lint-frontend

# または直接実行
docker-compose run --rm web npm run type-check
```

### テスト関連の問題

#### 問題14: テストが失敗する

**症状**:
```
FAILED tests/test_something.py::test_function - AssertionError
```

**原因**:
- テストデータの問題
- データベース状態の問題
- テストコードのバグ

**解決方法**:

1. **詳細なテスト出力を確認**
```bash
# バックエンド
docker-compose run --rm api pytest tests/ -v --tb=long

# 特定のテストのみ実行
docker-compose run --rm api pytest tests/test_specific.py::test_function -v
```

2. **データベースをリセット**
```bash
make db-reset
```

3. **テスト環境を確認**
```bash
# テスト用の環境変数
cat .env | grep TEST

# テストデータベースの確認
```

#### 問題15: カバレッジレポートが生成されない

**症状**:
- カバレッジレポートが表示されない
- htmlcovディレクトリが空

**原因**:
- pytest-covがインストールされていない
- 設定ファイルの問題

**解決方法**:

1. **pytest-covのインストール確認**
```bash
docker-compose run --rm api pip list | grep pytest-cov
```

2. **カバレッジ設定の確認**
```bash
cat api/.coveragerc

# または
cat api/pyproject.toml
```

3. **明示的にカバレッジを指定して実行**
```bash
docker-compose run --rm api pytest tests/ --cov=. --cov-report=html
```

### パフォーマンス関連の問題

#### 問題16: ホットリロードが遅い

**症状**:
- ファイル変更後、反映に時間がかかる
- ブラウザのリロードが遅い

**原因**:
- ファイルウォッチャーの問題
- Dockerボリュームのパフォーマンス
- システムリソース不足

**解決方法**:

1. **環境変数の確認**（フロントエンド）
```bash
cat .env | grep CHOKIDAR
# CHOKIDAR_USEPOLLING=true が設定されているか確認
```

2. **Dockerボリュームの最適化**（macOS）
```yaml
# docker-compose.ymlで
volumes:
  - ./web:/app:delegated  # delegatedオプションを追加
```

3. **システムリソースの確認**
```bash
# CPU・メモリ使用率を確認
docker stats
```

#### 問題17: ビルドが遅い

**症状**:
- `make setup` や `docker-compose build` に時間がかかる

**原因**:
- キャッシュが効いていない
- ネットワークが遅い
- ディスク I/O が遅い

**解決方法**:

1. **ビルドキャッシュの確認**
```bash
# キャッシュを利用してビルド
docker-compose build

# キャッシュをクリアして再ビルド（遅い）
docker-compose build --no-cache
```

2. **.dockerignoreの確認**
```bash
cat .dockerignore

# 不要なファイルが除外されているか確認
```

3. **ネットワーク接続の確認**
```bash
# インターネット速度をテスト
curl -o /dev/null http://cachefly.cachefly.net/10mb.test
```

### その他の問題

#### 問題18: `.env`ファイルが反映されない

**症状**:
- 環境変数を変更しても反映されない
- デフォルト値が使用される

**原因**:
- コンテナを再起動していない
- .envファイルの記述ミス

**解決方法**:

1. **.envファイルの確認**
```bash
cat .env

# 構文エラーがないか確認
# KEY=VALUE 形式
# スペースや引用符に注意
```

2. **コンテナを再起動**
```bash
make restart

# または完全に再起動
make stop
make dev
```

3. **環境変数が読み込まれているか確認**
```bash
docker-compose exec api env | grep DATABASE_URL
docker-compose exec web env | grep REACT_APP
```

#### 問題19: コマンドが見つからない

**症状**:
```
make: *** No rule to make target 'xxx'.  Stop.
```

**原因**:
- コマンド名のタイプミス
- Makefileが更新されていない

**解決方法**:

1. **利用可能なコマンドを確認**
```bash
make help
```

2. **Makefileの確認**
```bash
cat Makefile | grep "^[a-zA-Z]"
```

3. **コマンドリファレンスを確認**
- [COMMAND.md](COMMAND.md) - 全コマンドの一覧

## デバッグツールとテクニック

### ログの読み方

#### バックエンドログ
```bash
# リアルタイムでログを表示
make logs-backend

# 特定のパターンを検索
make logs-backend | grep -i "error\|warning"

# エラースタックトレースを確認
make logs-backend | grep -A 20 "Traceback"
```

#### フロントエンドログ
```bash
# リアルタイムでログを表示
make logs-frontend

# ビルドエラーを確認
make logs-frontend | grep -i "error\|failed"

# ブラウザのコンソールログも確認
# 開発者ツール (F12) > Console
```

#### データベースログ
```bash
# データベースログを表示
make logs-db

# 接続エラーを確認
make logs-db | grep -i "error\|fatal"

# スロークエリを確認（設定により）
make logs-db | grep -i "slow"
```

### インタラクティブデバッグ

#### Pythonデバッガー（pdb）

**コードにブレークポイントを設定**:
```python
# api/main.pyなどに追加
import pdb; pdb.set_trace()
```

**デバッガーを使用してコンテナを起動**:
```bash
# docker-compose.ymlのcommandを変更
# command: uvicorn main:app --reload
# ↓
# command: python -m pdb main.py

# またはipdbを使用
docker-compose run --rm api pip install ipdb
# コード内で: import ipdb; ipdb.set_trace()
```

#### データベースクエリのデバッグ

```bash
# psqlで直接クエリを実行
make db-connect

-- psql内で
\x  -- 拡張表示モード
SELECT * FROM inquiries LIMIT 1;

-- クエリプランを確認
EXPLAIN ANALYZE SELECT * FROM inquiries WHERE status = 'received';
```

#### APIリクエストのデバッグ

```bash
# curlでAPIをテスト
curl -X GET http://localhost:8000/api/inquiries

# 詳細な出力
curl -v -X POST http://localhost:8000/api/inquiries \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","content":"test inquiry","language":"ja"}'

# または Thunder Client (VS Code拡張) や Postman を使用
```

### パフォーマンスプロファイリング

#### バックエンドプロファイリング

```python
# cProfileを使用
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# プロファイリングしたいコード
...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

#### フロントエンドプロファイリング

```bash
# React DevTools Profilerを使用
# ブラウザ拡張をインストール
# 開発者ツール > Profiler タブ

# Lighthouseでパフォーマンス測定
# Chrome DevTools > Lighthouse > Generate report
```

## 環境のリセット手順

### レベル1: サービスの再起動
```bash
make restart
```
**用途**: 設定変更の反映、軽微な問題の解決

### レベル2: 環境のクリーンアップ
```bash
make clean
make setup
make dev
```
**用途**: キャッシュ削除、一般的な問題の解決

### レベル3: データベースのリセット
```bash
make db-reset
```
**用途**: データベース関連の問題解決（データは削除されます）

### レベル4: 完全リセット
```bash
make clean-deep
make setup
make dev
```
**用途**: node_modules含めた完全なリセット、深刻な問題の解決

### レベル5: Dockerの完全クリーンアップ
```bash
# すべてのコンテナ・ボリューム・イメージを削除
docker-compose down -v --rmi all
docker system prune -a --volumes -f

# 再セットアップ
make setup
make dev
```
**用途**: Docker関連の深刻な問題、ディスク容量の確保

## ヘルプとサポート

### 問題が解決しない場合

1. **ログを確認**
```bash
make logs > logs.txt
# logs.txtをチームに共有
```

2. **環境情報を収集**
```bash
make status
docker --version
docker-compose --version
uname -a  # OS情報
```

3. **関連ドキュメントを確認**
- [COMMAND.md](COMMAND.md) - コマンドリファレンス
- [DATABASE.md](DATABASE.md) - データベース管理
- [API.md](API.md) - API仕様
- [SDD.md](SDD.md) - 開発ワークフロー

4. **GitHub Issuesで報告**
- 問題の詳細な説明
- エラーメッセージ（全文）
- 再現手順
- 環境情報（OS, Docker version等）
- ログファイル

## チェックリスト

問題に直面した際の診断チェックリスト：

### 初期診断
- [ ] `make status` で状態確認
- [ ] `make logs` でエラーログ確認
- [ ] `.env` ファイルが存在し、正しく設定されているか
- [ ] Dockerが起動しているか（`docker ps`）
- [ ] ディスク容量は十分か（`make disk-usage`）

### Docker関連
- [ ] コンテナが起動しているか（`docker-compose ps`）
- [ ] ポート競合はないか（`lsof -i :8000`等）
- [ ] イメージが正しくビルドされているか
- [ ] Dockerリソース（メモリ・CPU）は十分か

### データベース関連
- [ ] データベースコンテナが起動しているか
- [ ] マイグレーションが適用されているか（`make db-status`）
- [ ] テストデータが投入されているか（`make db-data`）
- [ ] データベース接続情報は正しいか（`.env`）

### API関連
- [ ] バックエンドが起動しているか（`curl http://localhost:8000/health`）
- [ ] 環境変数が正しく設定されているか
- [ ] CORS設定は適切か
- [ ] OpenAI APIキーは有効か（AI機能を使用する場合）

### フロントエンド関連
- [ ] フロントエンドが起動しているか（`curl http://localhost:3000`）
- [ ] ビルドエラーはないか（`make logs-frontend`）
- [ ] node_modulesが正しくインストールされているか
- [ ] ブラウザのキャッシュをクリアしたか

## 関連ドキュメント

- [README.md](../README.md) - プロジェクト概要
- [COMMAND.md](COMMAND.md) - 開発コマンドリファレンス
- [API.md](API.md) - API仕様とトラブルシューティング
- [DATABASE.md](DATABASE.md) - データベース管理とトラブルシューティング
- [SDD.md](SDD.md) - Spec-Driven Development
- [CLAUDE.md](../CLAUDE.md) - AI開発アシスタント向けガイド

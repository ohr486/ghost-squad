# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

Ghost-Squadは、攻殻機動隊にインスパイアされた「Living Kanban」コンセプトを特徴とするマルチエージェントAIシステムです。システムは3つの主要アプリケーションで構成されています：

- **API (バックエンド)**: LangGraphベースのエージェントオーケストレーションを持つFastAPIサーバー
- **Web (フロントエンド)**: ドラッグ&ドロップ可能なカンバンボードを備えたNext.js 14アプリケーション
- **CLI**: Bubble Teaを使用したGo製TUI（ターミナルユーザーインターフェース）

アーキテクチャは、LangGraphを使用して「ゴーストブレイン」を作成し、協調するエージェントノード（planner → worker → reporter）を通じてミッションを処理します。フロントエンドは、ドラッグ&ドロップ機能とバックエンドの自動同期を備えたリアルタイムタスク可視化を提供します。

## 開発コマンド

### クイックスタート
```bash
# 全サービスの起動（推奨）
docker-compose up

# テストの実行
make test

# コードのフォーマット
make format

# コードのLint
make lint
```

### Docker Compose
```bash
# 全サービスの起動（API、Web、PostgreSQL、Redis）
docker-compose up
docker-compose up -d          # デタッチモード

# 特定のサービスを起動
docker-compose up api
docker-compose up web

# 全サービスの停止
docker-compose down
docker-compose down -v        # ボリュームも削除

# ログの表示
make logs                     # 全サービス
make api-logs                 # APIのみ
make web-logs                 # Webのみ

# コンテナの再ビルド
make build
make restart                  # Down + Up
```

### テスト
```bash
make test           # 全テストの実行（API + Web）
make test-api       # APIテストのみ（pytestとasyncio）
make test-web       # Webテストのみ（Jest）
```

**注意**: テストはインメモリSQLiteと`aiosqlite`を使用して非同期テストを実行します。APIテストは成功しますが、コマンドがタイムアウトする場合があります（現在はテストをスキップしてこの問題を回避しています）。

### コード品質
```bash
# Pythonコードのフォーマット（Black + Isort）
make format

# 全コードのLint
make lint           # API（Flake8、Black、Isort）+ Web（ESLint）
make lint-api       # APIのみ
make lint-web       # Webのみ
```

### データベース管理
```bash
# データベースのリセット（ボリュームを削除して再作成）
make db-reset

# PostgreSQLシェルへのアクセス
make db

# SQLクエリの実行
make dbe Q='SELECT * FROM missions;'
```

データベース認証情報: `ghost/squad_password`、データベース名: `ghost_memory`

### CLI
```bash
# DockerでCLIを実行
make cli

# または直接実行
docker-compose run --rm cli
```

### クリーンアップ
```bash
# 全コンテナ、ボリューム、キャッシュ、node_modulesを削除
make clean
```

### 手動開発（Dockerなし）

**API:**
```bash
cd apps/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
必要条件: PostgreSQL（ポート5432）とRedis（ポート6379）

**Web:**
```bash
cd apps/web
npm install
npm run dev         # 開発サーバー
npm run build       # プロダクションビルド
npm start           # プロダクションサーバー
```

## アーキテクチャ

### コアデータフロー

1. ユーザーがWeb UIまたはCLI経由でミッション指示を送信
2. APIがデータベースにミッションを作成し、バックグラウンドタスクをキューに追加
3. バックグラウンドタスクがLangGraphの`ghost_brain`ワークフローを実行
4. Plannerノードが OpenAI LLMを呼び出す（エラー時はフォールバックシミュレーション）
5. タスクがステータス、担当者、エネルギーコストと共にデータベースに作成される
6. フロントエンドが2秒ごとに`/missions`をポーリングしてUIを更新
7. ユーザーがカンバンボードでタスクをドラッグ＆ドロップすると、バックエンドへPATCH更新がトリガーされる

### エージェントシステム（LangGraph）

`apps/api/agents/`に配置：

**state.py** - `AgentState`（共有メモリ構造）を定義：
- `mission_id`: 一意の識別子
- `task_input`: ユーザーの指示
- `current_plan`: AI生成のワークブレイクダウンストラクチャ（WBS）
- `logs`: デバッグ用の思考ログ
- `status`: `'planning'`、`'working'`、または`'done'`
- `energy_used`: USD単位のコスト追跡

**graph.py** - 3つの連続するノードを持つLangGraphワークフロー：
- `node_planner`: OpenAI LLMを使用して指示を3〜5つのタスクに分解（日本語出力）。APIエラー時はシミュレーションにフォールバック
- `node_worker`: `time.sleep(1.5)`と"tachikoma-01"のようなランダムエージェント名でタスク実行をシミュレート。**実際のタスク処理ロジックはここに実装する必要があります。**
- `node_reporter`: ミッションを完了としてマーク

グラフは`ghost_brain`にコンパイルされ、バックグラウンドタスクとして呼び出されます。

### API構造（FastAPI）

**main.py** - 以下のエンドポイントを持つFastAPIアプリケーション：
- `GET /`: ヘルスチェック
- `POST /mission/start`: ミッションを作成し、バックグラウンドエージェント実行をトリガー
- `GET /mission/current`: タスク付きの最新ミッションを取得
- `GET /missions`: ミッション履歴を取得
- `PATCH /mission/tasks/{task_id}`: タスクステータスを更新（ドラッグ＆ドロップ用）
- `DELETE /mission/{mission_id}`: ミッションを削除
- `POST /mission/reset`: メモリをリセット（レガシー、TODO.mdに従い削除を検討）

CORSは`http://localhost:3000`に設定されています。ライフサイクルハンドラーが起動時にデータベーステーブルを作成します。

**database.py** - 非同期データベースセットアップ：
- `asyncpg`ドライバーを使用したSQLAlchemy 2.0非同期エンジン
- `DATABASE_URL`環境変数からのPostgreSQL接続
- 依存性注入: FastAPIルート用の`get_db()`

**models.py** - データベースモデル（SQLAlchemy ORM）：
- `MissionModel`: ミッションメタデータ、ステータス、ログ（JSON列）を保存
- `TaskModel`: ステータス、担当者、エネルギー追跡を持つ個別タスク
- リレーションシップ: 1つのミッション → 多数のタスク（カスケード削除）

**schemas.py** - Pydanticバリデーション：
- `MissionRequest`、`MissionResponse`、`MissionSchema`: ミッションデータ
- `TaskSchema`、`TaskUpdate`: タスクデータ
- `PlanSchema`: 構造化されたLLM出力フォーマット（Plannerノードで使用）

**services.py** - ビジネスロジック層：
- `create_mission()`: データベースにミッションを挿入
- `run_agent_for_mission()`: LangGraphワークフローを実行して結果を保存
- `get_latest_mission()`: タスク付きの最新ミッションを取得
- `get_all_missions()`: イーガーローディング付きの履歴
- `update_task_status()`: タスクステータスを変更
- `delete_mission()`: ミッションとカスケードされたタスクを削除

### フロントエンド構造（Next.js）

**app/page.tsx** - メインインターフェース：
- 削除機能付きミッション履歴サイドバー
- リアルタイムログコンソール（黒背景に緑テキスト、サイバーパンクテーマ）
- 「司令官」テーマのコマンド入力
- ミッション選択と表示
- **ポーリングメカニズム**: 2秒ごとに`/missions`を取得して状態を同期
- **スマート更新**: ログ/タスク/ステータスが実際に変更された場合のみ再レンダリング（不必要なレンダリングを防ぐためのJSON比較）

**components/LivingKanban.tsx** - インタラクティブなカンバンボード：
- 3つの列: Planning、Working、Done
- `@dnd-kit/core`と`@dnd-kit/sortable`を使用したドラッグ＆ドロップ
- 機能:
  - 担当者とエネルギー表示付きのドラッグ可能なタスクカード
  - "working"タスクのプログレスバーアニメーション（Framer Motion）
  - ステータスベースの列スタイリング
  - **自動バックエンド同期**: ドラッグ＆ドロップ時に`/mission/tasks/{id}`へPATCHを送信
- 衝突検出: `closestCorners`戦略

**app/layout.tsx** - Interフォント、メタデータ、Tailwind CSSを含むルートレイアウト

### CLI（Go + Bubble Tea）

`apps/cli/`に配置：
- シアン/マゼンタカラーのサイバーパンクスタイルTUI
- 2つのモード: 表示と入力（`i`を押して入力モードに入る）
- API統合: `/mission/start`へのPOST、ヘルスチェックのため`/`をポーリング
- コマンド: `i`（入力）、`q`（終了）、`esc`（キャンセル）
- 環境変数: `API_URL`（デフォルト: `http://api:8000/`）

### インフラストラクチャ

**docker-compose.yml**は4つのサービスをオーケストレート：
- **api**: Python FastAPIバックエンド（ポート8000）
- **web**: Next.jsフロントエンド（ポート3000）
- **db**: PostgreSQL 15（ポート5432） - "共有ゴーストメモリ"
- **redis**: Redis（ポート6379） - タスクキューと状態キャッシュ
- **cli**: Go TUI（プロファイル"tools"、デフォルトでは起動しない）

## 主要な依存関係

**API（Python）**:
- Web: `fastapi`、`uvicorn`
- データベース: `sqlalchemy>=2.0.0`、`asyncpg`、`greenlet`
- AI/LLM: `openai>=1.0.0`、`langchain`、`langchain-core`、`langchain-openai`、`langgraph`
- キャッシュ: `redis>=4.5.0`
- テスト: `pytest`、`pytest-asyncio`、`pytest-mock`、`httpx`、`aiosqlite`
- コード品質: `black`、`isort`、`flake8`

**Web（TypeScript/React）**:
- フレームワーク: `next@14.1.0`、`react@18`、`react-dom@18`
- ドラッグ＆ドロップ: `@dnd-kit/core`、`@dnd-kit/sortable`、`@dnd-kit/utilities`
- UI/アニメーション: `framer-motion@11.0.0`、`lucide-react`、`tailwindcss`
- テスト: `jest`、`@testing-library/react`、`@testing-library/jest-dom`

**CLI（Go）**:
- TUI: `github.com/charmbracelet/bubbletea`、`github.com/charmbracelet/lipgloss`
- 入力: `github.com/charmbracelet/bubbles/textinput`

## 設定

**API環境変数**（`apps/api/.env`）：
- `OPENAI_API_KEY`: LLM統合に必要
- `GHOST_MODEL_NAME`: モデル選択（デフォルト: `gpt-3.5-turbo`）
- `DATABASE_URL`: PostgreSQL接続文字列（docker-composeで設定）

`.env.example`を`.env`にコピーして、OpenAI APIキーを追加してください。

**Web環境変数**:
- `NEXT_PUBLIC_API_URL`: APIエンドポイント（デフォルト: `http://localhost:8000`）

## 開発ノート

### 現在の状態

- **フロントエンドはバックエンドに接続済み**: 2秒ごとにポーリング、ドラッグ＆ドロップはAPIと同期
- **LangGraph Planner**: エラー時のフォールバックシミュレーション付きで実際のOpenAI LLM呼び出しを使用
- **Workerノード**: まだ`time.sleep()`でシミュレート - **実際のタスク実行はまだ実装されていません**
- **データベース**: 起動時に`create_all()`を使用（Alembicのようなマイグレーションシステムなし）
- **ポーリングベースのUI**: WebSocket/SSEへのアップグレード準備完了（TODO.md参照）

### アーキテクチャパターン

- **非同期ファースト**: 全体を通してasyncpgドライバーを使用したSQLAlchemy 2.0非同期
- **バックグラウンド処理**: ミッションはFastAPIの`BackgroundTasks`で実行
- **ステートマシン**: LangGraphが線形ワークフローを提供（planner → worker → reporter）
- **楽観的UI更新**: フロントエンドはドラッグ＆ドロップを許可し、その後バックエンドに同期

### 既知の制限事項（TODO.mdより）

- APIエンドポイントに認証/認可なし
- `docker-compose.yml`にシークレットがハードコード（`.env`を使用すべき）
- TypeScript strictモードが無効（`tsconfig.json`で`"strict": false`）
- テストタイムアウト問題: APIテストは成功するが`make test`がタイムアウト（現在はテストをスキップ）
- マイグレーションシステムなし（`create_all()`を使用）
- WebSocketの代わりにポーリング（リアルタイム更新には非効率）

### コードスタイル

- **日本語コメント**: 全体に存在、特にGhost-Squadコンセプトを説明するAPIロジック
- **Python**: Blackフォーマッター（行長88）、Isortでインポート管理
- **TypeScript**: Next.jsルール付きESLint

### よくあるタスクのための重要なファイル

**新しいAPIエンドポイントの追加**: `apps/api/main.py`、`apps/api/services.py`、`apps/api/schemas.py`

**エージェントロジックの変更**: `apps/api/agents/graph.py`、`apps/api/agents/state.py`

**データベーススキーマの変更**: `apps/api/models.py`（その後`make db-reset`を実行）

**フロントエンドUI変更**: `apps/web/app/page.tsx`、`apps/web/components/LivingKanban.tsx`

**テスト**: `apps/api/tests/test_endpoints.py`、`apps/web/__tests__/Home.test.tsx`

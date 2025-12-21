# GEMINI.md

このファイルは、このリポジトリのコードを扱う際のGeminiへのガイダンスを提供します。

## プロジェクト概要

Ghost-Squadは、攻殻機動隊にインスパイアされたマルチエージェントAIシステムで、「Living Kanban」のコンセプトを特徴としています。このシステムは、3つの主要なアプリケーションで構成されています。

- **API (バックエンド)**: LangGraphベースのエージェントオーケストレーションを備えたFastAPIサーバー
- **Web (フロントエンド)**: TypeScriptとTailwind CSSを備えたNext.js 14アプリケーション
- **CLI**: コマンドラインインターフェース（プレースホルダーディレクトリ）

このアーキテクチャは、LangGraphを使用して、調整されたエージェントノード（プランナー → ワーカー → レポーター）を通じてミッションを処理する「ゴーストブレイン」を作成します。

## 開発コマンド

### Docker Compose (推奨)
```bash
# すべてのサービス（API、Web、PostgreSQL、Redis）を開始
docker-compose up

# 特定のサービスを開始
docker-compose up api
docker-compose up web

# すべてのサービスを停止
docker-compose down
```

### API (FastAPI バックエンド)
```bash
cd apps/api

# 開発サーバーを実行
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# APIは http://localhost:8000 で利用可能になります
# APIドキュメントは http://localhost:8000/docs で利用可能
```

**依存関係**: PostgreSQL (ポート5432) とRedis (ポート6379) が実行されている必要があります。

### Web (Next.js フロントエンド)
```bash
cd apps/web

# 依存関係をインストール
npm install

# 開発サーバーを実行
npm run dev

# プロダクション用にビルド
npm run build

# プロダクションサーバーを開始
npm start
```

Webアプリケーションは http://localhost:3000 で利用可能になります。

## アーキテクチャ

### エージェントシステム (LangGraph)

コアインテリジェンスは `apps/api/agents/` にあります。

- **state.py**: `AgentState` を定義します。これは、すべてのノード間で渡される共有メモリ構造です。ミッションメタデータ、タスク入力、計画ステップ、実行ログ、ステータス、コスト追跡が含まれます。

- **graph.py**: 3つのシーケンシャルノードを持つLangGraphワークフローを実装します。
  - `node_planner`: ミッション指示を受け取り、実行計画を作成します
  - `node_worker`: 計画を実行します（現在は「tachikoma-01」のようなランダムなエージェント名でシミュレートされています）
  - `node_reporter`: ミッション完了を最終決定し、報告します

  このグラフは `ghost_brain` にコンパイルされ、APIによって呼び出されます。

### API構造

**main.py** はFastAPIのエントリーポイントです。
- `POST /mission/start`: ミッション指示を受け入れ、`AgentState`を初期化し、`ghost_brain`を呼び出し、ログとステータスを含む最終状態を返します。
- `GET /`: ヘルスチェックエンドポイント。

APIは、リクエスト/レスポンスの検証にPydanticモデル（`MissionRequest`、`MissionResponse`）を使用します。

### フロントエンド構造

`apps/web/app/` の最小限のNext.js 14 App Routerセットアップ：
- **page.tsx**: 「GHOST-SQUAD」ブランディングとシステムステータスインジケーターを備えたランディングページ
- **layout.tsx**: 基本的なHTML構造を持つルートレイアウト

スタイリングにはTailwind CSSを使用しています。API連携はまだ実装されていません。

### インフラストラクチャ

**docker-compose.yml** は4つのサービスをオーケストレーションします。
- **api**: Python FastAPIバックエンド（ポート8000）
- **web**: Next.jsフロントエンド（ポート3000）
- **db**: PostgreSQL 15（ポート5432） - 「共有ゴーストメモリ」
- **redis**: Redis（ポート6379） - タスクキューとステートキャッシュ

環境変数はサービスごとに構成されています。データベース資格情報：`ghost/squad_password`、データベース名：`ghost_memory`。

## 主要な依存関係

**API (Python)**:
- fastapi, uvicorn: WebフレームワークとASGIサーバー
- sqlalchemy, asyncpg: データベースORMとPostgreSQLドライバー
- redis: キャッシュとキュー管理
- langchain, langgraph: エージェントオーケストレーションフレームワーク
- openai: LLM統合

**Web (TypeScript/React)**:
- next 14.1.0: ReactフレームワークとApp Router
- framer-motion: アニメーションライブラリ
- lucide-react: アイコンライブラリ
- tailwindcss: ユーティリティファーストCSS

## 開発ノート

- LangGraphの実装は現在、デモンストレーション目的で`time.sleep()`を使用してLLM呼び出しをシミュレートしています。実際のLLM統合（OpenAI）は依存関係に含まれていますが、まだ実装されていません。

- エージェントの状態はグラフノードを介して流れ、各ノードはLangGraphによって自動的にマージされる部分的な状態更新を返します。

- コードベース全体、特にGhost-Squadのコンセプトとミッションフローを説明するAPIロジックには、日本語のコメントが含まれています。

- フロントエンドはまだバックエンドAPIに接続されていません。`NEXT_PUBLIC_API_URL`環境変数は構成されていますが、使用されていません。

- WebアプリケーションではTypeScript厳格モードが無効になっています（tsconfig.jsonで`"strict": false`）。
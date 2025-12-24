# プロジェクト構造・組織化

## ルートディレクトリ構成

```
ghost-squad/
├── backend/                 # Python FastAPIバックエンド
├── frontend/                # React TypeScriptフロントエンド
├── docs/                    # プロジェクトドキュメント
├── bin/                     # ユーティリティスクリプト
├── .kiro/                   # Kiro設定・仕様
├── docker-compose.yml       # コンテナオーケストレーション
├── Makefile                 # 開発自動化
├── .env.example             # 環境変数テンプレート
└── README.md                # プロジェクト概要
```

## バックエンド構造 (`backend/`)

**コアアプリケーションファイル**
- `main.py` - FastAPIアプリケーションエントリーポイント（CORS・ライフサイクル管理）
- `database.py` - データベース接続・セッション管理
- `manage_db.py` - データベース管理ユーティリティ
- `seed_data.py` - テストデータシーディングスクリプト
- `requirements.txt` - Python依存関係

**モデル組織化** (`models/`)
- `database/` - SQLAlchemy ORMモデル（base.py、inquiry.py、story.py、template.py）
- `schemas/` - APIシリアライゼーション用Pydanticモデル
- `enums/` - 列挙型（status、priority、category、pattern）
- `api/` - APIエンドポイント用リクエスト・レスポンスモデル
- `export/` - エクスポート形式モデル（kanban.py）
- `protocols/` - サービス用プロトコル定義

**データベース管理** (`alembic/`)
- マイグレーションファイル・Alembic設定
- `versions/` - データベースマイグレーションスクリプト
- `env.py` - Alembic環境設定

**テスト** (`tests/`)
- `conftest.py` - pytest設定・フィクスチャ
- `test_*.py`命名規則に従うテストファイル

## フロントエンド構造 (`frontend/`)

**コアアプリケーション**
- `src/App.tsx` - メインアプリケーションコンポーネント
- `src/index.tsx` - アプリケーションエントリーポイント
- `public/` - 静的アセット・HTMLテンプレート
- `package.json` - Node.js依存関係・スクリプト

**型定義** (`src/types/`)
- `api/` - API関連型定義
- `enums/` - バックエンドと対応する列挙型
- `export/` - エクスポート形式型
- `models/` - データモデル型
- `index.ts` - 型エクスポート

## 設定ファイル

**環境設定**
- `.env.example` - 必要な環境変数のテンプレート
- `.env` - ローカル環境変数（バージョン管理対象外）

**Docker設定**
- `docker-compose.yml` - マルチサービスコンテナセットアップ
- `backend/Dockerfile` - バックエンドコンテナ定義
- `frontend/Dockerfile` - フロントエンドコンテナ定義

**開発ツール**
- `Makefile` - 統一開発コマンド
- `.gitignore` - バージョン管理除外設定
- バックエンド: `.flake8`、`alembic.ini`（リント・マイグレーション用）
- フロントエンド: `tsconfig.json`、ESLint設定

## 命名規則

**Python（バックエンド）**
- ファイル: `snake_case.py`
- クラス: `PascalCase`（例: `InquiryModel`、`StorySchema`）
- 関数・変数: `snake_case`
- 定数: `UPPER_SNAKE_CASE`
- データベーステーブル: `snake_case`（例: `inquiries`、`story_templates`）

**TypeScript（フロントエンド）**
- ファイル: コンポーネントは`PascalCase.tsx`、ユーティリティは`camelCase.ts`
- コンポーネント: `PascalCase`（例: `StoryBoard`、`InquiryForm`）
- 関数・変数: `camelCase`
- 型・インターフェース: `PascalCase`（説明的な接尾辞付き）

**データベーススキーマ**
- テーブル: `snake_case`複数形名詞
- カラム: `snake_case`
- 外部キー: `{table}_id`形式
- インデックス: `ix_{table}_{column}`形式

## インポート組織化

**Pythonインポート順序**
1. 標準ライブラリインポート
2. サードパーティインポート（FastAPI、SQLAlchemyなど）
3. ローカルアプリケーションインポート
4. 相対インポート

**TypeScriptインポート順序**
1. React・React関連インポート
2. サードパーティライブラリインポート
3. ローカルコンポーネントインポート
4. 型のみインポート（`type`キーワード付き）

## ファイル組織化原則

- **関心の分離**: モデル、スキーマ、ビジネスロジックを明確に分離
- **機能ベースグループ化**: 関連機能をまとめる（例: inquiryモデル、storyモデル）
- **一貫した命名**: ファイル・ディレクトリは一貫した命名パターンに従う
- **明確な依存関係**: インポート構造がアーキテクチャ層を反映
- **テスト近接性**: テストはソース構造を反映して組織化
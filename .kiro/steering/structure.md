---
inclusion: always
---

# プロジェクト構造・組織化ガイドライン

Ghost Squadプロジェクトの構造と組織化に関するガイドラインです。新しいファイルやディレクトリを作成する際は、この構造に従ってください。

## ルートディレクトリ構成

```
ghost-squad/
├── api/                 # Python FastAPIバックエンド
├── web/                # React TypeScriptフロントエンド
├── docs/                    # プロジェクトドキュメント
├── bin/                     # ユーティリティスクリプト
├── .kiro/                   # Kiro設定・仕様
├── docker-compose.yml       # コンテナオーケストレーション
├── Makefile                 # 開発自動化
├── .env.example             # 環境変数テンプレート
└── README.md                # プロジェクト概要
```

## バックエンド構造 (`api/`)

**コアアプリケーションファイル**
- `main.py` - FastAPIアプリケーションエントリーポイント（CORS・ライフサイクル管理）
- `database.py` - データベース接続・セッション管理
- `manage_db.py` - データベース管理ユーティリティ
- `seed_data.py` - テストデータシーディングスクリプト
- `requirements.txt` - Python依存関係

**モデル組織化** (`models/`)
```
models/
├── database/          # SQLAlchemy ORMモデル
│   ├── base.py       # ベースモデルクラス（実装済み）
│   ├── inquiry.py    # 問い合わせモデル（実装済み）
│   ├── story.py      # ストーリーモデル（実装済み）
│   ├── import_error_log.py  # インポートエラーログモデル（実装済み）
│   └── story_template.py  # テンプレートモデル（未実装）
├── schemas/          # Pydanticスキーマ（APIシリアライゼーション）
│   ├── inquiry.py    # 問い合わせスキーマ（実装済み）
│   └── story.py      # ストーリースキーマ（実装済み）
├── enums/           # 列挙型定義
│   ├── inquiry_status.py  # InquiryStatus列挙型（実装済み）
│   ├── story_status.py    # StoryStatus列挙型（実装済み）
│   └── priority.py        # Priority列挙型（実装済み）
├── api/             # APIリクエスト・レスポンスモデル
└── protocols/       # サービス用プロトコル定義
```

**サービス層** (`services/`)
- ビジネスロジックを含むサービスクラス
- **Inquiry関連（実装済み）**:
  - バリデーション（`inquiry_validator.py` - 問い合わせデータ検証、97%カバレッジ）
  - データアクセス（`inquiry_repository.py` - CRUD操作、フィルタリング、ソート、ページネーション、90%カバレッジ）
  - クエリサービス（`inquiry_query_service.py` - 問い合わせ検索・一覧取得、100%カバレッジ）
  - ワークフローサービス（`inquiry_workflow_service.py` - 承認・却下処理、ステータス遷移管理、89%カバレッジ）
- **Story関連（サービス層完了）**:
  - データアクセス（`story_repository.py` - CRUD操作、フィルタリング、ソート、ページネーション、86%カバレッジ）
  - クエリサービス（`story_query_service.py` - ストーリー検索・一覧取得、100%カバレッジ）
  - バリデーション（`story_validator.py` - ストーリーデータ検証、95%カバレッジ）
  - ワークフローサービス（`story_workflow_service.py` - 承認・却下処理、ステータス遷移管理、一括承認、100%カバレッジ）
  - AI統合（`story_generation_service.py` - OpenAI API統合、ストーリー自動生成、リトライ戦略、88%カバレッジ）
- **Importer関連（バックエンド実装完了、`services/importer/`）**:
  - **共通基盤**:
    - 共通Result型（`result.py` - Rust風Result型、BaseError基底クラス）
    - エラーログ永続化（`import_error_log_repository.py` - エラー記録・統計・自動解決）
  - **データソースプラグイン層**:
    - プラグイン基盤（`plugin_base.py` - DataSourcePlugin抽象クラス、RawImportData、ValidationResult）
    - プラグイン管理（`plugin_registry.py` - PluginRegistryService、登録・解除・有効/無効切替）
    - メールプラグイン（`email_plugin.py` - IMAP接続、メール取得・解析、リトライ戦略、EmailPluginConfig）
  - **AIプロバイダー層**:
    - AIプロバイダー基盤（`ai_provider_base.py` - AIProvider抽象クラス、AIProviderType列挙型、AIAnalysisRequest/Response）
    - AIプロバイダー管理（`ai_provider_registry.py` - AIProviderRegistryService、デフォルト設定、初期化管理）
    - OpenAIプロバイダー（`openai_provider.py` - GPT-4統合、リトライ戦略）
    - Anthropicプロバイダー（`anthropic_provider.py` - Claude統合、リトライ戦略）
  - **解析サービス層**:
    - 解析サービス（`analysis_service.py` - ImporterAnalysisService、信頼度判定、needs_reviewフラグ）
  - **統合サービス層**:
    - インポート統括（`importer_service.py` - ImporterService、インポート実行、重複チェック、リトライ機能）
    - 設定ローダー（`importer_config_loader.py` - ImporterConfigLoader、YAML設定、環境変数展開）

**API層** (`routers/`)
- FastAPIルーター定義
- エンドポイント実装
- 依存性注入
- **Inquiry API（実装済み）**: `inquiry.py` - CRUD + ワークフロー全エンドポイント
- **Story API（実装済み）**: `story.py` - CRUD + ワークフロー + AI変換 + 一括承認エンドポイント
- **Importer API（実装済み）**: `importer.py` - プラグイン管理 + AIプロバイダー管理 + インポート実行 + エラー統計

**テスト** (`tests/`)
- `conftest.py` - pytest設定・フィクスチャ
- `test_*.py` - テストファイル（テスト対象と同じ構造）
- `property_tests/` - プロパティベーステスト専用ディレクトリ

## フロントエンド構造 (`web/`)

**実装済みディレクトリ構造**
```
src/
├── types/              # TypeScript型定義（実装済み）
│   ├── inquiry.ts     # Inquiry関連型（InquiryResponse、CreateInquiryRequest等）
│   ├── story.ts       # Story関連型（StoryResponse、CreateStoryRequest等）
│   └── index.ts       # 型エクスポート
├── services/          # API呼び出しサービス（実装済み）
│   ├── inquiryApi.ts  # 問い合わせAPIクライアント（Axios、エラーハンドリング）
│   ├── storyApi.ts    # ストーリーAPIクライアント（CRUD、ワークフロー、AI生成）
│   └── index.ts       # サービスエクスポート
├── components/        # 再利用可能コンポーネント（実装済み）
│   ├── InquiryForm.tsx       # 問い合わせ入力フォーム（React Hook Form + Zod）
│   ├── InquiryForm.test.tsx  # フォームコンポーネントテスト
│   ├── InquiryList.tsx       # 問い合わせ一覧コンポーネント（TanStack Query、ページネーション、フィルタ）
│   ├── InquiryList.test.tsx  # 一覧コンポーネントテスト
│   ├── InquiryDetail.tsx     # 問い合わせ詳細・編集コンポーネント（TanStack Query、承認/却下）
│   ├── InquiryDetail.test.tsx # 詳細コンポーネントテスト
│   ├── StoryList.tsx         # ストーリー一覧コンポーネント（TanStack Query、ページネーション、フィルタ、ソート）
│   ├── StoryList.test.tsx    # ストーリー一覧コンポーネントテスト
│   ├── StoryForm.tsx         # ストーリー作成フォーム（React Hook Form + Zod、モーダル）
│   ├── StoryForm.test.tsx    # ストーリー作成フォームテスト
│   ├── StoryDetail.tsx       # ストーリー詳細・編集コンポーネント（TanStack Query、承認/却下/削除）
│   ├── StoryDetail.test.tsx  # ストーリー詳細コンポーネントテスト
│   ├── StoryIntegration.test.tsx  # E2E統合テスト（ストーリー生成・作成・承認/却下フロー）
│   └── index.ts              # コンポーネントエクスポート
├── __mocks__/         # テストモック（実装済み）
│   └── axios.ts       # Axiosマニュアルモック
├── App.tsx            # メインアプリケーションコンポーネント（タブナビゲーション）
├── index.tsx          # エントリーポイント
├── setupTests.ts      # テスト設定
└── App.test.tsx       # アプリケーションテスト
```

**将来実装予定のディレクトリ**
```
src/
├── components/       # 追加の再利用可能コンポーネント
│   ├── ui/          # 基本UIコンポーネント（未実装）
│   └── layout/      # レイアウトコンポーネント（未実装）
├── pages/           # ページコンポーネント（未実装）
├── hooks/           # カスタムReactフック（未実装）
├── utils/           # ユーティリティ関数（未実装）
└── constants/       # 定数定義（未実装）
```

**型定義組織化** (`src/types/`)
- **実装済み**:
  - `inquiry.ts` - Inquiry関連型定義（バックエンドPydanticスキーマと整合）
    - InquiryStatus（列挙型）
    - InquiryResponse, CreateInquiryRequest, UpdateInquiryRequest（API型）
    - PaginatedResponse, ErrorResponse（共通型）
  - `story.ts` - Story関連型定義（バックエンドPydanticスキーマと整合）
    - StoryStatus（WAITING_REVIEW/APPROVED/REJECTED）
    - Priority（LOW/MEDIUM/HIGH/URGENT）
    - StoryResponse, CreateStoryRequest, UpdateStoryRequest（API型）
    - ApproveStoryRequest, RejectStoryRequest（ワークフロー型）
  - `importer.ts` - Importer関連型定義（バックエンドPydanticスキーマと整合）
    - PluginStatus, PluginListResponse（プラグイン管理型）
    - AIProviderStatus, AIProviderListResponse（AIプロバイダー管理型）
    - ExecuteImportRequest, RetryImportRequest, ImportResult（インポート実行型）
    - ErrorStats, ErrorStatsListResponse（エラー統計型）
    - ImporterValidationError, ImporterErrorResponse（共通エラー型）
- **将来実装**:
  - `api/` - 追加のAPI関連型定義
  - `components/` - コンポーネントプロパティ型

**サービス層組織化** (`src/services/`)
- **実装済み**:
  - `inquiryApi.ts` - 問い合わせAPIクライアント（86.11%カバレッジ）
    - Axiosインスタンス作成（30秒タイムアウト、CORS設定）
    - エラーレスポンスインターセプター（ErrorResponse標準化）
    - CRUD操作（createInquiry、listInquiries、getInquiry、updateInquiry）
    - ワークフロー操作（approveInquiry、rejectInquiry）
    - ヘルスチェック（healthCheck）
  - `storyApi.ts` - ストーリーAPIクライアント（82.45%カバレッジ）
    - CRUD操作（createStory、listStories、getStory、updateStory、deleteStory）
    - ワークフロー操作（approveStory、rejectStory、batchApproveStories）
    - AI生成（generateStory）
  - `importerApi.ts` - インポーターAPIクライアント（実装済み）
    - Axiosインスタンス作成（30秒タイムアウト、CORS設定）
    - エラーレスポンスインターセプター（ImporterErrorResponse標準化）
    - プラグイン管理（listPlugins、enablePlugin、disablePlugin）
    - AIプロバイダー管理（listAIProviders、setDefaultAIProvider）
    - インポート実行（executeImport、retryImport）
    - エラー統計（getErrorStats）
- **将来実装**:
  - `authService.ts` - 認証サービス

**コンポーネント組織化** (`src/components/`)
- **実装済み**:
  - `InquiryForm.tsx` - 問い合わせ入力フォーム
    - React Hook Form + Zod バリデーション
    - リアルタイム入力検証
    - エラーハンドリング・成功通知（react-hot-toast）
    - 100% statements カバレッジ、94.28% branches カバレッジ
  - `InquiryList.tsx` - 問い合わせ一覧表示
    - TanStack React Query（サーバー状態管理）
    - ページネーション（前へ/次へ、ページ番号表示）
    - ステータスフィルタリング（全ステータス対応）
    - 行クリック・キーボードナビゲーション対応（アクセシビリティ）
    - 内容の省略表示（100文字制限）
    - ローディング・エラー状態表示
  - `InquiryDetail.tsx` - 問い合わせ詳細・編集
    - TanStack React Query（詳細取得・mutations）
    - 読み取り/編集モード切り替え
    - インライン編集（textarea）
    - 承認・却下ワークフロー（ステータス='received'のみ）
    - ストーリー生成トリガー（ステータス='task_working'時のみ表示）
    - モーダルダイアログ（却下理由入力）
    - 94.64% statements カバレッジ、86.36% branches カバレッジ
  - `StoryList.tsx` - ストーリー一覧表示
    - TanStack React Query（サーバー状態管理）
    - ページネーション（前へ/次へ、ページ番号表示）
    - ステータス・優先度フィルタリング
    - ソート機能（作成日時、更新日時、優先度、推定工数、担当者、期限）
    - 行クリック・キーボードナビゲーション対応（アクセシビリティ）
    - 95.83% statements カバレッジ
  - `StoryForm.tsx` - ストーリー作成フォーム（新規作成モード）
    - モーダルダイアログで表示
    - React Hook Form + Zod バリデーション
    - 問い合わせID選択ドロップダウン（プレビュー表示付き）
    - タイトル、説明、優先度、推定工数、担当者、期限入力
    - リアルタイムバリデーション（タイトル500文字以内、必須フィールド）
    - エラーハンドリング・成功通知（react-hot-toast）
  - `StoryDetail.tsx` - ストーリー詳細・編集コンポーネント
    - TanStack React Query（詳細取得・mutations）
    - 読み取り/編集モード切り替え
    - インライン編集（タイトル、説明、優先度、推定工数、担当者、期限）
    - 承認・却下ワークフロー（ステータス='waiting_review'のみ）
    - 確認ダイアログ（承認・却下・削除）
    - 却下理由入力モーダル（バリデーション付き）
    - 承認情報・却下情報の表示
    - 93.85% statements カバレッジ
  - `StoryIntegration.test.tsx` - E2E統合テスト
    - ストーリー生成フロー（問い合わせ詳細からのストーリー生成）
    - 手動作成フロー（StoryFormからの作成）
    - 承認・却下フロー（StoryDetailでのワークフロー）
    - ナビゲーション・ステータス別UI動作検証
    - 10テスト
  - `importer/` - インポーター管理コンポーネント（実装済み）
    - `ImporterPage.tsx` - インポーター管理統括ページ
    - `PluginListComponent.tsx` - プラグイン一覧・有効/無効切替
    - `AIProviderListComponent.tsx` - AIプロバイダー一覧・デフォルト設定
    - `ImportExecutorComponent.tsx` - インポート実行コンポーネント
    - `ErrorStatsComponent.tsx` - エラー統計表示コンポーネント
    - `ImporterIntegration.test.tsx` - E2E統合テスト
    - 各コンポーネントにテストファイル（*.test.tsx）あり
- **将来実装**:
  - `ui/` - 基本UIコンポーネント（Button、Input、Modal等）
  - `layout/` - レイアウトコンポーネント（Header、Footer、Sidebar等）

## 命名規則

**Python（バックエンド）**
- ファイル: `snake_case.py`
- クラス: `PascalCase` (例: `InquiryModel`, `StoryService`)
- 関数・変数: `snake_case`
- 定数: `UPPER_SNAKE_CASE`
- プライベートメソッド: `_snake_case`
- データベーステーブル: `snake_case`複数形 (例: `inquiries`, `story_templates`)

**TypeScript（フロントエンド）**
- ファイル: コンポーネントは`PascalCase.tsx`、その他は`camelCase.ts`
- コンポーネント: `PascalCase` (例: `StoryBoard`, `InquiryForm`)
- 関数・変数: `camelCase`
- 定数: `UPPER_SNAKE_CASE`
- 型・インターフェース: `PascalCase` + 説明的接尾辞 (例: `StoryData`, `InquiryFormProps`)

**データベーススキーマ**
- テーブル: `snake_case`複数形名詞
- カラム: `snake_case`
- 外部キー: `{table_name}_id`形式
- インデックス: `ix_{table}_{column}`形式
- 制約: `{constraint_type}_{table}_{column}`形式

## ファイル作成ガイドライン

**新しいモデル追加時**
1. `models/database/` にORMモデル作成
2. `models/schemas/` にPydanticスキーマ作成
3. `models/api/` にAPIモデル作成
4. 必要に応じて列挙型を `models/enums/` に追加
5. マイグレーションファイル生成: `make db-revision`

**新しいAPI追加時**
1. `api/` ディレクトリにルーター作成
2. 対応するサービスクラスを `services/` に作成
3. テストファイルを `tests/` に作成
4. API仕様をOpenAPIスキーマで文書化

**新しいコンポーネント追加時**
1. 適切なディレクトリに配置 (`components/`, `pages/`)
2. 型定義を `types/components/` に作成
3. テストファイルを同じディレクトリに作成
4. Storybookストーリー作成（UI コンポーネントの場合）

## インポート組織化

**Pythonインポート順序**
```python
# 1. 標準ライブラリ
import os
from datetime import datetime

# 2. サードパーティライブラリ
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# 3. ローカルアプリケーション（絶対インポート）
from models.database.inquiry import InquiryModel
from services.story_service import StoryService

# 4. 相対インポート
from .base import BaseModel
```

**TypeScriptインポート順序**
```typescript
// 1. React・React関連
import React, { useState, useEffect } from 'react';

// 2. サードパーティライブラリ
import axios from 'axios';
import { useQuery } from '@tanstack/react-query';

// 3. ローカルコンポーネント・サービス
import { StoryService } from '../services/storyService';
import { Button } from '../components/ui/Button';

// 4. 型のみインポート
import type { StoryData, InquiryFormProps } from '../types';
```

## アーキテクチャ層の分離

**バックエンド層構造**
```
API層 (FastAPI routes) 
    ↓
サービス層 (Business Logic)
    ↓
リポジトリ層 (Data Access)
    ↓
モデル層 (SQLAlchemy ORM)
```

**フロントエンド層構造**
```
コンポーネント層 (React Components)
    ↓
フック層 (Custom Hooks)
    ↓
サービス層 (API Calls)
    ↓
ユーティリティ層 (Pure Functions)
```

## コード組織化のベストプラクティス

**関心の分離**
- ビジネスロジックをサービス層に集約
- データアクセスをリポジトリパターンで抽象化
- UI ロジックとビジネスロジックを分離

**依存関係管理**
- 上位層から下位層への依存のみ許可
- 循環依存を避ける
- 依存性注入を活用

**テスト組織化**
- テストファイルはソース構造を反映
- ユニットテスト、統合テスト、E2Eテストを明確に分離
- プロパティベーステストは専用ディレクトリに配置
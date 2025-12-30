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
│   ├── base.py       # ベースモデルクラス
│   ├── inquiry.py    # 問い合わせモデル（実装済み）
│   ├── story.py      # ストーリーモデル
│   └── story_template.py  # テンプレートモデル
├── schemas/          # Pydanticスキーマ（APIシリアライゼーション）
│   └── inquiry.py    # 問い合わせスキーマ（実装済み）
├── enums/           # 列挙型定義
│   └── inquiry_status.py  # InquiryStatus列挙型（実装済み）
├── api/             # APIリクエスト・レスポンスモデル
├── export/          # エクスポート形式モデル
└── protocols/       # サービス用プロトコル定義
```

**サービス層** (`services/`)
- ビジネスロジックを含むサービスクラス
- バリデーション（`inquiry_validator.py` - 問い合わせデータ検証）
- データアクセス（`inquiry_repository.py` - CRUD操作、フィルタリング、ソート、ページネーション）
- クエリサービス（`inquiry_query_service.py` - 問い合わせ検索・一覧取得、100%カバレッジ）
- ワークフローサービス（`inquiry_workflow_service.py` - 承認・却下処理、ステータス遷移管理）
- 外部API統合（OpenAI、エクスポートサービス - 将来実装）

**API層** (`api/`) - 将来実装
- FastAPIルーター定義
- エンドポイント実装
- 依存性注入

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
│   └── index.ts       # 型エクスポート
├── services/          # API呼び出しサービス（実装済み）
│   ├── inquiryApi.ts  # 問い合わせAPIクライアント（Axios、エラーハンドリング）
│   └── index.ts       # サービスエクスポート
├── __mocks__/         # テストモック（実装済み）
│   └── axios.ts       # Axiosマニュアルモック
├── App.tsx            # メインアプリケーションコンポーネント
├── index.tsx          # エントリーポイント
├── setupTests.ts      # テスト設定
└── App.test.tsx       # アプリケーションテスト
```

**将来実装予定のディレクトリ**
```
src/
├── components/       # 再利用可能コンポーネント（未実装）
│   ├── ui/          # 基本UIコンポーネント
│   ├── forms/       # フォームコンポーネント
│   └── layout/      # レイアウトコンポーネント
├── pages/           # ページコンポーネント（未実装）
├── hooks/           # カスタムReactフック（未実装）
├── utils/           # ユーティリティ関数（未実装）
└── constants/       # 定数定義（未実装）
```

**型定義組織化** (`src/types/`)
- **実装済み**: `inquiry.ts` - Inquiry関連型定義（バックエンドPydanticスキーマと整合）
  - InquiryStatus, Priority, StoryCategory（列挙型）
  - InquiryResponse, CreateInquiryRequest, UpdateInquiryRequest（API型）
  - PaginatedResponse, ErrorResponse（共通型）
- **将来実装**:
  - `story.ts` - Story関連型定義
  - `api/` - 追加のAPI関連型定義
  - `components/` - コンポーネントプロパティ型

**サービス層組織化** (`src/services/`)
- **実装済み**: `inquiryApi.ts` - 問い合わせAPIクライアント
  - Axiosインスタンス作成（30秒タイムアウト、CORS設定）
  - エラーレスポンスインターセプター（ErrorResponse標準化）
  - CRUD操作（createInquiry、listInquiries、getInquiry、updateInquiry）
  - ワークフロー操作（approveInquiry、rejectInquiry）
  - ヘルスチェック（healthCheck）
- **将来実装**:
  - `storyApi.ts` - ストーリーAPIクライアント
  - `authService.ts` - 認証サービス
  - `exportService.ts` - エクスポートサービス

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
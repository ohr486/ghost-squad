---
inclusion: always
---

# プロジェクト構造・組織化ガイドライン

Ghost Squadプロジェクトの構造と組織化に関するガイドラインです。新しいファイルやディレクトリを作成する際は、この構造に従ってください。

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
```
models/
├── database/          # SQLAlchemy ORMモデル
│   ├── base.py       # ベースモデルクラス
│   ├── inquiry.py    # 問い合わせモデル
│   ├── story.py      # ストーリーモデル
│   └── story_template.py  # テンプレートモデル
├── schemas/          # Pydanticスキーマ（APIシリアライゼーション）
├── enums/           # 列挙型定義
├── api/             # APIリクエスト・レスポンスモデル
├── export/          # エクスポート形式モデル
└── protocols/       # サービス用プロトコル定義
```

**サービス層** (`services/`) - 新規作成時
- ビジネスロジックを含むサービスクラス
- 外部API統合（OpenAI、エクスポートサービス）
- データ変換・バリデーション

**API層** (`api/`) - 新規作成時
- FastAPIルーター定義
- エンドポイント実装
- 依存性注入

**テスト** (`tests/`)
- `conftest.py` - pytest設定・フィクスチャ
- `test_*.py` - テストファイル（テスト対象と同じ構造）
- `property_tests/` - プロパティベーステスト専用ディレクトリ

## フロントエンド構造 (`frontend/`)

**推奨ディレクトリ構造**
```
src/
├── components/       # 再利用可能コンポーネント
│   ├── ui/          # 基本UIコンポーネント
│   ├── forms/       # フォームコンポーネント
│   └── layout/      # レイアウトコンポーネント
├── pages/           # ページコンポーネント
├── hooks/           # カスタムReactフック
├── services/        # API呼び出し・ビジネスロジック
├── utils/           # ユーティリティ関数
├── types/           # TypeScript型定義
└── constants/       # 定数定義
```

**型定義組織化** (`src/types/`)
- `api/` - API関連型定義
- `enums/` - バックエンドと対応する列挙型
- `models/` - ドメインモデル型
- `components/` - コンポーネントプロパティ型

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
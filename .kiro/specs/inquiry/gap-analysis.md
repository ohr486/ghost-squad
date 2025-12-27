# 問い合わせ管理機能 ギャップ分析

## 分析サマリー

- **スコープ**: 問い合わせ管理機能は既にバックエンドの基本機能（作成・取得）が実装済みで、フロントエンドも入力フォームが完成している。要件で求められる追加機能は、問い合わせの編集、承認・却下のワークフロー、Web UIでの一覧表示・検索機能。
- **主な課題**:
  - 問い合わせ更新API（`PUT /api/inquiries/{id}`）が未実装
  - ステータス更新（承認・却下）のエンドポイントが未実装
  - フロントエンドの一覧表示・検索UIが未実装
- **推奨アプローチ**: 既存のAPIルーターとフロントエンドサービス層を拡張する方式（Option A）。新規ファイル作成は最小限に抑え、既存パターンに従った実装を推奨。

---

## 1. 現状調査

### 1.1 既存ドメイン資産

**バックエンド (Python/FastAPI)**

- **データモデル**: `backend/models/database/inquiry.py`
  - `InquiryModel`: 問い合わせのORMモデル（完全実装済み）
  - フィールド: `id`, `user_id`, `content`, `language`, `timestamp`, `status`, `inquiry_metadata`
  - BigInteger ID、UTC タイムスタンプ、JSON メタデータ対応済み

- **ステータス管理**: `backend/models/enums/inquiry_status.py`
  - `InquiryStatus` Enum: `RECEIVED`, `PROCESSING`, `NEEDS_CLARIFICATION`, `TASK_WORKING`, `COMPLETED`, `FAILED`
  - 要件の「received」、承認・却下後の「task_working」、「completed」をサポート

- **API層**: `backend/api/inquiries.py`
  - 実装済みエンドポイント:
    - `POST /api/inquiries/` - 問い合わせ作成
    - `GET /api/inquiries/` - 一覧取得（ページネーション: limit 1-1000, offset, user_id フィルタ対応）
    - `GET /api/inquiries/{id}` - 個別取得
  - パターン: 依存性注入（`Depends(get_db)`）、Pydantic バリデーション、日本語エラーメッセージ

- **スキーマ層**:
  - `backend/models/api/requests.py`: `InquiryCreateRequest`（実装済み）
  - `backend/models/api/responses.py`: `InquiryResponse`（実装済み、ORM自動マッピング対応）
  - `backend/models/schemas/inquiry.py`: Pydantic スキーマ `Inquiry`, `InquiryResult`

- **データベース**:
  - PostgreSQL 15 + SQLAlchemy 2.0.23 + Alembic マイグレーション
  - `inquiries` テーブル完全実装済み
  - 外部キー: `stories` テーブルへのリレーション（`inquiry_id`）

**フロントエンド (React/TypeScript)**

- **型定義**: `frontend/src/types/api/`
  - `InquiryCreateRequest`, `InquiryResponse` 完全実装済み
  - バックエンドスキーマと完全対応

- **サービス層**: `frontend/src/services/inquiryService.ts`
  - 実装済みメソッド:
    - `createInquiry()` - 問い合わせ作成
    - `getInquiries()` - 一覧取得（ページネーション対応）
    - `getInquiry()` - 個別取得
  - 未実装メソッド（コード存在、バックエンドエンドポイント未実装）:
    - `updateInquiry()` - 問い合わせ更新（コメントで未実装と明記）

- **UI コンポーネント**:
  - `frontend/src/components/forms/InquiryForm.tsx`: 問い合わせ入力フォーム（完全実装）
    - React Hook Form + Zod バリデーション
    - 送信状態管理、エラーハンドリング、アクセシビリティ対応済み
  - `frontend/src/pages/InquiriesPage.tsx`: 問い合わせ管理ページ
    - フォーム表示機能実装済み
    - 一覧表示は未実装（プレースホルダーのみ）

- **状態管理**:
  - TanStack React Query 5.8.4 設定済み（未使用）
  - API 通信: Axios 1.6.2 + apiClient（実装済み）

### 1.2 既存の規約とパターン

**命名規則**
- Python: `snake_case` (ファイル、関数、変数)、`PascalCase` (クラス)
- TypeScript: `PascalCase.tsx` (コンポーネント)、`camelCase.ts` (その他)
- データベーステーブル: `snake_case` 複数形（例: `inquiries`）

**アーキテクチャ層**
```
API層 (FastAPI routes)
  ↓
サービス層 (Business Logic) ※現在未実装、将来的に作成予定
  ↓
リポジトリ層 (Data Access) ※ORMで直接アクセス中
  ↓
モデル層 (SQLAlchemy ORM)
```

**API設計パターン**
- RESTful 原則
- エラーハンドリング: `try-except` ブロック + 日本語メッセージ
- バリデーション: Pydantic スキーマで自動検証
- レスポンス形式: Pydantic `model_validate()` で ORM オブジェクトを直接変換

**テスト戦略**
- pytest + pytest-asyncio + TestClient
- フィクスチャ: `test_session`, `client`, `clean_database`
- 14+テストケース（問い合わせAPI完全カバー済み）

### 1.3 統合ポイント

**データモデル統合**
- `InquiryModel` ↔ `StoryModel`: 1対多リレーション（`inquiry.stories`）
- 外部キー制約: `StoryModel.inquiry_id` → `InquiryModel.id`

**API統合**
- CORS設定: `localhost:3000`, Docker内部通信対応
- 依存性注入: `get_db()` でセッション管理
- エラーレスポンス: HTTPException + 日本語メッセージ

**フロントエンド統合**
- Axios プロキシ設定: `http://localhost:8000` へ自動転送
- エラーインターセプター: API エラーを自動的にトースト通知
- 型安全性: TypeScript strict mode + バックエンドと同期された型定義

---

## 2. 要件の実現可能性分析

### 要件1: 問い合わせの作成

**技術要件**:
- データベース保存 ✅
- タイムスタンプ、報告者名、内容、報告元システムの記録 ✅
- エラーメッセージ表示 ✅
- 必須項目検証 ✅
- 一意ID付与 ✅
- ステータス「received」設定 ✅

**ギャップ**: なし（完全実装済み）

**制約**: なし

---

### 要件2: 問い合わせの一覧表示、検索、編集

**技術要件**:
- ページネーション形式での一覧提供 ✅（バックエンド実装済み）
- ページサイズ 1-100件設定 ✅（バックエンドは1-1000件対応）
- 作成日時降順表示 ✅
- ID、内容、ステータス、タイムスタンプの返却 ✅
- 個別問い合わせ詳細取得 ✅
- 404エラーハンドリング ✅
- Web UI 一覧表示・検索機能 ❌（未実装）
- 問い合わせ編集機能 ❌（未実装）
- 更新タイムスタンプ記録 ⚠️（モデルにフィールドなし）

**ギャップ**:
1. **バックエンドAPI**:
   - `PUT /api/inquiries/{id}` エンドポイント未実装
   - リクエストモデル（`InquiryUpdateRequest`）未定義

2. **フロントエンド**:
   - 一覧表示コンポーネント未実装（`InquiriesPage.tsx` にプレースホルダーのみ）
   - 検索機能未実装
   - 編集UIコンポーネント未実装

3. **データモデル**:
   - `InquiryModel` に `updated_at` フィールドが存在しない（要件2-9で必要）
   - マイグレーションで追加が必要

**制約**:
- 既存データとの後方互換性維持（`updated_at` 追加時）
- 編集可能フィールドの定義（`content`, `status`, `metadata` など）

**複雑度シグナル**:
- 中程度（CRUD操作 + UI実装）
- データベーススキーマ変更が必要

---

### 要件3: 問い合わせの承認と却下

**技術要件**:
- 承認時のステータス更新 ❌
- 却下時のステータス更新 ❌
- 更新タイムスタンプ記録 ❌
- Web UI からの操作 ❌
- 処理済みステータス設定（`task_working`, `completed`） ⚠️（Enum定義あり、APIなし）

**ギャップ**:
1. **バックエンドAPI**:
   - ステータス更新専用エンドポイント未実装（例: `PUT /api/inquiries/{id}/approve`, `PUT /api/inquiries/{id}/reject`）
   - または汎用更新エンドポイント（`PUT /api/inquiries/{id}`）でステータス更新をサポート

2. **フロントエンド**:
   - 承認・却下UIコンポーネント未実装
   - ステータス更新APIクライアントメソッド未実装

**制約**:
- ステータス遷移ルールの定義（どのステータスから承認・却下可能か）
- 却下理由の記録方法（`metadata` に保存？）

**複雑度シグナル**:
- 中程度（ビジネスロジック + ワークフロー定義）

---

### 要件4: ユーザーインターフェース

**技術要件**:
- Web インターフェース提供 ✅（React アプリ実装済み）
- 入力フォームバリデーション ✅（React Hook Form + Zod 実装済み）
- エラーメッセージ表示 ✅
- 問い合わせ履歴表示ページ ❌（プレースホルダーのみ）
- 問い合わせ詳細表示・編集ページ ❌（未実装）

**ギャップ**:
1. **フロントエンドUI**:
   - 一覧表示コンポーネント（リスト、テーブル、カード形式など）
   - 検索・フィルタリングUI（user_id, status などで絞り込み）
   - 詳細表示モーダルまたはページ
   - 編集フォーム（インライン編集 or 専用フォーム）
   - 承認・却下ボタンコンポーネント

**制約**:
- アクセシビリティ対応（WCAG 2.1 AA準拠）
- レスポンシブデザイン（モバイル対応）
- ダークモード対応（既存のテーマシステムと統合）

**複雑度シグナル**:
- 中～高（複数のUIコンポーネント + 状態管理）

---

### 非機能要件の分析

**パフォーマンス**:
- 問い合わせ登録: < 500ms ✅（既存API対応）
- ストーリー一覧表示: < 1秒 ⚠️（フロントエンド実装次第）

**セキュリティ**:
- 入力値サニタイゼーション ✅（Pydantic バリデーション）
- SQLインジェクション対策 ✅（SQLAlchemy ORM使用）
- XSS対策 ✅（React標準機能）

**スケーラビリティ**:
- ページネーション対応 ✅（limit 1-1000, offset）
- インデックス: `timestamp`, `user_id` に必要（Research Needed）

---

## 3. 実装アプローチオプション

### Option A: 既存コンポーネント拡張（推奨）

**拡張対象ファイル**:

**バックエンド**:
1. `backend/api/inquiries.py`
   - 新規エンドポイント追加:
     - `PUT /api/inquiries/{id}` - 問い合わせ更新（汎用）
     - `PUT /api/inquiries/{id}/approve` - 承認専用（オプション）
     - `PUT /api/inquiries/{id}/reject` - 却下専用（オプション）

2. `backend/models/api/requests.py`
   - 新規リクエストモデル追加:
     - `InquiryUpdateRequest` - 編集可能フィールド定義
     - `InquiryStatusUpdateRequest` - ステータス更新専用（オプション）

3. `backend/models/database/inquiry.py`
   - `updated_at` フィールド追加
   - マイグレーションファイル作成（`alembic revision --autogenerate`）

**フロントエンド**:
1. `frontend/src/services/inquiryService.ts`
   - 新規メソッド追加:
     - `updateInquiryStatus()` - ステータス更新
     - 既存の `updateInquiry()` を有効化（バックエンド実装後）

2. `frontend/src/pages/InquiriesPage.tsx`
   - 一覧表示ロジック実装
   - TanStack React Query で状態管理

3. 新規コンポーネント作成:
   - `frontend/src/components/inquiries/InquiryList.tsx` - 一覧表示
   - `frontend/src/components/inquiries/InquiryItem.tsx` - 個別アイテム
   - `frontend/src/components/inquiries/InquiryDetailModal.tsx` - 詳細モーダル
   - `frontend/src/components/inquiries/InquiryEditForm.tsx` - 編集フォーム

**互換性評価**:
- ✅ 既存の `POST`, `GET` エンドポイントと同じパターンで実装可能
- ✅ 既存のエラーハンドリング、バリデーション、レスポンス形式を踏襲
- ✅ `InquiryResponse` モデルに `updated_at` を追加しても後方互換性あり（ORM自動マッピング）
- ⚠️ データベーススキーマ変更（`updated_at` 追加）は破壊的ではないが、マイグレーション必要

**複雑性と保守性**:
- ✅ 既存のルーターに統合されるため、ナビゲーションが容易
- ✅ 同じファイルに関連エンドポイントが集約され、保守性高い
- ⚠️ `inquiries.py` のファイルサイズ増加（現在207行 → 推定350-400行）
  - 許容範囲内（単一責任原則は維持）

**トレードオフ**:
- ✅ 最小限の新規ファイル作成（主にフロントエンドコンポーネント）
- ✅ 既存パターンの活用で実装速度が速い
- ✅ 既存インフラ（DB接続、CORS、テスト設定）をそのまま利用
- ❌ フロントエンドで複数の新規コンポーネント作成が必要
- ❌ ファイルサイズ増加のリスク（ただし許容範囲）

---

### Option B: 新規コンポーネント作成

**新規ファイル作成**:

**バックエンド**:
1. `backend/services/inquiry_service.py`
   - ビジネスロジック層を新規作成
   - 問い合わせ更新ロジック、ステータス遷移バリデーション

2. `backend/api/inquiry_status.py`
   - ステータス更新専用ルーター
   - `/api/inquiries/{id}/status` エンドポイント

**フロントエンド**:
- Option Aと同様の新規コンポーネント作成

**根拠**:
- ビジネスロジックが複雑化した場合の分離
- ステータス管理が独立したドメインとして成長する可能性

**統合ポイント**:
- `main.py` で新規ルーターを登録: `app.include_router(inquiry_status.router, prefix="/api")`
- サービス層を `api/inquiries.py` から依存性注入

**責任の境界**:
- `inquiry_service.py`: データアクセス + ビジネスロジック
- `api/inquiries.py`: HTTPリクエスト処理 + バリデーション
- `api/inquiry_status.py`: ステータス更新専用エンドポイント

**トレードオフ**:
- ✅ 関心の分離が明確
- ✅ 将来的な拡張性（複雑なワークフロー追加時）
- ❌ ファイル数増加（ナビゲーション複雑化）
- ❌ 現時点では過剰設計の可能性
- ❌ サービス層のパターンが未確立（技術負債リスク）

---

### Option C: ハイブリッドアプローチ

**組み合わせ戦略**:

**Phase 1（初期実装）**: Option A - 既存拡張
- `PUT /api/inquiries/{id}` を `api/inquiries.py` に実装
- データベースに `updated_at` 追加
- フロントエンド一覧表示実装

**Phase 2（リファクタリング）**: Option B - サービス層抽出
- ビジネスロジックが複雑化したタイミングで `inquiry_service.py` を作成
- 既存の API ルーターからロジックを移行

**段階的実装**:
1. **MVP（最小実装）**:
   - 問い合わせ更新API（`PUT /api/inquiries/{id}`）
   - フロントエンド一覧表示

2. **拡張フェーズ**:
   - 承認・却下UI実装
   - 検索・フィルタリング機能

3. **最適化フェーズ**:
   - サービス層リファクタリング
   - インデックス追加
   - パフォーマンスチューニング

**リスク軽減**:
- 増分ロールアウト（機能ごとに段階リリース）
- フィーチャーフラグ: 不要（問い合わせ管理は独立機能）
- ロールバック戦略: マイグレーションのダウングレードスクリプト用意

**トレードオフ**:
- ✅ 初期開発速度とスケーラビリティのバランス
- ✅ 反復的な改善が可能
- ❌ 複数フェーズの計画・調整が必要
- ❌ リファクタリングタイミングの見極めが必要

---

## 4. 深掘り調査が必要な項目

**Research Needed**:
1. **データベースインデックス戦略**:
   - `timestamp`, `user_id`, `status` へのインデックス追加の必要性
   - パフォーマンスベンチマーク（10,000件以上のデータでクエリ速度測定）

2. **ステータス遷移ルール定義**:
   - どのステータスから承認・却下可能か（ビジネスロジック）
   - `RECEIVED` → `TASK_WORKING` / `COMPLETED` / `REJECTED` の遷移条件

3. **却下理由の保存方法**:
   - `metadata` フィールドに `{"rejection_reason": "理由"}` として保存？
   - 専用フィールド追加（`rejection_reason` カラム）の必要性

4. **UI/UXパターン**:
   - 一覧表示形式（テーブル vs カード vs リスト）
   - 編集方法（インライン編集 vs モーダル vs 専用ページ）
   - 検索UI（検索バー + フィルタドロップダウン）

---

## 5. 実装複雑度とリスク評価

**工数見積もり**: M（3-7日）

**根拠**:
- バックエンドAPI拡張: 2日
  - `PUT /api/inquiries/{id}` 実装: 0.5日
  - `updated_at` マイグレーション: 0.5日
  - テスト作成: 1日
- フロントエンド実装: 4日
  - 一覧表示コンポーネント: 1.5日
  - 詳細・編集UI: 1.5日
  - 承認・却下ボタン統合: 0.5日
  - テスト作成: 0.5日
- 統合テスト・調整: 1日

**リスク**: Medium

**根拠**:
- ⚠️ データベーススキーマ変更（`updated_at` 追加）
  - リスク: マイグレーション失敗時のデータ損失
  - 軽減策: ダウングレードスクリプト作成、本番前にステージング環境で検証
- ⚠️ 既存データとの互換性
  - リスク: `updated_at` が NULL の既存レコード
  - 軽減策: マイグレーションで `created_at` の値を `updated_at` に初期設定
- ✅ 新規パターンの導入なし（既存パターン踏襲）
- ✅ 技術スタック全て既知（FastAPI, SQLAlchemy, React, TanStack Query）
- ✅ 統合ポイント明確（既存API、データモデル、フロントエンドサービス）

---

## 6. 設計フェーズへの推奨事項

### 推奨アプローチ: **Option A（既存拡張）**

**理由**:
- 既存のAPIパターンと完全に一致
- 最小限の新規ファイル作成（開発速度重視）
- ビジネスロジックは現時点で複雑でない（サービス層不要）
- フロントエンドは新規コンポーネント作成が不可避（どのオプションでも同じ）

### 主要な設計決定事項

1. **API設計**:
   - 汎用更新エンドポイント（`PUT /api/inquiries/{id}`）を実装
   - ステータス更新専用エンドポイントは後回し（汎用で対応可能）
   - リクエストモデル: `InquiryUpdateRequest` で編集可能フィールドを制限

2. **データモデル変更**:
   - `updated_at` フィールド追加（`DateTime`, nullable=False, default=UTC now）
   - マイグレーションで既存データに `created_at` の値を設定

3. **フロントエンド設計**:
   - TanStack React Query でサーバー状態管理
   - コンポーネント分割: List, Item, DetailModal, EditForm
   - 検索・フィルタリングはクライアントサイド実装（初期フェーズ）

4. **ステータス遷移ルール**:
   - 設計フェーズでビジネスロジック定義
   - 承認: `RECEIVED` → `TASK_WORKING`
   - 却下: `RECEIVED` → `COMPLETED` (却下理由を `metadata` に記録)

### 設計フェーズで解決すべき項目

1. **ステータス遷移の詳細ルール**:
   - どのステータスからどのステータスへ遷移可能か
   - バリデーションロジック（無効な遷移をブロック）

2. **却下理由の保存形式**:
   - `metadata` に `{"rejection": {"reason": "...", "timestamp": "..."}}` 形式で保存
   - または専用フィールド `rejection_reason: str` を追加

3. **検索・フィルタリング仕様**:
   - 初期フェーズ: クライアントサイドフィルタリング（全データ取得 → フィルタ）
   - 将来: バックエンドクエリパラメータ追加（`?status=received&user_id=xxx`）

4. **UI/UXデザイン**:
   - 一覧表示形式（テーブル推奨: ソート、ページネーション統合容易）
   - 編集方法（モーダル推奨: 既存ページとの一貫性）
   - 承認・却下ボタン配置（詳細モーダル内 or 一覧アイテム内）

---

## 7. 要件対資産マッピング

| 要件 | 既存資産 | ギャップ | タグ |
|------|----------|----------|------|
| **要件1: 問い合わせ作成** | | | |
| 1.1 データベース保存 | `InquiryModel`, `POST /api/inquiries/` | - | ✅ 実装済み |
| 1.2 タイムスタンプ等記録 | `InquiryModel` フィールド | - | ✅ 実装済み |
| 1.3 エラーメッセージ表示 | FastAPI `HTTPException` | - | ✅ 実装済み |
| 1.4 必須項目検証 | `InquiryCreateRequest` Pydantic | - | ✅ 実装済み |
| 1.5 一意ID付与 | `id` BigInteger autoincrement | - | ✅ 実装済み |
| 1.6 ステータス「received」設定 | `status` デフォルト値 | - | ✅ 実装済み |
| **要件2: 一覧表示・検索・編集** | | | |
| 2.1 ページネーション | `GET /api/inquiries/` (limit, offset) | - | ✅ 実装済み |
| 2.2 ページサイズ設定 | Query パラメータ (1-1000) | - | ✅ 実装済み |
| 2.3 作成日時降順 | `order_by(timestamp.desc())` | - | ✅ 実装済み |
| 2.4 各問い合わせ情報返却 | `InquiryResponse` | - | ✅ 実装済み |
| 2.5 個別取得 | `GET /api/inquiries/{id}` | - | ✅ 実装済み |
| 2.6 404エラー | `HTTPException 404` | - | ✅ 実装済み |
| 2.7 Web UI 一覧表示 | `InquiriesPage.tsx` プレースホルダー | UIコンポーネント未実装 | ❌ Missing |
| 2.8 問い合わせ編集 | - | `PUT /api/inquiries/{id}` 未実装 | ❌ Missing |
| 2.9 更新タイムスタンプ | - | `updated_at` フィールド未定義 | ❌ Missing |
| **要件3: 承認と却下** | | | |
| 3.1 承認時ステータス更新 | `InquiryStatus` Enum | API エンドポイント未実装 | ❌ Missing |
| 3.2 却下時ステータス更新 | `InquiryStatus` Enum | API エンドポイント未実装 | ❌ Missing |
| 3.3 更新タイムスタンプ | - | `updated_at` フィールド未定義 | ❌ Missing |
| 3.4 Web UI 操作 | - | UI コンポーネント未実装 | ❌ Missing |
| 3.5 処理済みステータス | `TASK_WORKING`, `COMPLETED` Enum | - | ✅ 実装済み |
| **要件4: ユーザーインターフェース** | | | |
| 4.1 Web インターフェース | React アプリ | - | ✅ 実装済み |
| 4.2 フォームバリデーション | `InquiryForm.tsx` (Zod) | - | ✅ 実装済み |
| 4.3 エラーメッセージ | フォーム内エラー表示 | - | ✅ 実装済み |
| 4.4 問い合わせ履歴ページ | `InquiriesPage.tsx` 骨格 | 一覧表示ロジック未実装 | ❌ Missing |
| 4.5 詳細表示・編集ページ | - | コンポーネント未実装 | ❌ Missing |

**凡例**:
- ✅ 実装済み: 既存コードで完全対応
- ❌ Missing: 実装が必要
- ⚠️ Constraint: 制約あり（後方互換性、パフォーマンス等）

---

## 8. 補足情報

### 既存テストカバレッジ
- `backend/tests/test_inquiry_api.py`: 14+テストケース
  - `POST /api/inquiries/` の成功・失敗ケース
  - `GET /api/inquiries/` のページネーション、フィルタリング
  - `GET /api/inquiries/{id}` の取得・404エラー

### 追加テストが必要な領域
- `PUT /api/inquiries/{id}` の成功・失敗ケース
- ステータス遷移バリデーション
- `updated_at` フィールドの自動更新
- フロントエンド一覧表示コンポーネント（React Testing Library）

### 参考実装パターン
- 既存の `POST /api/inquiries/` エンドポイント（`api/inquiries.py:24-80`）
  - エラーハンドリング、Pydantic バリデーション、日本語メッセージ
- `InquiryForm.tsx` （`frontend/src/components/forms/InquiryForm.tsx`）
  - React Hook Form + Zod パターン、状態管理、アクセシビリティ

---

## まとめ

**ギャップ分析結果**: 問い合わせ管理機能の基盤は実装済みだが、編集、承認・却下、一覧表示UIが未実装。実装工数は中程度（3-7日）、リスクは中程度（データベーススキーマ変更あり）。

**推奨実装戦略**: Option A（既存拡張）を採用し、`PUT /api/inquiries/{id}` を実装、フロントエンドに一覧表示・詳細・編集コンポーネントを追加。将来的な複雑化に備え、Option Cのハイブリッドアプローチ（段階的サービス層抽出）も視野に入れる。

**次ステップ**: `/kiro:spec-design inquiry` を実行し、詳細な技術設計とタスク分解を行う。設計フェーズでステータス遷移ルール、却下理由の保存形式、UI/UX詳細を確定させる。

---
inclusion: always
---

# Ghost Squad 実装状況ガイドライン

このファイルは、Ghost Squadプロジェクトの現在の実装状況と開発優先度を明確にします。新しい機能を実装する際は、この状況を考慮してください。

## 🎯 現在の実装状況（2025年12月28日時点）

### ✅ 実装済み機能

**1. プロジェクト基盤**
- Docker Compose設定（`docker-compose.yml`）- 3サービス構成（db、api、web）
- Makefile（46+の開発コマンド定義）
- 環境変数テンプレート（`.env.example`）- CORS、データベース、OpenAI、外部統合設定
- Git設定（`.gitignore`、`.dockerignore`）
- プロジェクトドキュメント（`README.md`、`docs/`）

**2. バックエンド実装（`api/`）**
- FastAPI アプリケーション（`main.py`）
  - CORS設定済み
  - ヘルスチェックエンドポイント（`/health`）
  - ルートエンドポイント（`/`）
- データベースモデル（SQLAlchemy ORM）
  - `InquiryModel` - 問い合わせエンティティ（`models/database/inquiry.py`）
  - `BaseModel` - 共通ベースモデル（`models/database/base.py`）
  - `InquiryStatus` - 問い合わせステータス列挙型（`models/enums/inquiry_status.py`）
- Pydanticスキーマ（`models/schemas/`）
  - `inquiry.py` - 問い合わせスキーマ（CreateInquiryRequest、UpdateInquiryRequest、InquiryResponse、ErrorResponse）
- サービス層（`services/`）
  - `inquiry_validator.py` - 問い合わせバリデーション（97%カバレッジ）
  - `inquiry_repository.py` - データアクセス層（90%カバレッジ、CRUD・フィルタリング・ソート・ページネーション実装）
  - `inquiry_query_service.py` - クエリサービス（100%カバレッジ、検索・一覧取得・ページネーション）
  - `inquiry_workflow_service.py` - ワークフローサービス（89%カバレッジ、承認・却下・ステータス遷移管理）
- テストコード（`tests/`）
  - pytest設定済み（`conftest.py`、`pytest.ini`）
  - 189テスト、高カバレッジ（inquiry: 91%、database接続テスト含む）
  - `test_inquiry_model.py` - Inquiryモデルテスト
  - `test_inquiry_schemas.py` - Pydanticスキーマテスト
  - `test_inquiry_validator.py` - バリデーションテスト
  - `test_inquiry_repository.py` - リポジトリテスト（17テスト）
  - `test_inquiry_query_service.py` - クエリサービステスト（12テスト、100%カバレッジ）
  - `test_inquiry_workflow_service.py` - ワークフローサービステスト
  - カバレッジレポート設定（`.coveragerc`）
- 依存関係定義（`requirements.txt`）- FastAPI、SQLAlchemy、Alembic、pytest等
- コード品質設定（`.flake8`、`mypy.ini`）

**3. フロントエンド実装（`web/`）**
- React アプリケーション（**TypeScript実装完了** ✅）
  - `package.json` - React 18、Testing Library設定、TypeScript 4.9.5、Axios 1.6.2
  - `App.tsx` - メインアプリケーションコンポーネント（TypeScript化）
  - `index.tsx` - エントリーポイント（TypeScript化）
  - `App.test.tsx` - アプリケーションテスト（TypeScript化）
  - `tsconfig.json` - TypeScript strict mode設定
- 型定義（`src/types/`）
  - `inquiry.ts` - Inquiry関連型定義（InquiryResponse、CreateInquiryRequest、ErrorResponse等）
  - `index.ts` - 型エクスポート
- APIクライアントサービス（`src/services/`）
  - `inquiryApi.ts` - 問い合わせAPI呼び出し実装（Axios、エラーインターセプター、75%カバレッジ）
  - `index.ts` - サービスエクスポート
- テスト設定
  - `setupTests.ts` - TypeScript化
  - `__mocks__/axios.ts` - Axiosマニュアルモック（エラーハンドリングテスト用）
  - `inquiryApi.test.ts` - APIクライアント包括的テスト（9テスト、エラーハンドリング含む）
- 依存関係定義（`package.json`、`package-lock.json`）
  - TypeScript: `@types/react`, `@types/react-dom`, `@types/node`, `@types/jest`
  - コード品質: `prettier`, `eslint-config-prettier`, `eslint-plugin-prettier`
- コード品質設定
  - `.prettierrc.json` - Prettierフォーマット設定
  - `.prettierignore` - フォーマット除外ファイル

**4. 設計・仕様ドキュメント**
- `.kiro/specs/inquiry/` - 問い合わせ機能仕様
  - Phase: tasks-generated
  - Requirements（生成済み・承認済み）
  - Design（生成済み・承認済み）
  - Tasks（生成済み）
  - Gap Analysis（生成済み）
  - Dependencies: なし
- `.kiro/specs/story/` - ストーリー機能仕様
  - Phase: requirements-generated
  - Requirements（生成済み）
  - Dependencies: inquiry

**5. ステアリングドキュメント（`.kiro/steering/`）**
- `product.md` - プロダクト開発ガイドライン
- `tech.md` - 技術スタック・開発環境ガイドライン
- `structure.md` - プロジェクト構造・組織化ガイドライン
- `implementation-status.md` - このファイル

### 🚧 部分実装・未実装機能

**バックエンド（`api/`）**
- ✅ Alembic マイグレーションファイル（作成済み）
- ✅ データベース接続設定（`database.py` 作成済み）
- ✅ Pydanticスキーマ（`models/schemas/inquiry.py` 実装済み）
- ✅ サービス層（`services/` 実装済み - バリデーション＋リポジトリ＋クエリ＋ワークフロー）
- ✅ ワークフローサービス（`InquiryWorkflowService` 実装済み - 89%カバレッジ）
- ✅ クエリサービス（`InquiryQueryService` 実装済み - 100%カバレッジ）
- ✅ **APIエンドポイント**（`routers/inquiry.py` 実装完了 - CRUD + ワークフロー）
  - POST /api/inquiries - 問い合わせ作成
  - GET /api/inquiries - 問い合わせ一覧（ページネーション・フィルタリング・ソート）
  - GET /api/inquiries/{id} - 問い合わせ詳細
  - PUT /api/inquiries/{id} - 問い合わせ更新
  - POST /api/inquiries/{id}/approve - 承認処理
  - POST /api/inquiries/{id}/reject - 却下処理
- ❌ ストーリーモデル（`story.py` 未作成）

**フロントエンド（`web/`）**
- ✅ TypeScript設定（完了 - strict mode、tsconfig.json）
- ✅ 型定義（完了 - `src/types/inquiry.ts`、バックエンドスキーマと整合）
- ✅ Axios設定（完了 - `src/services/inquiryApi.ts`、エラーインターセプター実装）
- ✅ サービス層基盤（完了 - APIクライアント実装、75%カバレッジ、9テスト）
- ✅ テスト基盤（完了 - Jest + RTL + TypeScript、Axiosマニュアルモック）
- ✅ コード品質基盤（完了 - Prettier + ESLint設定）
- ❌ Tailwind CSS設定（未設定）
- ❌ React Router設定（未設定）
- ❌ TanStack React Query設定（未設定）
- ❌ コンポーネント（UIコンポーネント未作成）
- ❌ ページ（ページコンポーネント未作成）

## 📋 次のステップ

### 実装の優先順位

**Phase 1: バックエンド基盤の完成（優先度：高）**
1. ✅ ~~`api/requirements.txt` の作成~~ （完了）
2. ✅ ~~データベース接続設定（`database.py`）~~ （完了）
3. ✅ ~~Alembic初期化とマイグレーション~~ （完了）
4. ✅ ~~Pydanticスキーマ作成（`models/schemas/inquiry.py`）~~ （完了）
5. ✅ ~~InquiryValidator実装~~ （完了）
6. ✅ ~~InquiryRepository実装（データアクセス層）~~ （完了）
7. ❌ 開発環境の動作確認（`make dev`、`make db-migrate`）

**Phase 2: Inquiry機能の完全実装（優先度：高）** - 🎉 **バックエンド完了**
- `.kiro/specs/inquiry/` の仕様に従って実装
- Tasks: 全バックエンドタスク完了（データモデル → サービス層 → API層）
- 進捗: データモデル → バリデーション → データアクセス層 → サービス層 → **API層完了** ✅
- 次: フロントエンド実装 → 統合テスト
- 実装状況:
  - ✅ ~~InquiryRepository（データアクセス層）~~ （完了 - 90%カバレッジ）
  - ✅ ~~InquiryWorkflowService（ワークフロー管理）~~ （完了 - 89%カバレッジ）
  - ✅ ~~InquiryQueryService（クエリサービス）~~ （完了 - 100%カバレッジ）
  - ✅ ~~問い合わせCRUD APIエンドポイント（ルーター層）~~ （完了 - 全エンドポイント実装済み）
  - ✅ ~~トランザクション管理・エラーハンドリング強化~~ （完了 - PR #80, #81, #82）
  - ❌ 問い合わせ一覧・詳細画面（React）
  - ❌ 問い合わせ登録フォーム（React + Validation）
  - ❌ E2Eテスト・統合テスト

**Phase 3: フロントエンド基盤の完成（優先度：中）** - 🎉 **基盤完了**
1. ✅ ~~`web/package.json` の作成~~ （完了）
2. ✅ ~~TypeScriptへの移行（`.tsx`、`tsconfig.json`）~~ （完了）
3. ✅ ~~型定義作成（`src/types/inquiry.ts`）~~ （完了）
4. ✅ ~~Axios設定（API通信、エラーハンドリング）~~ （完了）
5. ✅ ~~テスト基盤（Jest + RTL + TypeScript）~~ （完了）
6. ✅ ~~コード品質設定（Prettier + ESLint）~~ （完了）
7. ❌ Tailwind CSS設定
8. ❌ React Router設定
9. ❌ TanStack React Query設定

**Phase 4: Story機能の実装（優先度：中）**
- `.kiro/specs/story/` の設計・タスク生成から開始
- Inquiry機能への依存があるため、Phase 2完了後に着手
- Requirements生成済み、次は Design生成が必要

## 🔧 技術的な考慮事項

### データベース
- **ID型**: BigInteger（64ビット整数）使用予定
- **タイムゾーン**: UTC統一
- **JSON列**: 適切なデフォルト値設定（`{}`）
- **マイグレーション**: Alembic による管理
- **外部キー**: 適切な制約設定

### API設計
- **RESTful**: 標準的なREST API設計
- **エラーハンドリング**: 日本語メッセージ対応
- **ページネーション**: limit、offset対応
- **バリデーション**: Pydantic 2.x使用
- **CORS**: localhost:3000、Docker内部通信対応

### フロントエンド
- **技術スタック**: React 18+ + TypeScript 4.9+ + Tailwind CSS 3.3+
- **状態管理**: TanStack React Query（サーバー状態管理）
- **フォーム**: React Hook Form + Zod バリデーション
- **API通信**: Axios（プロキシ設定）
- **型安全性**: strict モード、バックエンドと型定義を統一

### 開発環境
- **コンテナ化**: Docker Compose
- **自動化**: Makefile
- **テスト**: pytest（バックエンド）、Jest + RTL（フロントエンド）
- **品質管理**: black、flake8、mypy、prettier

## 📝 開発時の注意事項

### 新規実装時の原則
1. **仕様ファースト**: `.kiro/specs/` の仕様を確認してから実装
2. **ガイドライン遵守**: `.kiro/steering/` のガイドラインに従う
3. **段階的実装**: 小さな単位で実装 → テスト → コミット
4. **型安全性**: TypeScript strict mode、mypy strict mode
5. **テストカバレッジ**: 新機能は80%以上を目標

### 実装順序
1. バックエンドAPI（データモデル → エンドポイント → テスト）
2. フロントエンド型定義（バックエンドと整合性を保つ）
3. フロントエンドコンポーネント（サービス層 → UI）
4. 統合テスト
5. ドキュメント更新

### コード品質基準
- **フォーマット**: black（Python）、prettier（TypeScript）
- **リント**: flake8 + mypy（Python）、ESLint（TypeScript）
- **テスト**: pytest（Python）、Jest（TypeScript）
- **セキュリティ**: bandit（Python）、ESLint security rules（TypeScript）

## 🚀 マイルストーン

### 短期目標（1週間）
- [ ] 開発環境の再構築
- [ ] `api/requirements.txt` 作成
- [ ] `web/package.json` 作成
- [ ] Docker環境の動作確認
- [ ] Inquiry仕様のタスク承認

### 中期目標（2-4週間）
- [ ] Inquiry機能のバックエンド実装
- [ ] Inquiry機能のフロントエンド実装
- [ ] Inquiry機能の統合テスト
- [ ] Story仕様の要件・設計生成

### 長期目標（1-3ヶ月）
- [ ] Story機能の実装
- [ ] AI統合（OpenAI API）
- [ ] 外部システム統合（Trello、Jira、GitHub Projects）
- [ ] 通知システム
- [ ] 高度な検索・フィルタリング

## 📈 開発進捗追跡

### 完了済み（65%） - 🚀 フロントエンド基盤完成
- ✅ プロジェクト基盤（Docker、Makefile、ドキュメント）
- ✅ 仕様定義（Inquiry: implementation phase、Story: requirements-generated）
- ✅ ステアリングドキュメント
- ✅ バックエンド基本構成（FastAPI、モデル、テスト設定）
- ✅ フロントエンド基本構成（React、テスト設定）
- ✅ 依存関係定義（requirements.txt、package.json）
- ✅ Inquiryデータアクセス層（InquiryRepository、InquiryValidator）
- ✅ Inquiryサービス層（InquiryQueryService、InquiryWorkflowService）
- ✅ Pydanticスキーマ（CreateInquiryRequest、UpdateInquiryRequest、InquiryResponse）
- ✅ **Inquiry API層完全実装**（CRUD + ワークフロー全エンドポイント）
- ✅ **トランザクション管理・エラーハンドリング**（PR #80, #81, #82で強化）
- ✅ 包括的バックエンドテスト（189テスト、高カバレッジ）
- ✅ **TypeScript完全移行**（strict mode、tsconfig.json）
- ✅ **型定義基盤**（InquiryResponse、CreateInquiryRequest、ErrorResponse等）
- ✅ **APIクライアントサービス**（Axios、エラーインターセプター、75%カバレッジ）
- ✅ **フロントエンドテスト基盤**（Jest + RTL + TypeScript、9テスト）
- ✅ **コード品質基盤**（Prettier + ESLint設定）

### 進行中（5%）
- 🔄 Inquiry UI実装（一覧・詳細・登録フォーム）
- 🔄 フロントエンド高度機能（Tailwind、Router、Query）

### 未着手（30%）
- ❌ Inquiry機能のUIコンポーネント実装
- ❌ Story機能の設計・実装
- ❌ AI統合（OpenAI API）
- ❌ 外部システム統合（Trello、Jira、GitHub Projects）
- ❌ E2Eテスト・統合テスト

---

**最終更新**: 2025年12月30日
**更新理由**: フロントエンド基盤完成 - TypeScript完全移行、型定義・APIクライアント実装、テスト基盤・コード品質基盤整備（Tasks 7.1, 7.2完了）

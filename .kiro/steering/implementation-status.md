---
inclusion: always
---

# Ghost Squad 実装状況ガイドライン

このファイルは、Ghost Squadプロジェクトの現在の実装状況と開発優先度を明確にします。新しい機能を実装する際は、この状況を考慮してください。

## 🎯 現在の実装状況（2025年12月25日時点）

### ✅ 完全実装済み

**1. プロジェクト基盤**
- Docker Compose開発環境（PostgreSQL 15 Alpine + FastAPI + React）
- Makefile統合（46+の開発コマンド）
- 環境変数管理（.env.example）
- Git設定（.gitignore、.dockerignore）

**2. バックエンドAPI（FastAPI）**
- 問い合わせ管理API（完全実装）
  - `POST /api/inquiries` - 問い合わせ作成（バリデーション付き）
  - `GET /api/inquiries` - 一覧取得（ページネーション: limit 1-1000, offset対応）
  - `GET /api/inquiries/{id}` - 個別取得
  - 日本語エラーメッセージ対応
- システムAPI
  - `GET /health` - ヘルスチェック（DB接続状態含む）
  - `GET /api/info` - API情報
  - `GET /api/db-test` - データベーステスト
  - `GET /` - ルートエンドポイント
- CORS設定（localhost:3000, Docker内部通信対応）
- 依存性注入（データベースセッション管理）
- アプリケーションライフサイクル管理

**3. データベース（PostgreSQL + SQLAlchemy）**
- 完全なスキーマ設計（BigInteger ID使用）
- Alembicマイグレーション管理
- 統合マイグレーション（`initial_schema_for_storyboard.py`）
- テストデータシーディング（4件の問い合わせ、3件のストーリー、3件のテンプレート）
- JSON列のデフォルト値設定（スキーマ整合性確保）
- UTC タイムゾーン統一
- 適切な外部キー制約

**4. データモデル**
- InquiryModel（問い合わせ）- 完全実装
- StoryModel（ストーリー）- 完全実装
- StoryTemplateModel（テンプレート）- 完全実装
- 全Enumクラス（InquiryStatus、StoryStatus、Priority、StoryCategory、StoryPattern）
- Pydanticスキーマ（API Request/Response）
- 型定義（TypeScript側も完全対応）

**5. テスト**
- 14+テストケース（inquiry API完全カバー）
- ユニットテスト（API、データベース、シーディング）
- 統合テスト（エンドツーエンド）
- テストデータ管理
- pytest + pytest-asyncio + pytest-cov 設定済み

### 🚧 部分実装済み（開発中）

**1. React TypeScriptフロントエンド**
- 基本セットアップ（Create React App + TypeScript）
- ルーティング設定（React Router DOM）
- レイアウトシステム（基本的なLayout.tsx）
- ページ構造（HomePage, InquiriesPage, TasksPage - プレースホルダー）
- 型定義（35ファイル、バックエンドと完全対応）
- 依存関係（TanStack Query, React Hook Form, Zod, Tailwind CSS）
- **未実装**: 実際のコンポーネント、API統合、状態管理

**2. フロントエンド型システム**
- 完全なTypeScript型定義（35ファイル）
- Enumクラス（バックエンドと完全対応）
- APIリクエスト・レスポンス型
- モデル型定義
- エクスポート型定義
- **未実装**: 実際の使用、バリデーション統合

### ❌ 未実装（計画済み）

**1. AI統合（OpenAI API）**
- StoryConverterクラス
- ストーリー生成エンドポイント
- 期限抽出機能
- プロンプト設計
- AI品質保証機能

**2. ストーリー管理API**
- `GET /api/stories` - ストーリー一覧
- `POST /api/stories` - ストーリー作成
- `PUT /api/stories/{id}` - ストーリー更新
- `DELETE /api/stories/{id}` - ストーリー削除
- `POST /api/stories/generate` - AI生成エンドポイント
- 承認・拒否ワークフロー
- 一括操作

**3. フロントエンド機能コンポーネント**
- 問い合わせ入力フォーム（InquiryForm）
- 問い合わせ一覧（InquiryList）
- ストーリー表示・編集コンポーネント
- APIクライアントサービス
- 状態管理実装
- フォームハンドリング実装

**4. 問い合わせAPI拡張**
- `PUT /api/inquiries/{id}` - 問い合わせ更新
- `DELETE /api/inquiries/{id}` - 問い合わせ削除
- フィルタリング機能拡張
- 検索機能

### 📋 将来実装（長期計画）

**1. 高度なストーリー管理**
- パターン認識とテンプレート適用
- 変更履歴管理
- コメント・メモ機能
- ストーリー依存関係管理

**2. 外部システム統合**
- Trello、Jira、GitHub Projects連携
- エクスポート機能（`POST /api/export/*`）
- 同期状態追跡
- Webhook対応

**3. 通知システム**
- メール通知
- Webhook通知
- 期限アラート
- リアルタイム更新

**4. 検索・フィルタリング**
- 全文検索
- 高度なフィルタリング
- 並び替え機能
- 保存済み検索

**5. テンプレート管理**
- `GET /api/templates` - テンプレート一覧
- `POST /api/templates` - カスタムテンプレート作成
- テンプレート共有機能
- 業界別テンプレート

## 🎯 開発優先度

### Phase 1: フロントエンド基本機能（現在の最優先）
1. **APIクライアントサービス** - Axiosベースのサービス層作成
2. **問い合わせ入力フォーム** - React Hook Form + Zod バリデーション
3. **問い合わせ履歴表示** - TanStack Query + ページネーション
4. **基本的なUI/UX** - Tailwind CSS + Lucide React

### Phase 2: ストーリー管理API
1. **ストーリーCRUD API** - 基本的なストーリー操作
2. **ストーリー表示UI** - ストーリー一覧・詳細表示
3. **ストーリー編集機能** - インライン編集
4. **基本的なワークフロー** - 承認・拒否機能

### Phase 3: AI統合
1. **OpenAI API統合** - ストーリー生成機能
2. **AI生成UI** - 生成進捗表示・結果表示
3. **生成品質向上** - プロンプト最適化・バリデーション
4. **テンプレート活用** - AI生成時のテンプレート適用

### Phase 4: 高度な機能
1. **外部システム統合** - エクスポート機能
2. **通知システム** - リアルタイム通知
3. **検索・フィルタリング** - 高度な検索機能
4. **パフォーマンス最適化** - キャッシュ・最適化

## 🔧 技術的な考慮事項

### データベース
- **ID型**: BigInteger（64ビット整数）使用
- **タイムゾーン**: UTC統一
- **JSON列**: 適切なデフォルト値設定済み（`{}`）
- **マイグレーション**: 統合マイグレーション（`initial_schema_for_storyboard.py`）で管理
- **外部キー**: 適切な制約設定済み

### API設計
- **RESTful**: 標準的なREST API設計
- **エラーハンドリング**: 日本語メッセージ対応
- **ページネーション**: limit（1-1000）、offset対応
- **バリデーション**: Pydantic 2.5.0使用
- **CORS**: localhost:3000、Docker内部通信対応

### フロントエンド
- **技術スタック**: React 18.2.0 + TypeScript 4.9.5 + Tailwind CSS 3.3.5
- **状態管理**: TanStack React Query 5.8.4（設定済み、未使用）
- **フォーム**: React Hook Form 7.47.0 + Zod 3.22.4（設定済み、未使用）
- **API通信**: Axios 1.6.2（プロキシ設定済み）
- **型安全性**: 35の型定義ファイル、バックエンドと完全対応

### 開発環境
- **コンテナ化**: Docker Compose（PostgreSQL 15 Alpine + FastAPI + React）
- **自動化**: Makefile（46+コマンド）
- **テスト**: pytest 7.4.3（バックエンド）、Jest + RTL + fast-check（フロントエンド）
- **品質管理**: black 23.11.0、flake8 6.1.0、mypy 1.7.1、prettier

## 📊 実装状況の詳細

### 実装済みAPIエンドポイント（7個）
```
# 問い合わせ管理（3個）
POST   /api/inquiries              # 問い合わせ作成
GET    /api/inquiries              # 一覧取得（ページネーション）
GET    /api/inquiries/{id}         # 個別取得

# システム（4個）
GET    /                           # ルート
GET    /health                     # ヘルスチェック
GET    /api/info                   # API情報
GET    /api/db-test                # データベーステスト
```

### 未実装APIエンドポイント
```
# 問い合わせ拡張
PUT    /api/inquiries/{id}         # 問い合わせ更新
DELETE /api/inquiries/{id}         # 問い合わせ削除

# ストーリー管理
GET    /api/stories                # ストーリー一覧
POST   /api/stories                # ストーリー作成
PUT    /api/stories/{id}           # ストーリー更新
DELETE /api/stories/{id}           # ストーリー削除
POST   /api/stories/generate       # AI生成

# テンプレート管理
GET    /api/templates              # テンプレート一覧
POST   /api/templates              # カスタムテンプレート作成

# 外部統合
POST   /api/export/trello          # Trelloエクスポート
POST   /api/export/jira            # Jiraエクスポート
POST   /api/export/github          # GitHub Projectsエクスポート
```

### フロントエンド実装状況
```
実装済み:
- App.tsx（ルーティング設定）
- Layout.tsx（基本レイアウト）
- HomePage.tsx（機能紹介、API接続確認）
- 型定義（35ファイル、完全）

プレースホルダー:
- InquiriesPage.tsx（"Coming Soon"メッセージのみ）
- TasksPage.tsx（基本構造のみ）

空ディレクトリ:
- hooks/（カスタムフック用）
- services/（API クライアント用）
- utils/（ユーティリティ関数用）
```

## 📝 開発時の注意事項

### 新機能実装時
1. **既存APIとの整合性**: 現在のAPI設計パターンに従う
   - Pydantic バリデーション使用
   - 日本語エラーメッセージ
   - 適切なHTTPステータスコード
2. **データモデル**: BigInteger IDと既存スキーマを維持
3. **テスト**: 新機能には必ずテストを追加（現在14+テスト）
4. **型定義**: TypeScript側の型定義も同時更新

### コード品質
- **テストカバレッジ**: 現在は問い合わせAPIのみカバー、新機能は80%以上を目標
- **型安全性**: TypeScript strict mode、mypy strict mode
- **コードスタイル**: 既存のフォーマット設定に従う
  - Backend: black 23.11.0 + flake8 6.1.0 + mypy 1.7.1
  - Frontend: prettier + ESLint

### データベース変更
- **マイグレーション**: 必ずAlembicを使用
- **後方互換性**: 既存データを保護
- **テスト**: マイグレーション前後でテスト実行
- **JSON列**: デフォルト値 `{}` を設定

### フロントエンド開発
- **API統合**: まずservices/ディレクトリにAPIクライアント作成
- **状態管理**: TanStack React Query を活用
- **フォーム**: React Hook Form + Zod バリデーション
- **型安全性**: 既存の35型定義ファイルを活用

## 🚀 次のマイルストーン

### 短期目標（1-2週間）
- [ ] **APIクライアントサービス作成** - services/inquiryService.ts
- [ ] **問い合わせ入力フォーム実装** - components/forms/InquiryForm.tsx
- [ ] **問い合わせ履歴表示実装** - components/lists/InquiryList.tsx
- [ ] **フロントエンド・バックエンド統合テスト**

### 中期目標（1ヶ月）
- [ ] **ストーリー管理API実装** - api/stories.py
- [ ] **ストーリー表示コンポーネント** - components/stories/
- [ ] **OpenAI API統合準備** - services/aiService.ts
- [ ] **基本的なレビューワークフロー**

### 長期目標（3ヶ月）
- [ ] **AI統合完了** - ストーリー生成機能
- [ ] **外部システム統合** - エクスポート機能
- [ ] **通知システム** - リアルタイム通知
- [ ] **高度な検索・フィルタリング**
- [ ] **パフォーマンス最適化**

## 📈 開発進捗追跡

### 完了済み機能（推定40%）
- ✅ プロジェクト基盤
- ✅ バックエンドAPI（問い合わせ管理）
- ✅ データベース設計・マイグレーション
- ✅ 開発環境・ツール
- ✅ 型定義システム

### 進行中機能（推定20%）
- 🚧 フロントエンド基本構造
- 🚧 テストカバレッジ拡張

### 未着手機能（推定40%）
- ❌ ストーリー管理API
- ❌ AI統合
- ❌ フロントエンド機能コンポーネント
- ❌ 外部システム統合

この実装状況ガイドラインは、プロジェクトの進捗に応じて定期的に更新されます。最終更新: 2025年12月25日
---
inclusion: always
---

# Ghost Squad 実装状況ガイドライン

このファイルは、Ghost Squadプロジェクトの現在の実装状況と開発優先度を明確にします。新しい機能を実装する際は、この状況を考慮してください。

## 🎯 現在の実装状況（2025年12月25日時点）

### ✅ 完全実装済み

**1. プロジェクト基盤**
- Docker Compose開発環境（PostgreSQL + FastAPI + React）
- Makefile統合（46の開発コマンド）
- 環境変数管理（.env.example）
- Git設定（.gitignore、.dockerignore）

**2. バックエンドAPI（FastAPI）**
- 問い合わせ管理API（完全実装）
  - `POST /api/inquiries` - 問い合わせ作成
  - `GET /api/inquiries` - 一覧取得（ページネーション対応）
  - `GET /api/inquiries/{id}` - 個別取得
- システムAPI
  - `GET /health` - ヘルスチェック
  - `GET /api/info` - API情報
  - `GET /api/db-test` - データベーステスト
- CORS設定（フロントエンド連携準備済み）
- 依存性注入（データベースセッション管理）

**3. データベース（PostgreSQL + SQLAlchemy）**
- 完全なスキーマ設計（BigInteger ID使用）
- Alembicマイグレーション管理
- 統合マイグレーション（`initial_schema_for_storyboard.py`）
- テストデータシーディング（4件の問い合わせ、3件のストーリー、3件のテンプレート）
- JSON列のデフォルト値設定（スキーマ整合性確保）

**4. データモデル**
- InquiryModel（問い合わせ）- 完全実装
- StoryModel（ストーリー）- 完全実装
- StoryTemplateModel（テンプレート）- 完全実装
- 全Enumクラス（InquiryStatus、StoryStatus、Priority、StoryCategory）
- Pydanticスキーマ（API Request/Response）

**5. テスト**
- 46テストケース、98%カバレッジ
- ユニットテスト（API、データベース、シーディング）
- 統合テスト（エンドツーエンド）
- テストデータ管理

### 🚧 開発中（次の優先実装）

**1. React TypeScriptフロントエンド**
- 基本セットアップ（Create React App）
- 問い合わせフォーム（InquiryForm）
- 問い合わせ一覧（InquiryList）
- APIクライアント（Axios）

**2. AI統合（OpenAI API）**
- StoryConverterクラス
- ストーリー生成エンドポイント
- 期限抽出機能

**3. ストーリー管理API**
- ストーリーCRUD操作
- 承認・拒否ワークフロー
- 一括操作

### 📋 未実装（将来の機能）

**1. 高度なストーリー管理**
- パターン認識とテンプレート適用
- 変更履歴管理
- コメント・メモ機能

**2. 外部システム統合**
- Trello、Jira、GitHub Projects連携
- エクスポート機能
- 同期状態追跡

**3. 通知システム**
- メール通知
- Webhook通知
- 期限アラート

**4. 検索・フィルタリング**
- 全文検索
- 高度なフィルタリング
- リアルタイム更新

## 🎯 開発優先度

### Phase 1: WebUI基本機能（現在）
1. React TypeScriptアプリケーション設定
2. 問い合わせ入力フォーム
3. 問い合わせ履歴表示
4. 基本的なUI/UX

### Phase 2: AI統合
1. OpenAI API統合
2. ストーリー生成機能
3. 生成されたストーリーの表示
4. 基本的なレビュー機能

### Phase 3: ストーリー管理
1. ストーリー編集機能
2. 承認・拒否ワークフロー
3. 一括操作
4. 検索・フィルタリング

### Phase 4: 外部統合
1. エクスポート機能
2. 外部システム連携
3. 通知システム
4. 高度な管理機能

## 🔧 技術的な考慮事項

### データベース
- **ID型**: BigInteger（64ビット整数）使用
- **タイムゾーン**: UTC統一
- **JSON列**: 適切なデフォルト値設定済み
- **マイグレーション**: 統合マイグレーションで管理

### API設計
- **RESTful**: 標準的なREST API設計
- **エラーハンドリング**: 日本語メッセージ対応
- **ページネーション**: 実装済み
- **バリデーション**: Pydantic使用

### フロントエンド
- **技術スタック**: React + TypeScript + Tailwind CSS
- **状態管理**: TanStack React Query（予定）
- **フォーム**: React Hook Form + Zod（予定）
- **API通信**: Axios

### 開発環境
- **コンテナ化**: Docker Compose
- **自動化**: Makefile（46コマンド）
- **テスト**: pytest（バックエンド）、Jest（フロントエンド予定）
- **品質管理**: black、flake8、mypy、prettier

## 📝 開発時の注意事項

### 新機能実装時
1. **既存APIとの整合性**: 現在のAPI設計パターンに従う
2. **データモデル**: BigInteger IDと既存スキーマを維持
3. **テスト**: 新機能には必ずテストを追加
4. **ドキュメント**: README.mdとDATABASE.mdを更新

### コード品質
- **カバレッジ**: 最低80%を維持
- **型安全性**: TypeScript strict mode、mypy strict mode
- **コードスタイル**: 既存のフォーマット設定に従う

### データベース変更
- **マイグレーション**: 必ずAlembicを使用
- **後方互換性**: 既存データを保護
- **テスト**: マイグレーション前後でテスト実行

## 🚀 次のマイルストーン

### 短期目標（1-2週間）
- [ ] React TypeScriptアプリケーション基本セットアップ
- [ ] 問い合わせ入力フォーム実装
- [ ] 問い合わせ履歴表示実装
- [ ] フロントエンド・バックエンド統合テスト

### 中期目標（1ヶ月）
- [ ] OpenAI API統合
- [ ] ストーリー生成機能
- [ ] ストーリー管理API
- [ ] 基本的なレビューワークフロー

### 長期目標（3ヶ月）
- [ ] 外部システム統合
- [ ] 通知システム
- [ ] 高度な検索・フィルタリング
- [ ] パフォーマンス最適化

この実装状況ガイドラインは、プロジェクトの進捗に応じて定期的に更新されます。
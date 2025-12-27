---
inclusion: always
---

# Ghost Squad 実装状況ガイドライン

このファイルは、Ghost Squadプロジェクトの現在の実装状況と開発優先度を明確にします。新しい機能を実装する際は、この状況を考慮してください。

## 🎯 現在の実装状況（2025年12月27日時点）

### 🔄 実装リセット通知

**重要**: 2025年12月27日に `backend/` と `frontend/` ディレクトリ内の実装を全て削除しました。
- 現在は**設計と仕様のみ**が存在し、**コード実装はゼロ**からの状態です
- プロジェクト基盤（Docker設定、Makefile、ドキュメント）は維持されています
- `.kiro/specs/` の仕様定義は保持されており、これに基づいて再実装を行います

### ✅ 現在存在するもの

**1. プロジェクト基盤**
- Docker Compose設定（`docker-compose.yml`）
- Makefile（46+の開発コマンド定義）
- 環境変数テンプレート（`.env.example`）
- Git設定（`.gitignore`、`.dockerignore`）
- プロジェクトドキュメント（`README.md`、`docs/`）

**2. 設計・仕様ドキュメント**
- `.kiro/specs/inquiry/` - 問い合わせ機能仕様
  - Phase: tasks-generated
  - Requirements（生成済み・承認済み）
  - Design（生成済み・承認済み）
  - Tasks（生成済み・未承認）
  - Dependencies: なし
- `.kiro/specs/story/` - ストーリー機能仕様
  - Phase: init
  - Dependencies: inquiry
  - まだ要件生成前の段階

**3. ステアリングドキュメント（`.kiro/steering/`）**
- `product.md` - プロダクト開発ガイドライン
- `tech.md` - 技術スタック・開発環境ガイドライン
- `structure.md` - プロジェクト構造・組織化ガイドライン
- `implementation-status.md` - このファイル

### ❌ 現在存在しないもの（削除済み）

**バックエンド実装（`backend/`）**
- FastAPI アプリケーション
- データベースモデル（SQLAlchemy ORM）
- API エンドポイント
- Alembic マイグレーションファイル
- テストコード
- 依存関係定義（`requirements.txt`）
- 全ての Python ソースファイル

**フロントエンド実装（`frontend/`）**
- React アプリケーション
- TypeScript 型定義
- コンポーネント
- ページ
- サービス層
- 依存関係定義（`package.json`、`package-lock.json`）
- 設定ファイル（`tsconfig.json`、`tailwind.config.js` など）
- 全ての TypeScript/JavaScript ソースファイル

## 📋 次のステップ

### 実装の優先順位

**Phase 1: 基盤の再構築**
1. `backend/requirements.txt` の作成
2. `frontend/package.json` の作成
3. Docker イメージのビルド確認
4. 開発環境の動作確認

**Phase 2: Inquiry機能の実装**
- `.kiro/specs/inquiry/` の仕様に従って実装
- Tasks が生成済みなので、承認後に実装開始可能
- バックエンド → フロントエンドの順で実装推奨

**Phase 3: Story機能の実装**
- `.kiro/specs/story/` の要件生成から開始
- Inquiry機能への依存があるため、Phase 2完了後に着手

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
- [ ] `backend/requirements.txt` 作成
- [ ] `frontend/package.json` 作成
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

### 完了済み（10%）
- ✅ プロジェクト基盤（Docker、Makefile、ドキュメント）
- ✅ 仕様定義（Inquiry: tasks-generated、Story: init）
- ✅ ステアリングドキュメント

### 次のステップ（5%）
- 🔄 開発環境の再構築

### 未着手（85%）
- ❌ バックエンド実装
- ❌ フロントエンド実装
- ❌ AI統合
- ❌ 外部システム統合
- ❌ テスト実装

---

**最終更新**: 2025年12月27日
**更新理由**: backend/ と frontend/ の実装を全削除、設計のみの状態に更新

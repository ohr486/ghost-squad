# ストーリーボード機能 実装計画

## 概要

Ghost Squadのストーリーボード機能をPython（FastAPIバックエンド）とTypeScript（Reactフロントエンド）で実装します。**WebUIを先行実装**してユーザー体験を早期に確認できるよう、最小限のAPIエンドポイントとReact TypeScriptフロントエンドを優先的に実装し、その後バックエンド機能を段階的に拡張します。バックエンドはFastAPI + SQLAlchemy + PostgreSQL、フロントエンドはReact + TypeScript + Tailwind CSSで構築し、OpenAI APIを使用したストーリー変換、外部カンバンシステム（Trello、Jira、GitHub Projects）との統合を含みます。

## タスク

- [x] 1. プロジェクト構造とコアインターフェースの設定
  - [x] 1.1 ディレクトリ構造の作成
    - backend/、frontend/ディレクトリの作成
    - _要件: 全般_
  
  - [x] 1.2 依存関係の定義
    - バックエンド依存関係の定義（requirements.txt）
    - フロントエンド依存関係の定義（package.json）
    - _要件: 全般_
  
  - [x] 1.3 WebUI用コア型定義
    - TypeScript: Inquiry、Story、InquiryStatus、StoryStatus型
    - Python: InquiryModel、StoryModel、InquiryStatus、StoryStatus型ヒント
    - _要件: 全般_

- [x] 2. 開発環境とツールチェーンの設定
  - [x] 2.1 Docker Compose設定
    - PostgreSQLデータベースコンテナ
    - バックエンドAPIコンテナ
    - フロントエンドコンテナ
    - 開発用ボリュームマウント設定
    - _要件: 9.1, 9.3_

  - [x] 2.2 Makefileによる開発ツール統合
    - **基本コマンド:**
      - `make setup`: 初期環境構築
      - `make clean`: 環境クリーンアップ
    - **開発サーバー管理:**
      - `make dev`: 開発サーバー起動（バックグラウンド）
      - `make stop`: 開発サーバー停止
      - `make restart`: 開発サーバー再起動
    - **テスト実行:**
      - `make test`: 全テスト実行
      - `make test-backend`: バックエンドテスト
      - `make test-frontend`: フロントエンドテスト
    - **コード品質チェック:**
      - `make lint`: コード品質チェック
      - `make lint-backend`: バックエンドコード品質チェック
      - `make lint-frontend`: フロントエンドコード品質チェック
    - **コードフォーマット:**
      - `make format`: コードフォーマット
      - `make format-backend`: バックエンドコードフォーマット
      - `make format-frontend`: フロントエンドコードフォーマット
    - **データベース管理:**
      - `make db-migrate`: データベースマイグレーション
      - `make db-init`: Alembic初期化
      - `make db-revision`: 新しいマイグレーション作成
      - `make db-status`: データベース状態確認
      - `make db-seed`: テストデータ投入
      - `make db-reset`: データベースリセット
    - **モニタリング:**
      - `make status`: 開発環境状態確認
      - `make logs`: 全サービスログ表示
      - `make logs-backend`: バックエンドログ表示
      - `make logs-frontend`: フロントエンドログ表示
      - `make logs-db`: データベースログ表示
    - **実装済み機能:**
      - pip警告抑制（PIP_ROOT_USER_ACTION=ignore）
      - Alembic自動初期化
      - バックグラウンドサーバー起動
      - 包括的なヘルプシステム
      - 日本語コマンド説明
    - _要件: 全般_

  - [x] 2.3 開発環境設定ファイル
    - .env.example（環境変数テンプレート）
    - .gitignore（Git除外設定）
    - .dockerignore（Docker除外設定）
    - README.md（開発環境セットアップ手順）
    - _要件: 全般_

- [x] 3. WebUI用最小APIとデータモデルの実装
  - [x] 3.1 WebUI用SQLAlchemyモデルの実装
    - InquiryModel、StoryModelクラス
    - InquiryStatus、StoryStatus、Priority、StoryCategoryエnum
    - _要件: 6.1, 9.1_

  - [x] 3.2 データベース接続とマイグレーション
    - Alembicによるマイグレーション設定
    - データベース接続管理
    - Makefileとの統合（make db-migrate, make db-reset）
    - 初期データシード機能
    - _要件: 9.1, 9.3_

  - [x] 3.3 データベーススキーマ整合性の修正
    - story_metadataカラムにserver_default='{}'を追加するマイグレーション作成
    - SQLAlchemyモデルにPythonレベルのdefault=dictを追加
    - story_templates.fieldsとchecklistカラムの設定確認と修正
    - マイグレーション安全性テスト（既存データ保持確認）
    - _要件: 11.1, 11.2, 11.3, 11.4_

  - [x] 3.4 FastAPIアプリケーション初期設定
    - FastAPIアプリケーションインスタンス作成
    - CORSMiddleware設定（フロントエンド連携用）
    - APIRouter設定（/api プレフィックス）
    - lifespan context manager実装（モダンなFastAPI 0.104.0+対応）
    - _要件: 8.1, 8.2_

  - [x] 3.5 問い合わせAPIエンドポイント実装
    - POST /api/inquiries（InquiryCreateRequest → InquiryResponse）
    - GET /api/inquiries（→ List[InquiryResponse]）
    - GET /api/inquiries/{id}（→ InquiryResponse）
    - FastAPI依存性注入によるデータベースセッション管理（get_db）
    - _要件: 1.1, 6.3_

- [ ] 4. React + TypeScriptフロントエンドの実装
  - [ ] 4.1 Reactアプリケーション初期設定
    - Create React App with TypeScript
    - React Router設定（/, /inquiries, /tasks ルート）
    - Axios APIクライアント設定
    - _要件: 8.1, 8.6_

  - [ ] 4.2 InquiryFormコンポーネント実装
    - 問い合わせ入力フォーム（textarea + submit button）
    - 日本語入力対応
    - 送信状態表示（loading, success, error）
    - _要件: 8.2, 8.6, 8.5_

  - [ ] 4.3 InquiryListコンポーネント実装
    - 問い合わせ履歴一覧表示
    - InquiryItemコンポーネント（個別問い合わせ表示）
    - 基本フィルタリング（ステータス別）
    - _要件: 8.4, 6.3_

  - [ ] 4.4 フロントエンドユニットテスト実装
    - InquiryForm.test.tsx（Jest + React Testing Library）
    - InquiryList.test.tsx
    - APIクライアントのモックテスト
    - _要件: 3.2, 8.6_

- [ ] 5. チェックポイント - WebUI基本機能の確認
  - [ ] 5.1 WebUI基本機能テスト確認
    - 問い合わせ入力と履歴表示が動作することを確認し、質問があれば尋ねる

- [ ] 6. ストーリー管理APIとUIコンポーネントの追加
  - [ ] 6.1 ストーリー管理APIエンドポイント実装
    - GET /api/stories（→ List[StoryResponse]）
    - GET /api/stories/{id}（→ StoryResponse）
    - PUT /api/stories/{id}（StoryUpdateRequest → StoryResponse）
    - POST /api/stories/{id}/approve（→ StoryResponse）
    - POST /api/stories/{id}/reject（RejectRequest → StoryResponse）
    - _要件: 3.2, 3.4_

  - [ ] 6.2 StoryReviewコンポーネント実装
    - StoryListコンポーネント（ストーリー一覧表示）
    - StoryDetailコンポーネント（詳細表示・編集）
    - StoryActionButtonsコンポーネント（承認・拒否ボタン）
    - BatchOperationコンポーネント（一括操作）
    - _要件: 8.3, 3.2, 3.6_

  - [ ] 6.3 ストーリー管理のプロパティテスト
    - **プロパティ12: 状態遷移の正確性**
    - **検証: 要件 3.4, 3.5**

- [ ] 7. AI統合とストーリー変換機能の実装
  - [ ] 7.1 StoryConverterクラス実装
    - OpenAI APIクライアント設定
    - convert_to_stories()メソッド（Inquiry → List[Story]）
    - extract_deadlines()メソッド（str → Optional[datetime]）
    - _要件: 1.2, 1.4_

  - [ ] 7.2 ストーリー変換APIエンドポイント実装
    - POST /api/inquiries/{id}/generate-stories（→ StoryGenerationResponse）
    - GET /api/inquiries/{id}/generation-status（→ GenerationStatusResponse）
    - _要件: 1.2, 1.4_

  - [ ] 7.3 ストーリー変換プロパティテスト実装
    - **プロパティ2: ストーリー変換の完全性**
    - **プロパティ3: 複数ストーリー分離**
    - **検証: 要件 1.2, 1.4, 1.3**

  - [ ] 7.4 StoryGenerationコンポーネント実装
    - GenerateStoriesButtonコンポーネント
    - StoryGenerationProgressコンポーネント
    - GeneratedStoriesListコンポーネント
    - _要件: 8.5_

- [ ] 8. チェックポイント - 基本ワークフローの確認
  - [ ] 8.1 基本ワークフロー確認
    - 問い合わせ→ストーリー生成→レビューの基本フローが動作することを確認し、質問があれば尋ねる

- [ ] 9. 完全なデータモデルとサービス層の実装
  - [ ] 9.1 拡張SQLAlchemyモデル実装
    - StoryTemplateModel、UserModel、StoryMetadataModelクラス
    - StoryVersionModel（変更履歴用）、CommentModelクラス
    - _要件: 6.1, 9.1_

  - [ ] 9.2 完全な型定義実装
    - TypeScript: StoryTemplate、User、StoryMetadata、StoryVersion、Comment型
    - Python: 全サービスクラスのインターフェース（Protocol）
    - Pydantic: 全Request/Responseモデル
    - _要件: 全般_

  - [ ] 9.3 データモデルプロパティテスト実装
    - **プロパティ1: 問い合わせ受付と保存**
    - **プロパティ9: ストーリー初期状態**
    - **プロパティ31: データベーススキーマの整合性**
    - **検証: 要件 1.1, 6.1, 9.1, 3.1, 11.1, 11.2, 11.3, 11.4**

  - [ ] 9.4 InquiryServiceクラス実装
    - submit_inquiry()、get_inquiry_history()、update_inquiry_status()メソッド
    - check_task_completion()、request_clarification()メソッド
    - _要件: 1.1, 1.5_

  - [ ] 9.5 問い合わせ処理プロパティテスト実装
    - **プロパティ4: 日本語サポート**
    - **プロパティ30: 問い合わせステータス管理**
    - **検証: 要件 1.5, 1.1, 3.4**

- [ ] 10. 高度なストーリー管理機能の実装
  - [ ] 10.1 StoryServiceクラスの実装
    - ストーリーのCRUD操作
    - レビュー機能（承認・拒否）
    - _要件: 3.1, 3.4, 3.5_

  - [ ] 10.2 ストーリーレビューのプロパティテスト
    - **プロパティ13: 一括処理の原子性**
    - **検証: 要件 3.6**

  - [ ] 10.3 変更履歴とコメント機能
    - ストーリーの変更履歴管理
    - コメント・メモ機能
    - _要件: 3.3, 6.4, 6.5_

  - [ ] 10.4 履歴管理のプロパティテスト
    - **プロパティ11: 変更履歴保持**
    - **プロパティ19: コメント機能**
    - **検証: 要件 3.3, 6.4, 6.5**

- [ ] 11. 期限抽出と自動分類機能
  - [ ] 11.1 期限抽出と自動分類機能
    - 自然言語からの期限抽出
    - カテゴリと優先度の自動割り当て
    - _要件: 2.1, 2.2, 10.2_

  - [ ] 11.2 自動分類のプロパティテスト
    - **プロパティ5: 自動分類の一貫性**
    - **プロパティ6: 緊急キーワード検出**
    - **プロパティ27: 期限自動設定**
    - **検証: 要件 2.1, 2.2, 2.3, 10.2**

- [ ] 12. パターン認識とテンプレート機能の実装
  - [ ] 12.1 PatternRecognizerクラスの実装
    - ストーリーパターンの識別
    - テンプレートの適用
    - _要件: 5.1, 5.2_

  - [ ] 12.2 パターン認識のプロパティテスト
    - **プロパティ16: パターン認識とテンプレート適用**
    - **検証: 要件 5.1, 5.2, 5.4**

  - [ ] 12.3 カスタムテンプレート管理
    - ユーザー定義テンプレートの保存・取得
    - テンプレートの検証
    - _要件: 5.3, 5.4_

  - [ ] 12.4 テンプレート管理のプロパティテスト
    - **プロパティ17: カスタムテンプレート管理**
    - **検証: 要件 5.3**

- [ ] 13. 検索機能とリアルタイム更新
  - [ ] 13.1 バックエンド検索APIの実装
    - 問い合わせとストーリーの検索
    - フィルタリング機能
    - _要件: 8.4_

  - [ ] 13.2 フロントエンド検索コンポーネント
    - 検索UI（TypeScript/React）
    - 検索結果の表示
    - _要件: 8.4_

  - [ ] 13.3 検索機能のプロパティテスト
    - **プロパティ22: 検索機能**
    - **検証: 要件 8.4**

  - [ ] 13.4 リアルタイム進捗表示
    - WebSocketまたはSSEによる進捗更新
    - フロントエンドでの進捗状況表示
    - _要件: 8.5_

  - [ ] 13.5 進捗表示のプロパティテスト
    - **プロパティ23: 進捗状況更新**
    - **検証: 要件 8.5**

- [ ] 14. 外部システム統合とエクスポート機能
  - [ ] 14.1 ExportServiceクラスの実装
    - カンバンシステムへの出力機能
    - 複数フォーマット対応（JSON、CSV）
    - _要件: 4.1, 4.2_

  - [ ] 14.2 エクスポート機能のプロパティテスト
    - **プロパティ14: 出力データ完全性**
    - **プロパティ15: 外部システム統合**
    - **検証: 要件 4.2, 10.3, 4.3, 4.4, 4.5**

  - [ ] 14.3 外部API統合（Trello、Jira等）
    - 外部システムとのAPI連携
    - 認証とエラーハンドリング
    - _要件: 4.3, 4.4_

  - [ ] 14.4 同期状態追跡のプロパティテスト
    - **プロパティ26: 同期状態追跡**
    - **検証: 要件 9.5**

- [ ] 15. 通知システムの実装
  - [ ] 15.1 NotificationServiceクラスの実装
    - 各種通知の送信機能
    - 複数チャネル対応
    - _要件: 7.1, 7.2, 7.3_

  - [ ] 15.2 通知機能のプロパティテスト
    - **プロパティ20: 通知配信**
    - **プロパティ21: 通知設定適用**
    - **プロパティ28: 期限通知**
    - **検証: 要件 7.1, 7.2, 7.3, 7.4, 7.5, 10.4**

  - [ ] 15.3 期限管理と優先度調整
    - 期限による通知機能
    - 優先度の自動調整
    - _要件: 10.4, 10.5_

  - [ ] 15.4 期限管理のプロパティテスト
    - **プロパティ29: 期限による優先度調整**
    - **検証: 要件 10.5**

- [ ] 16. データ永続化とバックアップ機能
  - [ ] 16.1 データ復元機能の実装
    - システム再起動時のデータ復元
    - データ整合性チェック
    - _要件: 9.3_

  - [ ] 16.2 データ復元のプロパティテスト
    - **プロパティ24: データ復元**
    - **検証: 要件 9.3**

  - [ ] 16.3 自動バックアップ機能
    - 定期的なデータバックアップ
    - バックアップ状態の監視
    - _要件: 9.4_

  - [ ] 16.4 バックアップ機能のプロパティテスト
    - **プロパティ25: バックアップ実行**
    - **検証: 要件 9.4**

- [ ] 17. エラーハンドリングとログ記録
  - [ ] 17.1 包括的エラーハンドリング
    - 各種エラーの適切な処理
    - ユーザーフレンドリーなエラーメッセージ
    - _要件: 1.4, 7.2_

  - [ ] 17.2 ログ記録システム
    - ストーリー生成プロセスのログ
    - システム操作ログ
    - _要件: 6.2_

  - [ ] 17.3 ログ記録のプロパティテスト
    - **プロパティ18: 生成ログ記録**
    - **検証: 要件 6.2, 6.3**

- [ ] 18. 統合テストとデプロイメント準備
  - [ ] 18.1 エンドツーエンド統合テスト
    - 完全なワークフローのテスト（Python + TypeScript）
    - 外部システム統合のテスト
    - Docker環境でのテスト実行
    - _要件: 全般_

  - [ ] 18.2 パフォーマンステストと最適化
    - バックエンドレスポンス時間の測定
    - フロントエンドレンダリング最適化
    - データベースクエリの最適化
    - _要件: 全般_

  - [ ] 18.3 本番環境用Docker設定
    - docker-compose.prod.yml（本番用設定）
    - Nginx リバースプロキシ設定
    - SSL/TLS証明書設定
    - 環境変数の本番用設定
    - ヘルスチェック設定
    - _要件: 全般_

  - [ ] 18.4 CI/CDパイプライン設定
    - GitHub Actions または GitLab CI設定
    - 自動テスト実行
    - 自動デプロイメント
    - セキュリティスキャン
    - _要件: 全般_

- [ ] 19. 最終チェックポイント - 全機能の確認
  - [ ] 19.1 全機能テスト確認
    - すべてのテストが通ることを確認し、質問があれば尋ねる

## 注意事項

- **WebUI優先実装**: 使い心地を早期確認するため、最小限のAPIとWebUIを先行実装
- **段階的な機能拡張**: 基本的なワークフロー確認後、段階的にバックエンド機能を拡張
- 各タスクは特定の要件への参照を含む
- チェックポイントで段階的な検証を実施
- プロパティテストは普遍的な正確性プロパティを検証
- ユニットテストは特定の例とエッジケースを検証
- バックエンドはPython（FastAPI + SQLAlchemy）、フロントエンドはTypeScript（React）で実装
- Docker Composeによる統合開発環境を提供
- Makefileによる開発タスクの自動化（テスト、リント、データベース操作等）
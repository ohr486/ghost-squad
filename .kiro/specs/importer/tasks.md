# Implementation Plan

## タスク一覧

### 1. プラグインアーキテクチャ基盤の実装

- [x] 1.1 (P) データソースプラグイン共通インターフェースの実装
  - RawImportDataデータクラスの定義（source_id、source_type、content、subject、sender、received_at、raw_metadata）
  - DataSourcePluginの抽象基底クラスの定義（plugin_type、validate_config、connect、disconnect、fetch、mark_as_processed）
  - ValidationResultデータクラスの定義
  - 型パラメータによる設定型の安全性確保
  - ユニットテスト作成
  - _Requirements: 1.4_

- [x] 1.2 PluginRegistryサービスの実装
  - プラグイン登録・解除機能の実装（register、unregister）
  - プラグイン有効/無効切り替え機能の実装（enable、disable）
  - 設定情報検証機能の実装（登録時にvalidate_config呼び出し）
  - 初期化失敗時のエラーログ記録と自動無効化
  - PluginStatusデータクラスの定義（plugin_type、enabled、initialized、error_message）
  - プラグイン取得・一覧機能の実装（get_plugin、list_plugins）
  - 同一plugin_typeの重複登録防止
  - ユニットテスト作成
  - _Requirements: 1.1, 1.2, 1.3, 1.5_

### 2. AIプロバイダーアーキテクチャ基盤の実装

- [x] 2.1 (P) AIプロバイダー共通インターフェースの実装
  - AIProviderType列挙型の定義（OPENAI、ANTHROPIC）
  - AIProviderConfig基底データクラスの定義（api_key、model、temperature、max_tokens、timeout、retry_max、retry_backoff_base）
  - AIAnalysisRequestデータクラスの定義（content、subject、sender、source_type、additional_context）
  - AIAnalysisResponseデータクラスの定義（title、content、priority、category、confidence_score、raw_response、provider_type、model）
  - AIProvider抽象基底クラスの定義（provider_type、supported_models、validate_config、initialize、analyze、health_check）
  - ユニットテスト作成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 2.2 AIProviderRegistryサービスの実装
  - プロバイダー登録・解除機能の実装（register、unregister）
  - デフォルトプロバイダー設定機能の実装（set_default）
  - プロバイダー取得機能の実装（get_provider、引数未指定時はデフォルト返却）
  - 一覧機能の実装（list_providers）
  - AIProviderStatusデータクラスの定義（provider_type、enabled、initialized、is_default、model、error_message）
  - デフォルトプロバイダーは1つのみの制約
  - ユニットテスト作成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

### 3. メールプラグインの実装

- [x] 3.1 EmailPluginConfigと設定検証の実装
  - EmailPluginConfigデータクラスの定義（imap_server、imap_port、username、password、folder、use_ssl、fetch_limit、retry_max、retry_backoff_base）
  - 設定検証ロジックの実装（必須フィールド、ポート範囲、フォルダ名形式）
  - ユニットテスト作成
  - _Requirements: 2.1, 2.3_

- [x] 3.2 EmailPluginのIMAP接続機能の実装
  - IMAP4_SSLによるメールサーバー接続の実装（connect）
  - 接続切断の実装（disconnect）
  - 指数バックオフによるリトライ戦略の実装（最大3回、2^n秒）
  - 接続失敗時のエラーハンドリングとエラー通知
  - タイムアウト設定（30秒）
  - ユニットテスト作成（モックIMAPサーバー使用）
  - _Requirements: 2.1, 2.5_

- [x] 3.3 EmailPluginのメール取得・解析機能の実装
  - 指定フォルダからの未読メール取得の実装（fetch）
  - メール本文・件名・送信者情報の抽出
  - Message-IDをsource_idとして使用
  - RawImportDataへの変換処理
  - fetch_limit件数制限の適用
  - フォルダフィルタリング機能の実装
  - 取り込み進捗状況の記録
  - メール既読マーク処理の実装（mark_as_processed）
  - ユニットテスト作成
  - _Requirements: 2.2, 2.3, 2.4, 2.6_

### 4. OpenAIプロバイダーの実装

- [x] 4.1 OpenAIProviderConfigと設定検証の実装
  - OpenAIProviderConfigデータクラスの定義（AIProviderConfig継承、organization）
  - サポートモデル一覧の定義（gpt-4、gpt-4-turbo、gpt-4o、gpt-3.5-turbo）
  - API Key形式検証の実装
  - モデル名検証の実装
  - ユニットテスト作成
  - _Requirements: 3.1, 3.6_

- [x] 4.2 OpenAIProviderの解析機能の実装
  - OpenAIクライアント初期化の実装（initialize）
  - 問い合わせ解析プロンプトの構築（日本語対応）
  - AI解析リクエストの実行（analyze）
  - レスポンス解析とAIAnalysisResponseへの変換
  - カテゴリ判定、優先度推定、タイトル生成、本文構造化
  - 信頼度スコアの算出
  - 指数バックオフによるリトライ戦略の実装
  - ヘルスチェック機能の実装（health_check）
  - ユニットテスト作成（OpenAI APIモック使用）
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

### 5. Anthropicプロバイダーの実装

- [ ] 5.1 (P) AnthropicProviderConfigと設定検証の実装
  - AnthropicProviderConfigデータクラスの定義（AIProviderConfig継承）
  - サポートモデル一覧の定義（claude-3-opus、claude-3-sonnet、claude-3-haiku、claude-3-5-sonnet）
  - API Key形式検証の実装
  - モデル名検証の実装
  - ユニットテスト作成
  - _Requirements: 3.1, 3.6_

- [ ] 5.2 (P) AnthropicProviderの解析機能の実装
  - Anthropicクライアント初期化の実装（initialize）
  - 問い合わせ解析プロンプトの構築（日本語対応、OpenAIProviderと共通化）
  - AI解析リクエストの実行（analyze）
  - レスポンス解析とAIAnalysisResponseへの変換
  - カテゴリ判定、優先度推定、タイトル生成、本文構造化
  - 信頼度スコアの算出
  - 指数バックオフによるリトライ戦略の実装
  - ヘルスチェック機能の実装（health_check）
  - ユニットテスト作成（Anthropic APIモック使用）
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

### 6. Analysis Serviceの実装

- [ ] 6.1 ImporterAnalysisServiceの実装
  - AIProviderRegistryとの統合
  - 解析用プロンプトの構築（全プロバイダー共通、日本語対応）
  - プロバイダー選択機能（引数指定またはデフォルト使用）
  - AIレスポンスからAnalysisResultへの変換
  - 信頼度に基づくneeds_reviewフラグ判定（閾値0.8）
  - AnalysisResultデータクラスの定義（title、content、priority、category、confidence_score、needs_review、provider_type、model、analysis_metadata）
  - ユニットテスト作成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

### 7. エラーログ永続化の実装

- [ ] 7.1 (P) ImportErrorLogモデルとマイグレーションの実装
  - ImportErrorLogモデルの定義（id、error_code、plugin_type、source_id、error_message、occurred_at、resolved）
  - インデックスの定義（error_code + occurred_at、plugin_type）
  - Alembicマイグレーションファイルの作成
  - ユニットテスト作成
  - _Requirements: 5.1, 5.4_

- [ ] 7.2 (P) ImportErrorLogRepositoryの実装
  - エラーログ作成機能の実装
  - 解決済みマーク機能の実装（resolved = true）
  - エラー統計取得機能の実装（error_code別集計）
  - ユニットテスト作成
  - _Requirements: 5.1, 5.4_

### 8. 重複チェック用インデックスの追加

- [ ] 8.1 (P) inquiry_metadataへのGINインデックス追加
  - Alembicマイグレーションファイルの作成
  - inquiry_metadata->'importer'へのGINインデックス追加
  - 重複チェッククエリの最適化確認
  - _Requirements: 4.5_

### 9. Importer Serviceの実装

- [ ] 9.1 ImporterMetadataとImportResultの定義
  - ImporterMetadataデータクラスの定義（source_type、source_id、imported_at、confidence_score、needs_review、original_subject、original_sender、ai_provider、ai_model）
  - ImportResultデータクラスの定義（total_fetched、total_imported、total_skipped、total_failed、imported_inquiry_ids、errors）
  - ErrorStatsデータクラスの定義（error_code、count、last_occurred）
  - ユニットテスト作成
  - _Requirements: 4.2, 5.4_

- [ ] 9.2 ImporterServiceのインポート実行機能の実装
  - PluginRegistryからプラグイン取得
  - プラグインによるデータ取得
  - 重複チェック機能の実装（inquiry_metadata内のsource_type + source_idで検索）
  - AIプロバイダー指定オプションの対応
  - AnalysisServiceによるAI解析
  - InquiryRepositoryを使用した問い合わせ作成
  - ステータス「received」での登録
  - インポート元メタデータ（ImporterMetadata）の付与
  - インポート結果の集計と返却
  - ユニットテスト作成
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [ ] 9.3 ImporterServiceのエラーハンドリング機能の実装
  - エラーログ出力（structlog使用）
  - ImportErrorLogへのエラー記録
  - 生成失敗時の手動対応用キューへの追加（error_logsに未解決として記録）
  - 連続エラー検出とアラートログ出力
  - 指数バックオフによるリトライ処理
  - エラー統計取得機能の実装（get_error_stats）
  - ユニットテスト作成
  - _Requirements: 4.4, 5.1, 5.3, 5.4, 5.5_

- [ ] 9.4 ImporterServiceのリトライ機能の実装
  - 失敗したインポートのリトライ処理（retry_failed）
  - source_idsリストによる対象指定
  - AIプロバイダー切り替えオプション
  - リトライ成功時のエラーログ解決済みマーク
  - ユニットテスト作成
  - _Requirements: 5.2_

### 10. Importer APIエンドポイントの実装

- [ ] 10.1 プラグイン管理APIの実装
  - GET /api/plugins - プラグイン一覧取得
  - POST /api/plugins/{type}/enable - プラグイン有効化
  - POST /api/plugins/{type}/disable - プラグイン無効化
  - Pydanticスキーマの定義（PluginStatusResponse）
  - エラーレスポンスの実装（GS-301、GS-302）
  - ユニットテスト作成
  - _Requirements: 1.1, 1.2_

- [ ] 10.2 AIプロバイダー管理APIの実装
  - GET /api/ai-providers - プロバイダー一覧取得
  - POST /api/ai-providers/{type}/set-default - デフォルト設定
  - Pydanticスキーマの定義（AIProviderStatusResponse）
  - エラーレスポンスの実装（GS-308、GS-309）
  - ユニットテスト作成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 10.3 インポート実行APIの実装
  - POST /api/importers/execute - インポート実行
  - POST /api/importers/retry - リトライ実行
  - Pydanticスキーマの定義（ExecuteImportRequest、RetryImportRequest、ImportResultResponse）
  - AIプロバイダー選択オプションの対応
  - エラーレスポンスの実装（GS-303、GS-304、GS-305、GS-306、GS-307）
  - ユニットテスト作成
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5, 5.2_

- [ ] 10.4 エラー統計APIの実装
  - GET /api/importers/stats - エラー統計取得
  - Pydanticスキーマの定義（ErrorStatsResponse）
  - ユニットテスト作成
  - _Requirements: 5.4_

### 11. 設定ファイル管理の実装

- [ ] 11.1 (P) YAML設定ファイルローダーの実装
  - importer_config.yaml設定ファイルスキーマの定義
  - 環境変数展開機能の実装（${IMAP_SERVER}等）
  - プラグイン設定の読み込み
  - AIプロバイダー設定の読み込み
  - デフォルトプロバイダー設定の読み込み
  - アプリケーション起動時のレジストリ初期化
  - ユニットテスト作成
  - _Requirements: 1.1, 1.2, 1.3, 3.1_

### 12. フロントエンドAPIクライアントの実装

- [ ] 12.1 (P) ImporterAPIサービスの実装
  - TypeScript型定義の作成（PluginStatus、AIProviderStatus、ExecuteImportRequest、RetryImportRequest、ImportResult、ErrorStats）
  - プラグイン管理API呼び出し（listPlugins、enablePlugin、disablePlugin）
  - AIプロバイダー管理API呼び出し（listAIProviders、setDefaultAIProvider）
  - インポート実行API呼び出し（executeImport、retryImport）
  - エラー統計API呼び出し（getErrorStats）
  - Axiosインスタンス設定
  - エラーハンドリングインターセプター
  - ユニットテスト作成
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 5.2, 5.4_

### 13. フロントエンドコンポーネントの実装

- [ ] 13.1 PluginListComponentの実装
  - プラグイン一覧テーブルの表示
  - プラグインタイプ、状態（初期化状態）、エラーメッセージの表示
  - 有効/無効トグルスイッチの実装
  - TanStack React Queryによるサーバー状態管理
  - ローディング・エラー状態の表示
  - ユニットテスト作成
  - _Requirements: 1.1, 1.2_

- [ ] 13.2 (P) AIProviderListComponentの実装
  - プロバイダー一覧テーブルの表示
  - プロバイダータイプ、モデル、状態、エラーメッセージの表示
  - デフォルト選択ラジオボタンの実装
  - TanStack React Queryによるサーバー状態管理
  - ローディング・エラー状態の表示
  - ユニットテスト作成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 13.3 ImportExecutorComponentの実装
  - データソースプラグイン選択ドロップダウン
  - AIプロバイダー選択ドロップダウン（オプション、デフォルト使用可）
  - インポート実行ボタン
  - 実行中ローディング表示
  - 実行結果の表示（取得件数、インポート成功、スキップ、失敗）
  - エラー詳細の展開表示
  - TanStack React Queryによるmutation管理
  - ユニットテスト作成
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 13.4 (P) ErrorStatsComponentの実装
  - エラー統計テーブルの表示
  - エラーコード、発生回数、最終発生日時の表示
  - エラーなし時のメッセージ表示
  - TanStack React Queryによるサーバー状態管理
  - 自動更新機能
  - ユニットテスト作成
  - _Requirements: 5.4_

- [ ] 13.5 ImporterPageの実装
  - 各子コンポーネントの統合（ImportExecutor、PluginList、AIProviderList、ErrorStats）
  - セクションベースのレイアウト
  - 見出しとナビゲーション
  - レスポンシブデザイン対応
  - ユニットテスト作成
  - _Requirements: MVP UI_

### 14. 統合テストの実装

- [ ] 14.1 バックエンド統合テストの実装
  - EmailPlugin + IMAPサーバーモックによる統合テスト
  - OpenAIProvider + OpenAI APIモックによる統合テスト
  - AnthropicProvider + Anthropic APIモックによる統合テスト
  - AnalysisService + AIProviderモックによる統合テスト
  - ImporterService + InquiryRepositoryによる統合テスト
  - 完全なインポートフロー（メール取得→解析→問い合わせ作成）
  - AIプロバイダー切り替えフロー
  - エラーハンドリングフロー（接続失敗→リトライ→成功）
  - 重複検出フロー
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 14.2 フロントエンド統合テストの実装
  - ImporterPage + MSW（Mock Service Worker）によるAPI統合テスト
  - インポート実行フロー（UI操作→API→結果確認）
  - プラグイン有効/無効切り替えフロー
  - AIプロバイダーデフォルト設定フロー
  - エラー発生時のUI状態遷移
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 4.1, 5.4_

## Requirements Coverage

| Requirement ID | Summary | Tasks |
|----------------|---------|-------|
| 1.1 | プラグイン登録・解除 | 1.2, 10.1, 11.1, 12.1, 13.1, 14.1, 14.2 |
| 1.2 | 有効/無効切り替え | 1.2, 10.1, 11.1, 12.1, 13.1, 14.1, 14.2 |
| 1.3 | 設定情報検証 | 1.2, 11.1, 14.1 |
| 1.4 | 共通インターフェース | 1.1, 14.1 |
| 1.5 | 初期化失敗処理 | 1.2, 14.1 |
| 2.1 | IMAP/POP3接続 | 3.2, 10.3, 12.1, 13.3, 14.1, 14.2 |
| 2.2 | メール情報取得 | 3.3, 10.3, 12.1, 13.3, 14.1, 14.2 |
| 2.3 | フォルダフィルタリング | 3.1, 3.3, 10.3, 12.1, 13.3, 14.1 |
| 2.4 | 進捗状況記録 | 3.3, 10.3, 12.1, 13.3, 14.1 |
| 2.5 | リトライ処理 | 3.2, 10.3, 12.1, 13.3, 14.1 |
| 2.6 | 重複取り込み防止 | 3.3, 10.3, 12.1, 13.3, 14.1 |
| 3.1 | カテゴリ判定 | 2.1, 2.2, 4.2, 5.2, 6.1, 10.2, 11.1, 12.1, 13.2, 14.1, 14.2 |
| 3.2 | 優先度推定 | 2.1, 2.2, 4.2, 5.2, 6.1, 10.2, 12.1, 13.2, 14.1 |
| 3.3 | タイトル生成 | 2.1, 2.2, 4.2, 5.2, 6.1, 10.2, 12.1, 13.2, 14.1 |
| 3.4 | 本文構造化 | 2.1, 2.2, 4.2, 5.2, 6.1, 10.2, 12.1, 13.2, 14.1 |
| 3.5 | 信頼度フラグ | 2.1, 2.2, 4.2, 5.2, 6.1, 10.2, 12.1, 13.2, 14.1 |
| 3.6 | 日本語解析 | 2.1, 2.2, 4.1, 4.2, 5.1, 5.2, 6.1, 10.2, 12.1, 13.2, 14.1 |
| 4.1 | Inquiry API使用 | 9.2, 10.3, 12.1, 13.3, 14.1, 14.2 |
| 4.2 | メタデータ付与 | 9.1, 9.2, 10.3, 12.1, 13.3, 14.1 |
| 4.3 | ステータス登録 | 9.2, 10.3, 12.1, 13.3, 14.1 |
| 4.4 | 生成失敗処理 | 9.3, 10.3, 12.1, 13.3, 14.1 |
| 4.5 | 重複防止 | 8.1, 9.2, 10.3, 12.1, 13.3, 14.1 |
| 5.1 | エラーログ出力 | 7.1, 7.2, 9.3, 14.1 |
| 5.2 | 手動リトライ | 9.4, 10.3, 12.1, 14.1 |
| 5.3 | 連続エラーアラート | 9.3, 14.1 |
| 5.4 | エラー統計 | 7.1, 7.2, 9.1, 9.3, 10.4, 12.1, 13.4, 14.1, 14.2 |
| 5.5 | 指数バックオフ | 9.3, 14.1 |

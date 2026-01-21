/**
 * Importer機能の型定義
 *
 * バックエンドPydanticスキーマ（models/schemas/importer.py）との整合性を保証
 * 要件: 1.1, 1.2, 2.1-2.6, 3.1-3.6, 4.1-4.5, 5.2, 5.4
 */

// =============================================================================
// プラグイン管理型（要件1.1, 1.2）
// =============================================================================

/**
 * プラグインステータス
 */
export interface PluginStatus {
  /** プラグイン種別（例: email, sentry） */
  plugin_type: string;
  /** プラグインが有効かどうか */
  enabled: boolean;
  /** プラグインが正常に初期化されたかどうか */
  initialized: boolean;
  /** 初期化失敗時のエラーメッセージ */
  error_message?: string | null;
}

/**
 * プラグイン一覧レスポンス
 */
export interface PluginListResponse {
  /** プラグインステータスリスト */
  data: PluginStatus[];
  /** レスポンスタイムスタンプ（ISO 8601形式） */
  timestamp: string;
}

// =============================================================================
// AIプロバイダー管理型（要件3.1-3.6）
// =============================================================================

/**
 * AIプロバイダーステータス
 */
export interface AIProviderStatus {
  /** プロバイダー種別（例: openai, anthropic） */
  provider_type: string;
  /** プロバイダーが有効かどうか */
  enabled: boolean;
  /** プロバイダーが正常に初期化されたかどうか */
  initialized: boolean;
  /** デフォルトプロバイダーかどうか */
  is_default: boolean;
  /** 使用しているモデル名 */
  model: string;
  /** 初期化失敗時のエラーメッセージ */
  error_message?: string | null;
}

/**
 * AIプロバイダー一覧レスポンス
 */
export interface AIProviderListResponse {
  /** プロバイダーステータスリスト */
  data: AIProviderStatus[];
  /** レスポンスタイムスタンプ（ISO 8601形式） */
  timestamp: string;
}

// =============================================================================
// インポート実行型（要件2.1-2.6, 4.1-4.5, 5.2）
// =============================================================================

/**
 * インポート実行リクエスト
 */
export interface ExecuteImportRequest {
  /** データソースプラグイン種別（例: email） */
  plugin_type: string;
  /** AIプロバイダー種別（例: openai, anthropic）。未指定時はデフォルト使用 */
  ai_provider_type?: string | null;
}

/**
 * インポートリトライリクエスト
 */
export interface RetryImportRequest {
  /** データソースプラグイン種別（例: email） */
  plugin_type: string;
  /** リトライ対象のソースIDリスト */
  source_ids: string[];
  /** AIプロバイダー種別（例: openai, anthropic）。未指定時はデフォルト使用 */
  ai_provider_type?: string | null;
}

/**
 * インポートエラー情報
 */
export interface ImportError {
  /** エラーが発生したソースID */
  source_id: string;
  /** エラーコード（GS-3xx形式） */
  error_code: string;
  /** エラーメッセージ（日本語） */
  error_message: string;
}

/**
 * インポート結果レスポンス
 */
export interface ImportResult {
  /** 取得件数 */
  total_fetched: number;
  /** インポート成功件数 */
  total_imported: number;
  /** スキップ件数（重複等） */
  total_skipped: number;
  /** 失敗件数 */
  total_failed: number;
  /** インポートされた問い合わせIDリスト */
  imported_inquiry_ids: number[];
  /** エラー情報リスト */
  errors: ImportError[];
  /** レスポンスタイムスタンプ（ISO 8601形式） */
  timestamp: string;
}

// =============================================================================
// エラー統計型（要件5.4）
// =============================================================================

/**
 * エラー統計
 */
export interface ErrorStats {
  /** エラーコード（GS-3xx形式） */
  error_code: string;
  /** エラー発生回数 */
  count: number;
  /** 最終発生日時（ISO 8601形式） */
  last_occurred: string;
}

/**
 * エラー統計一覧レスポンス
 */
export interface ErrorStatsListResponse {
  /** エラー統計リスト */
  data: ErrorStats[];
  /** レスポンスタイムスタンプ（ISO 8601形式） */
  timestamp: string;
}

// =============================================================================
// 共通エラー型
// =============================================================================

/**
 * バリデーションエラー詳細
 */
export interface ImporterValidationError {
  /** エラーコード（GS-xxx形式） */
  code: string;
  /** エラーメッセージ（日本語） */
  message: string;
  /** エラーが発生したフィールド名 */
  field?: string | null;
}

/**
 * Importerエラーレスポンス
 */
export interface ImporterErrorResponse {
  /** エラー詳細リスト */
  errors: ImporterValidationError[];
  /** エラー発生タイムスタンプ */
  timestamp: string;
}

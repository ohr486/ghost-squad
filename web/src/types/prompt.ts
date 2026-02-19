/**
 * プロンプト管理機能 - TypeScript型定義
 *
 * バックエンドPydanticスキーマ（models/schemas/prompt.py）との整合性を保証
 * 要件: 1.1, 1.2, 2.2, 2.5, 3.1, 3.2, 3.4, 4.4, 4.5
 */

// =============================================================================
// カテゴリ型（要件1.4）
// =============================================================================

/**
 * プロンプトカテゴリ
 */
export type PromptCategory =
  | "story_generation" // ストーリー生成
  | "import_analysis" // インポート解析
  | "general"; // 汎用

// =============================================================================
// レスポンス型（要件1.1, 1.2, 4.5）
// =============================================================================

/**
 * プロンプトレスポンス
 * プロンプトの詳細情報
 */
export interface PromptResponse {
  /** プロンプトID */
  id: number;
  /** プロンプトキー（一意識別子） */
  key: string;
  /** 表示名 */
  name: string;
  /** 説明 */
  description: string | null;
  /** カテゴリ */
  category: PromptCategory;
  /** 現在のプロンプト本文 */
  content: string;
  /** デフォルトプロンプト本文 */
  default_content: string;
  /** プレースホルダー変数リスト */
  variables: string[];
  /** デフォルトから変更されているか */
  is_modified: boolean;
  /** 編集中ユーザーID */
  editing_by: string | null;
  /** 編集開始日時（ISO 8601形式） */
  editing_since: string | null;
  /** 作成日時（ISO 8601形式） */
  created_at: string;
  /** 更新日時（ISO 8601形式） */
  updated_at: string;
}

/**
 * プロンプト一覧レスポンス
 */
export interface PromptListResponse {
  /** プロンプトリスト */
  data: PromptResponse[];
  /** 総件数 */
  total: number;
}

// =============================================================================
// リクエスト型（要件2.2, 2.5, 3.1, 3.2）
// =============================================================================

/**
 * プロンプト更新リクエスト
 */
export interface UpdatePromptRequest {
  /** プロンプト本文（必須、空文字不可） */
  content: string;
  /** 説明（オプション） */
  description?: string;
}

/**
 * テスト実行リクエスト
 */
export interface TestPromptRequest {
  /** テスト対象のプロンプト本文 */
  content: string;
  /** プレースホルダー変数の値 */
  variables: Record<string, string>;
  /** AIプロバイダー（"openai" | "anthropic"、未指定時はデフォルト） */
  provider?: string;
}

/**
 * テスト実行結果
 */
export interface TestPromptResult {
  /** AI出力結果 */
  output: string;
  /** 使用プロバイダー */
  provider: string;
  /** 使用モデル */
  model: string;
  /** 実行時間（ミリ秒） */
  elapsed_ms: number;
}

/**
 * 編集ロック取得リクエスト
 */
export interface AcquireLockRequest {
  /** 編集者ID */
  user_id: string;
}

/**
 * 編集ロックレスポンス
 */
export interface LockResponse {
  /** ロック取得成功フラグ */
  acquired: boolean;
  /** ロック保持者 */
  locked_by: string | null;
  /** ロック開始日時（ISO 8601形式） */
  locked_since: string | null;
}

// =============================================================================
// 共通エラー型（既存ErrorResponseを再利用）
// =============================================================================

/**
 * プロンプト管理用バリデーションエラー
 */
export interface PromptValidationError {
  /** エラーコード（GS-4xx形式） */
  code: string;
  /** エラーメッセージ（日本語） */
  message: string;
  /** エラーが発生したフィールド名 */
  field?: string | null;
}

/**
 * プロンプト管理エラーレスポンス
 */
export interface PromptErrorResponse {
  /** エラー詳細リスト */
  errors: PromptValidationError[];
  /** エラー発生タイムスタンプ */
  timestamp: string;
}

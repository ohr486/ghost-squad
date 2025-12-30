/**
 * 問い合わせ管理機能 - TypeScript型定義
 *
 * バックエンドスキーマと完全に一致する型定義
 * 要件: 1.1, 1.2, 1.6, 2.4, 3.6, 3.7, 3.12
 */

/**
 * 問い合わせステータス列挙型
 */
export type InquiryStatus =
  | "received" // 受付済み
  | "processing" // AI処理中
  | "needs_clarification" // 明確化要求
  | "task_working" // タスク作業中
  | "completed" // 完了
  | "rejected" // 却下済み
  | "failed"; // 失敗

/**
 * 優先度列挙型
 */
export type Priority =
  | "low" // 低
  | "medium" // 中
  | "high" // 高
  | "urgent"; // 緊急

/**
 * ストーリーカテゴリ列挙型
 */
export type StoryCategory =
  | "development" // 開発
  | "testing" // テスト
  | "documentation" // ドキュメント
  | "research" // 調査
  | "maintenance" // メンテナンス
  | "custom"; // カスタム

/**
 * ステータス変更履歴エントリ
 */
export interface StatusHistoryEntry {
  from_status: InquiryStatus;
  to_status: InquiryStatus;
  changed_at: string; // ISO 8601形式
  changed_by?: string; // 変更者（将来実装）
}

/**
 * 却下情報
 */
export interface RejectionInfo {
  reason?: string; // 却下理由
  rejected_at: string; // 却下日時（ISO 8601）
  rejected_by?: string; // 却下者（将来実装）
}

/**
 * 問い合わせメタデータ構造
 */
export interface InquiryMetadata {
  // 却下情報（要件3.6-3.7）
  rejection?: RejectionInfo;

  // ステータス変更履歴（要件3.12）
  status_history?: StatusHistoryEntry[];

  // その他のメタデータ
  source?: string; // 送信元詳細情報
  tags?: string[]; // タグ（将来実装）
}

/**
 * 問い合わせレスポンス型
 * バックエンドAPIから返される問い合わせデータ
 */
export interface InquiryResponse {
  id: number;
  user_id: string;
  content: string;
  source_system: string;
  timestamp: string; // ISO 8601形式
  status: InquiryStatus;
  created_at: string; // ISO 8601形式
  updated_at: string; // ISO 8601形式
  inquiry_metadata?: InquiryMetadata;
}

/**
 * 問い合わせ作成リクエスト型
 */
export interface CreateInquiryRequest {
  user_id: string;
  content: string;
  source_system: string; // 送信元システム (例: "manual", "email", "chat")
}

/**
 * 問い合わせ更新リクエスト型
 */
export interface UpdateInquiryRequest {
  content?: string;
  source_system?: string;
}

/**
 * ページネーションメタデータ
 */
export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  has_next: boolean;
}

/**
 * ページネーションレスポンス型
 */
export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
  timestamp: string; // ISO 8601形式
}

/**
 * バリデーションエラー型
 */
export interface ValidationError {
  field: string;
  message: string;
  code: string; // GS-xxx形式
}

/**
 * エラーレスポンス型
 */
export interface ErrorResponse {
  errors: Array<{
    code: string; // GS-xxx形式
    message: string; // 日本語メッセージ
    field?: string; // バリデーションエラー時のフィールド名
  }>;
  timestamp: string; // ISO 8601形式
}

/**
 * 問い合わせ却下リクエスト型
 */
export interface RejectInquiryRequest {
  reason?: string; // 却下理由（任意）
}

/**
 * 問い合わせ一覧リクエストパラメータ型
 */
export interface ListInquiriesParams {
  page?: number; // デフォルト: 1
  limit?: number; // デフォルト: 20、範囲: 1-100
  status?: InquiryStatus | InquiryStatus[];
  user_id?: string;
  sort_by?: "created_at" | "updated_at";
  sort_order?: "asc" | "desc"; // デフォルト: 'desc'
}

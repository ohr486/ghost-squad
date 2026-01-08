/**
 * ストーリー管理機能 - TypeScript型定義
 *
 * バックエンドスキーマと完全に一致する型定義
 * 要件: 4.7, 4.8
 */

import type { Priority } from "./inquiry";

/**
 * ストーリーステータス列挙型
 */
export type StoryStatus =
  | "waiting_review" // レビュー待ち
  | "approved" // 承認済み
  | "rejected"; // 却下

/**
 * 承認情報
 */
export interface ApprovalInfo {
  approved_at: string; // 承認日時（ISO 8601）
  approver: string; // 承認者
}

/**
 * ストーリー却下情報
 */
export interface StoryRejectionInfo {
  rejected_at: string; // 却下日時（ISO 8601）
  rejector: string; // 却下者
  reason: string; // 却下理由（必須）
}

/**
 * ストーリーステータス変更履歴エントリ
 */
export interface StoryStatusHistoryEntry {
  from_status: StoryStatus;
  to_status: StoryStatus;
  changed_at: string; // ISO 8601形式
  changed_by?: string; // 変更者
}

/**
 * ストーリーメタデータ構造
 */
export interface StoryMetadata {
  // 承認情報
  approval?: ApprovalInfo;

  // 却下情報
  rejection?: StoryRejectionInfo;

  // ステータス変更履歴
  status_history?: StoryStatusHistoryEntry[];

  // その他のメタデータ
  [key: string]: any;
}

/**
 * ストーリーレスポンス型
 * バックエンドAPIから返されるストーリーデータ
 */
export interface StoryResponse {
  id: number;
  inquiry_id: number;
  title: string;
  description: string;
  priority: Priority;
  status: StoryStatus;
  estimated_effort: number | null;
  deadline: string | null; // ISO 8601形式
  assignee: string | null;
  story_metadata: StoryMetadata;
  created_at: string; // ISO 8601形式
  updated_at: string; // ISO 8601形式
}

/**
 * ストーリー作成リクエスト型（手動作成）
 * inquiry_idはパスパラメータで指定
 */
export interface CreateStoryRequest {
  title: string; // 1-500文字
  description: string; // 必須
  priority: Priority;
  estimated_effort?: number; // オプショナル
  deadline?: string; // ISO 8601形式、オプショナル
  assignee?: string; // オプショナル
}

/**
 * ストーリー更新リクエスト型
 */
export interface UpdateStoryRequest {
  title?: string;
  description?: string;
  priority?: Priority;
  estimated_effort?: number;
  deadline?: string; // ISO 8601形式
  assignee?: string;
}

/**
 * ストーリー承認リクエスト型
 */
export interface ApproveStoryRequest {
  approver: string; // 承認者名
}

/**
 * ストーリー却下リクエスト型
 */
export interface RejectStoryRequest {
  rejector: string; // 却下者名
  reason: string; // 却下理由（必須）
}

/**
 * 一括承認リクエスト型
 */
export interface BatchApproveRequest {
  story_ids: number[];
  approver: string; // 承認者名
}

/**
 * 一括承認レスポンス型
 */
export interface BatchApproveResponse {
  results: Array<{
    id: number;
    success: boolean;
    error?: string;
  }>;
}

/**
 * ストーリー一覧リクエストパラメータ型
 */
export interface ListStoriesParams {
  page?: number; // デフォルト: 1
  limit?: number; // デフォルト: 20、範囲: 1-100
  status?: StoryStatus | StoryStatus[];
  priority?: Priority | Priority[];
  inquiry_id?: number;
  sort_by?:
    | "created_at"
    | "updated_at"
    | "priority"
    | "estimated_effort"
    | "assignee"
    | "deadline";
  sort_order?: "asc" | "desc"; // デフォルト: 'desc'
}

/**
 * ストーリーAPI クライアントサービス
 *
 * Axiosを使用したHTTP通信とエラーハンドリング
 * 要件: 2.1, 2.5, 2.6, 2.8, 2.15, 3.1, 3.4
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from "axios";
import type {
  StoryResponse,
  CreateStoryRequest,
  UpdateStoryRequest,
  ApproveStoryRequest,
  RejectStoryRequest,
  BatchApproveRequest,
  BatchApproveResponse,
  PaginatedResponse,
  ErrorResponse,
  ListStoriesParams,
} from "../types";

/**
 * APIベースURL
 * 環境変数から取得、デフォルトはlocalhost:8000
 */
const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

/**
 * Axiosインスタンスの作成と設定
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30秒タイムアウト
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: false, // CORS設定
});

/**
 * レスポンスインターセプター - タイムスタンプのパース
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // タイムスタンプフィールドをDateオブジェクトに変換する処理は
    // コンポーネント側で必要に応じて実施
    return response;
  },
  (error: AxiosError<ErrorResponse>) => {
    // エラーレスポンスの標準化
    if (error.response?.data) {
      // バックエンドから返されたエラーレスポンスをそのまま返す
      return Promise.reject(error.response.data);
    }

    // ネットワークエラーなど、バックエンドから返されないエラー
    const genericError: ErrorResponse = {
      errors: [
        {
          code: "NETWORK_ERROR",
          message: "ネットワークエラーが発生しました。接続を確認してください。",
        },
      ],
      timestamp: new Date().toISOString(),
    };
    return Promise.reject(genericError);
  },
);

/**
 * ストーリー手動作成API呼び出し
 *
 * @param inquiryId 問い合わせID（パスパラメータ）
 * @param data ストーリー作成リクエストデータ
 * @returns 作成されたストーリー
 * @throws ErrorResponse バリデーションエラーまたはサーバーエラー
 */
export async function createStory(
  inquiryId: number,
  data: CreateStoryRequest,
): Promise<StoryResponse> {
  const response = await apiClient.post<StoryResponse>(
    `/api/inquiries/${inquiryId}/stories`,
    data,
  );
  return response.data;
}

/**
 * AI自動生成によるストーリー作成API呼び出し
 *
 * @param inquiryId 問い合わせID（パスパラメータ）
 * @returns 生成されたストーリー
 * @throws ErrorResponse AI生成失敗、Inquiry不存在、またはサーバーエラー
 */
export async function generateStory(inquiryId: number): Promise<StoryResponse> {
  // ボディなしでPOSTすることでAI自動生成を指示
  const response = await apiClient.post<StoryResponse>(
    `/api/inquiries/${inquiryId}/stories`,
    undefined,
  );
  return response.data;
}

/**
 * クエリパラメータ構築のヘルパー関数
 *
 * @param params ListStoriesParams型のパラメータ
 * @returns クエリパラメータオブジェクト
 */
function buildQueryParams(params?: ListStoriesParams): Record<string, string> {
  const queryParams: Record<string, string> = {};

  if (params?.page !== undefined) {
    queryParams.page = String(params.page);
  }
  if (params?.limit !== undefined) {
    queryParams.limit = String(params.limit);
  }
  if (params?.status !== undefined) {
    // 単一ステータスまたは配列を処理
    queryParams.status = Array.isArray(params.status)
      ? params.status.join(",")
      : params.status;
  }
  if (params?.priority !== undefined) {
    // 単一優先度または配列を処理
    queryParams.priority = Array.isArray(params.priority)
      ? params.priority.join(",")
      : params.priority;
  }
  if (params?.inquiry_id !== undefined) {
    queryParams.inquiry_id = String(params.inquiry_id);
  }
  if (params?.sort_by !== undefined) {
    queryParams.sort_by = params.sort_by;
  }
  if (params?.sort_order !== undefined) {
    queryParams.sort_order = params.sort_order;
  }

  return queryParams;
}

/**
 * ストーリー一覧取得API呼び出し（全ストーリー）
 *
 * @param params クエリパラメータ（ページネーション、フィルタリング、ソート）
 * @returns ページネーション付きストーリー一覧
 * @throws ErrorResponse サーバーエラー
 */
export async function listStories(
  params?: ListStoriesParams,
): Promise<PaginatedResponse<StoryResponse>> {
  const queryParams = buildQueryParams(params);

  const response = await apiClient.get<PaginatedResponse<StoryResponse>>(
    "/api/stories",
    { params: queryParams },
  );
  return response.data;
}

/**
 * 問い合わせ配下のストーリー一覧取得API呼び出し
 *
 * @param inquiryId 問い合わせID
 * @param params クエリパラメータ（ページネーション、フィルタリング、ソート）
 * @returns ページネーション付きストーリー一覧
 * @throws ErrorResponse Inquiry不存在またはサーバーエラー
 */
export async function listStoriesByInquiry(
  inquiryId: number,
  params?: ListStoriesParams,
): Promise<PaginatedResponse<StoryResponse>> {
  const queryParams = buildQueryParams(params);

  const response = await apiClient.get<PaginatedResponse<StoryResponse>>(
    `/api/inquiries/${inquiryId}/stories`,
    { params: queryParams },
  );
  return response.data;
}

/**
 * ストーリー詳細取得API呼び出し
 *
 * @param id ストーリーID
 * @returns ストーリー詳細
 * @throws ErrorResponse 404 Not Foundまたはサーバーエラー
 */
export async function getStory(id: number): Promise<StoryResponse> {
  const response = await apiClient.get<StoryResponse>(`/api/stories/${id}`);
  return response.data;
}

/**
 * ストーリー更新API呼び出し
 *
 * @param id ストーリーID
 * @param data 更新データ
 * @returns 更新されたストーリー
 * @throws ErrorResponse バリデーションエラー、404 Not Found、またはサーバーエラー
 */
export async function updateStory(
  id: number,
  data: UpdateStoryRequest,
): Promise<StoryResponse> {
  const response = await apiClient.put<StoryResponse>(
    `/api/stories/${id}`,
    data,
  );
  return response.data;
}

/**
 * ストーリー削除API呼び出し
 *
 * @param id ストーリーID
 * @returns 削除成功時のレスポンス
 * @throws ErrorResponse 404 Not Foundまたはサーバーエラー
 */
export async function deleteStory(id: number): Promise<{ success: boolean }> {
  const response = await apiClient.delete<{ success: boolean }>(
    `/api/stories/${id}`,
  );
  return response.data;
}

/**
 * ストーリー承認API呼び出し
 *
 * @param id ストーリーID
 * @param data 承認者情報
 * @returns 承認されたストーリー（ステータス: approved）
 * @throws ErrorResponse 404 Not Found、422 Unprocessable Entity（無効なステータス遷移）、またはサーバーエラー
 */
export async function approveStory(
  id: number,
  data: ApproveStoryRequest,
): Promise<StoryResponse> {
  const response = await apiClient.post<StoryResponse>(
    `/api/stories/${id}/approve`,
    data,
  );
  return response.data;
}

/**
 * ストーリー却下API呼び出し
 *
 * @param id ストーリーID
 * @param data 却下者情報と却下理由（必須）
 * @returns 却下されたストーリー（ステータス: rejected）
 * @throws ErrorResponse 404 Not Found、422 Unprocessable Entity（無効なステータス遷移）、400 Bad Request（理由未入力）、またはサーバーエラー
 */
export async function rejectStory(
  id: number,
  data: RejectStoryRequest,
): Promise<StoryResponse> {
  const response = await apiClient.post<StoryResponse>(
    `/api/stories/${id}/reject`,
    data,
  );
  return response.data;
}

/**
 * ストーリー一括承認API呼び出し
 *
 * @param data 一括承認リクエスト（ストーリーIDリストと承認者）
 * @returns 一括承認結果（各ストーリーの成功/失敗）
 * @throws ErrorResponse バリデーションエラーまたはサーバーエラー
 */
export async function batchApproveStories(
  data: BatchApproveRequest,
): Promise<BatchApproveResponse> {
  const response = await apiClient.post<BatchApproveResponse>(
    "/api/stories/batch-approve",
    data,
  );
  return response.data;
}

/**
 * エクスポート用APIクライアント（デフォルトエクスポート）
 */
const storyApiClient = {
  createStory,
  generateStory,
  listStories,
  listStoriesByInquiry,
  getStory,
  updateStory,
  deleteStory,
  approveStory,
  rejectStory,
  batchApproveStories,
};

export default storyApiClient;

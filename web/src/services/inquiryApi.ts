/**
 * 問い合わせAPI クライアントサービス
 *
 * Axiosを使用したHTTP通信とエラーハンドリング
 * 要件: 1.1, 2.1, 2.3, 2.5, 2.8, 3.1, 3.4
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from "axios";
import type {
  InquiryResponse,
  CreateInquiryRequest,
  UpdateInquiryRequest,
  PaginatedResponse,
  ErrorResponse,
  RejectInquiryRequest,
  ListInquiriesParams,
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
 * 問い合わせ作成API呼び出し
 *
 * @param data 問い合わせ作成リクエストデータ
 * @returns 作成された問い合わせ
 * @throws ErrorResponse バリデーションエラーまたはサーバーエラー
 */
export async function createInquiry(
  data: CreateInquiryRequest,
): Promise<InquiryResponse> {
  const response = await apiClient.post<InquiryResponse>(
    "/api/inquiries",
    data,
  );
  return response.data;
}

/**
 * 問い合わせ一覧取得API呼び出し
 *
 * @param params クエリパラメータ（ページネーション、フィルタリング、ソート）
 * @returns ページネーション付き問い合わせ一覧
 * @throws ErrorResponse サーバーエラー
 */
export async function listInquiries(
  params?: ListInquiriesParams,
): Promise<PaginatedResponse<InquiryResponse>> {
  // クエリパラメータの構築
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
  if (params?.user_id !== undefined) {
    queryParams.user_id = params.user_id;
  }
  if (params?.sort_by !== undefined) {
    queryParams.sort_by = params.sort_by;
  }
  if (params?.sort_order !== undefined) {
    queryParams.sort_order = params.sort_order;
  }

  const response = await apiClient.get<PaginatedResponse<InquiryResponse>>(
    "/api/inquiries",
    { params: queryParams },
  );
  return response.data;
}

/**
 * 問い合わせ詳細取得API呼び出し
 *
 * @param id 問い合わせID
 * @returns 問い合わせ詳細
 * @throws ErrorResponse 404 Not Foundまたはサーバーエラー
 */
export async function getInquiry(id: number): Promise<InquiryResponse> {
  const response = await apiClient.get<InquiryResponse>(`/api/inquiries/${id}`);
  return response.data;
}

/**
 * 問い合わせ更新API呼び出し
 *
 * @param id 問い合わせID
 * @param data 更新データ
 * @returns 更新された問い合わせ
 * @throws ErrorResponse バリデーションエラー、404 Not Found、またはサーバーエラー
 */
export async function updateInquiry(
  id: number,
  data: UpdateInquiryRequest,
): Promise<InquiryResponse> {
  const response = await apiClient.put<InquiryResponse>(
    `/api/inquiries/${id}`,
    data,
  );
  return response.data;
}

/**
 * 問い合わせ承認API呼び出し
 *
 * @param id 問い合わせID
 * @returns 承認された問い合わせ（ステータス: task_working）
 * @throws ErrorResponse 404 Not Found、409 Conflict（無効なステータス遷移）、またはサーバーエラー
 */
export async function approveInquiry(id: number): Promise<InquiryResponse> {
  const response = await apiClient.post<InquiryResponse>(
    `/api/inquiries/${id}/approve`,
  );
  return response.data;
}

/**
 * 問い合わせ却下API呼び出し
 *
 * @param id 問い合わせID
 * @param data 却下理由（任意）
 * @returns 却下された問い合わせ（ステータス: rejected）
 * @throws ErrorResponse 404 Not Found、409 Conflict（無効なステータス遷移）、またはサーバーエラー
 */
export async function rejectInquiry(
  id: number,
  data?: RejectInquiryRequest,
): Promise<InquiryResponse> {
  const response = await apiClient.post<InquiryResponse>(
    `/api/inquiries/${id}/reject`,
    data || {},
  );
  return response.data;
}

/**
 * ヘルスチェックAPI呼び出し
 *
 * @returns ヘルスチェック結果
 */
export async function healthCheck(): Promise<{ status: string }> {
  const response = await apiClient.get<{ status: string }>("/health");
  return response.data;
}

/**
 * エクスポート用APIクライアント（デフォルトエクスポート）
 */
const inquiryApiClient = {
  createInquiry,
  listInquiries,
  getInquiry,
  updateInquiry,
  approveInquiry,
  rejectInquiry,
  healthCheck,
};

export default inquiryApiClient;

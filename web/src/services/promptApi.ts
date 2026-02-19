/**
 * Prompt管理 API クライアントサービス
 *
 * Axiosを使用したHTTP通信とエラーハンドリング
 * 要件: 1.1, 1.2, 2.2, 2.5, 3.1, 3.2, 3.4, 4.4
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from "axios";
import type {
  PromptResponse,
  PromptListResponse,
  PromptCategory,
  UpdatePromptRequest,
  TestPromptRequest,
  TestPromptResult,
  AcquireLockRequest,
  LockResponse,
  PromptErrorResponse,
} from "../types/prompt";

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
 * レスポンスインターセプター - エラーハンドリング
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError<{ detail: PromptErrorResponse }>) => {
    // エラーレスポンスの標準化
    if (error.response?.data?.detail) {
      // FastAPIのHTTPExceptionは { detail: {...} } 形式で返す
      return Promise.reject(error.response.data.detail);
    }

    // ネットワークエラーなど、バックエンドから返されないエラー
    const genericError: PromptErrorResponse = {
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

// =============================================================================
// プロンプト一覧・詳細API（要件1.1, 1.2, 1.3）
// =============================================================================

/**
 * プロンプト一覧取得
 *
 * @param category カテゴリフィルタ（オプション）
 * @returns プロンプト一覧レスポンス
 * @throws PromptErrorResponse 無効なカテゴリ（GS-403）またはサーバーエラー
 */
export async function listPrompts(
  category?: PromptCategory,
): Promise<PromptListResponse> {
  const params: Record<string, string> = {};
  if (category) {
    params.category = category;
  }

  const response = await apiClient.get<PromptListResponse>("/api/prompts", {
    params,
  });
  return response.data;
}

/**
 * プロンプト詳細取得
 *
 * @param key プロンプトキー
 * @returns プロンプトレスポンス
 * @throws PromptErrorResponse プロンプトが見つからない（GS-404）またはサーバーエラー
 */
export async function getPrompt(key: string): Promise<PromptResponse> {
  const response = await apiClient.get<PromptResponse>(`/api/prompts/${key}`);
  return response.data;
}

// =============================================================================
// プロンプト更新API（要件2.2）
// =============================================================================

/**
 * プロンプト更新
 *
 * @param key プロンプトキー
 * @param request 更新リクエスト
 * @returns 更新後のプロンプトレスポンス
 * @throws PromptErrorResponse バリデーションエラー（GS-401）、プロンプトが見つからない（GS-404）、編集ロック競合（GS-405）
 */
export async function updatePrompt(
  key: string,
  request: UpdatePromptRequest,
): Promise<PromptResponse> {
  const response = await apiClient.put<PromptResponse>(
    `/api/prompts/${key}`,
    request,
  );
  return response.data;
}

// =============================================================================
// テスト実行API（要件3.1, 3.2, 3.4）
// =============================================================================

/**
 * プロンプトテスト実行
 *
 * @param request テスト実行リクエスト
 * @returns テスト実行結果
 * @throws PromptErrorResponse バリデーションエラー（GS-401）、タイムアウト（GS-406）、AI API失敗（GS-407）
 */
export async function testPrompt(
  request: TestPromptRequest,
): Promise<TestPromptResult> {
  const response = await apiClient.post<TestPromptResult>(
    "/api/prompts/test",
    request,
  );
  return response.data;
}

// =============================================================================
// デフォルトリセットAPI（要件4.4）
// =============================================================================

/**
 * プロンプトをデフォルトにリセット
 *
 * @param key プロンプトキー
 * @returns リセット後のプロンプトレスポンス
 * @throws PromptErrorResponse プロンプトが見つからない（GS-404）
 */
export async function resetPrompt(key: string): Promise<PromptResponse> {
  const response = await apiClient.post<PromptResponse>(
    `/api/prompts/${key}/reset`,
  );
  return response.data;
}

// =============================================================================
// 編集ロックAPI（要件2.5）
// =============================================================================

/**
 * 編集ロック取得
 *
 * @param key プロンプトキー
 * @param request ロック取得リクエスト
 * @returns ロックレスポンス
 * @throws PromptErrorResponse プロンプトが見つからない（GS-404）、編集ロック競合（GS-405）
 */
export async function acquireLock(
  key: string,
  request: AcquireLockRequest,
): Promise<LockResponse> {
  const response = await apiClient.post<LockResponse>(
    `/api/prompts/${key}/lock`,
    request,
  );
  return response.data;
}

/**
 * 編集ロック解放
 *
 * @param key プロンプトキー
 * @throws PromptErrorResponse プロンプトが見つからない（GS-404）
 */
export async function releaseLock(key: string): Promise<void> {
  await apiClient.delete(`/api/prompts/${key}/lock`);
}

// =============================================================================
// デフォルトエクスポート
// =============================================================================

/**
 * エクスポート用APIクライアント（デフォルトエクスポート）
 */
const promptApiClient = {
  listPrompts,
  getPrompt,
  updatePrompt,
  testPrompt,
  resetPrompt,
  acquireLock,
  releaseLock,
};

export default promptApiClient;

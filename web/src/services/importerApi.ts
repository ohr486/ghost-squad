/**
 * Importer API クライアントサービス
 *
 * Axiosを使用したHTTP通信とエラーハンドリング
 * 要件: 1.1, 1.2, 2.1-2.6, 3.1-3.6, 4.1-4.5, 5.2, 5.4
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from "axios";
import type {
  PluginStatus,
  PluginListResponse,
  AIProviderStatus,
  AIProviderListResponse,
  ExecuteImportRequest,
  RetryImportRequest,
  ImportResult,
  ErrorStatsListResponse,
  ImporterErrorResponse,
} from "../types/importer";

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
  (error: AxiosError<ImporterErrorResponse>) => {
    // エラーレスポンスの標準化
    if (error.response?.data) {
      // バックエンドから返されたエラーレスポンスをそのまま返す
      return Promise.reject(error.response.data);
    }

    // ネットワークエラーなど、バックエンドから返されないエラー
    const genericError: ImporterErrorResponse = {
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
// プラグイン管理API（タスク10.1）
// =============================================================================

/**
 * プラグイン一覧取得
 *
 * @returns プラグイン一覧レスポンス
 * @throws ImporterErrorResponse サーバーエラー
 */
export async function listPlugins(): Promise<PluginListResponse> {
  const response = await apiClient.get<PluginListResponse>("/api/plugins");
  return response.data;
}

/**
 * プラグイン有効化
 *
 * @param pluginType プラグイン種別（例: email, sentry）
 * @returns 有効化後のプラグインステータス
 * @throws ImporterErrorResponse プラグインが見つからない（GS-301）またはサーバーエラー
 */
export async function enablePlugin(pluginType: string): Promise<PluginStatus> {
  const response = await apiClient.post<PluginStatus>(
    `/api/plugins/${pluginType}/enable`,
  );
  return response.data;
}

/**
 * プラグイン無効化
 *
 * @param pluginType プラグイン種別（例: email, sentry）
 * @returns 無効化後のプラグインステータス
 * @throws ImporterErrorResponse プラグインが見つからない（GS-301）またはサーバーエラー
 */
export async function disablePlugin(pluginType: string): Promise<PluginStatus> {
  const response = await apiClient.post<PluginStatus>(
    `/api/plugins/${pluginType}/disable`,
  );
  return response.data;
}

// =============================================================================
// AIプロバイダー管理API（タスク10.2）
// =============================================================================

/**
 * AIプロバイダー一覧取得
 *
 * @returns AIプロバイダー一覧レスポンス
 * @throws ImporterErrorResponse サーバーエラー
 */
export async function listAIProviders(): Promise<AIProviderListResponse> {
  const response =
    await apiClient.get<AIProviderListResponse>("/api/ai-providers");
  return response.data;
}

/**
 * デフォルトAIプロバイダー設定
 *
 * @param providerType プロバイダー種別（例: openai, anthropic）
 * @returns 設定後のプロバイダーステータス
 * @throws ImporterErrorResponse プロバイダーが見つからない（GS-308）またはサーバーエラー
 */
export async function setDefaultAIProvider(
  providerType: string,
): Promise<AIProviderStatus> {
  const response = await apiClient.post<AIProviderStatus>(
    `/api/ai-providers/${providerType}/set-default`,
  );
  return response.data;
}

// =============================================================================
// インポート実行API（タスク10.3）
// =============================================================================

/**
 * インポート実行
 *
 * @param request インポート実行リクエスト
 * @returns インポート結果
 * @throws ImporterErrorResponse プラグインが見つからない（GS-301）、接続エラー（GS-303）、AI解析失敗（GS-304）、その他エラー
 */
export async function executeImport(
  request: ExecuteImportRequest,
): Promise<ImportResult> {
  const response = await apiClient.post<ImportResult>(
    "/api/importers/execute",
    request,
  );
  return response.data;
}

/**
 * インポートリトライ
 *
 * @param request リトライリクエスト
 * @returns リトライ結果
 * @throws ImporterErrorResponse プラグインが見つからない（GS-301）、データ取得失敗（GS-306）、その他エラー
 */
export async function retryImport(
  request: RetryImportRequest,
): Promise<ImportResult> {
  const response = await apiClient.post<ImportResult>(
    "/api/importers/retry",
    request,
  );
  return response.data;
}

// =============================================================================
// エラー統計API（タスク10.4）
// =============================================================================

/**
 * エラー統計取得
 *
 * @param pluginType プラグイン種別でフィルタ（オプション）
 * @returns エラー統計一覧レスポンス
 * @throws ImporterErrorResponse サーバーエラー
 */
export async function getErrorStats(
  pluginType?: string,
): Promise<ErrorStatsListResponse> {
  const params: Record<string, string> = {};
  if (pluginType) {
    params.plugin_type = pluginType;
  }

  const response = await apiClient.get<ErrorStatsListResponse>(
    "/api/importers/stats",
    { params },
  );
  return response.data;
}

// =============================================================================
// デフォルトエクスポート
// =============================================================================

/**
 * エクスポート用APIクライアント（デフォルトエクスポート）
 */
const importerApiClient = {
  // プラグイン管理
  listPlugins,
  enablePlugin,
  disablePlugin,
  // AIプロバイダー管理
  listAIProviders,
  setDefaultAIProvider,
  // インポート実行
  executeImport,
  retryImport,
  // エラー統計
  getErrorStats,
};

export default importerApiClient;

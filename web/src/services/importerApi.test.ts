/**
 * ImporterAPI テスト
 *
 * TDD: RED/GREEN Phase
 * 要件: 1.1, 1.2, 2.1-2.6, 3.1-3.6, 4.1-4.5, 5.2, 5.4
 */

import type {
  PluginStatus,
  PluginListResponse,
  AIProviderStatus,
  AIProviderListResponse,
  ImportResult,
  ErrorStats,
  ErrorStatsListResponse,
  ImporterErrorResponse,
} from "../types/importer";
import axios from "axios";
import {
  listPlugins,
  enablePlugin,
  disablePlugin,
  listAIProviders,
  setDefaultAIProvider,
  executeImport,
  retryImport,
  getErrorStats,
} from "./importerApi";

// axiosのマニュアルモックを使用
jest.mock("axios");

// モックインスタンスを型安全に取得
const mockAxiosInstance = (axios as any).create() as {
  get: jest.Mock;
  post: jest.Mock;
  put: jest.Mock;
  delete: jest.Mock;
};

// Get the applyErrorInterceptor helper from the mocked module
const axiosMock = axios as any;
const applyErrorInterceptor = axiosMock.applyErrorInterceptor;

describe("ImporterAPI", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // =============================================================================
  // プラグイン管理API（タスク10.1）
  // =============================================================================

  describe("プラグイン管理API", () => {
    describe("listPlugins", () => {
      it("プラグイン一覧を取得できる", async () => {
        const mockPlugins: PluginStatus[] = [
          {
            plugin_type: "email",
            enabled: true,
            initialized: true,
            error_message: null,
          },
          {
            plugin_type: "sentry",
            enabled: false,
            initialized: false,
            error_message: "未設定",
          },
        ];
        const mockResponse: PluginListResponse = {
          data: mockPlugins,
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

        const result = await listPlugins();

        expect(mockAxiosInstance.get).toHaveBeenCalledWith("/api/plugins");
        expect(result.data).toHaveLength(2);
        expect(result.data[0].plugin_type).toBe("email");
        expect(result.data[1].enabled).toBe(false);
      });

      it("サーバーエラー時にエラーを返す", async () => {
        const errorResponse: ImporterErrorResponse = {
          errors: [
            {
              code: "GS-310",
              message: "プラグイン一覧の取得に失敗しました",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 500,
            data: errorResponse,
          },
        };

        mockAxiosInstance.get.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(listPlugins()).rejects.toEqual(errorResponse);
      });
    });

    describe("enablePlugin", () => {
      it("プラグインを有効化できる", async () => {
        const mockPlugin: PluginStatus = {
          plugin_type: "email",
          enabled: true,
          initialized: true,
          error_message: null,
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockPlugin });

        const result = await enablePlugin("email");

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/plugins/email/enable",
        );
        expect(result.enabled).toBe(true);
        expect(result.plugin_type).toBe("email");
      });

      it("存在しないプラグインでエラー", async () => {
        const errorResponse: ImporterErrorResponse = {
          errors: [
            {
              code: "GS-301",
              message: "プラグイン 'unknown' が見つかりません",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 404,
            data: errorResponse,
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(enablePlugin("unknown")).rejects.toEqual(errorResponse);
      });
    });

    describe("disablePlugin", () => {
      it("プラグインを無効化できる", async () => {
        const mockPlugin: PluginStatus = {
          plugin_type: "email",
          enabled: false,
          initialized: true,
          error_message: null,
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockPlugin });

        const result = await disablePlugin("email");

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/plugins/email/disable",
        );
        expect(result.enabled).toBe(false);
      });

      it("存在しないプラグインでエラー", async () => {
        const errorResponse: ImporterErrorResponse = {
          errors: [
            {
              code: "GS-301",
              message: "プラグイン 'unknown' が見つかりません",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 404,
            data: errorResponse,
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(disablePlugin("unknown")).rejects.toEqual(errorResponse);
      });
    });
  });

  // =============================================================================
  // AIプロバイダー管理API（タスク10.2）
  // =============================================================================

  describe("AIプロバイダー管理API", () => {
    describe("listAIProviders", () => {
      it("AIプロバイダー一覧を取得できる", async () => {
        const mockProviders: AIProviderStatus[] = [
          {
            provider_type: "openai",
            enabled: true,
            initialized: true,
            is_default: true,
            model: "gpt-4",
            error_message: null,
          },
          {
            provider_type: "anthropic",
            enabled: true,
            initialized: true,
            is_default: false,
            model: "claude-3-sonnet-20240229",
            error_message: null,
          },
        ];
        const mockResponse: AIProviderListResponse = {
          data: mockProviders,
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

        const result = await listAIProviders();

        expect(mockAxiosInstance.get).toHaveBeenCalledWith("/api/ai-providers");
        expect(result.data).toHaveLength(2);
        expect(result.data[0].provider_type).toBe("openai");
        expect(result.data[0].is_default).toBe(true);
        expect(result.data[1].provider_type).toBe("anthropic");
      });

      it("サーバーエラー時にエラーを返す", async () => {
        const errorResponse: ImporterErrorResponse = {
          errors: [
            {
              code: "GS-309",
              message: "AIプロバイダー一覧の取得に失敗しました",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 500,
            data: errorResponse,
          },
        };

        mockAxiosInstance.get.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(listAIProviders()).rejects.toEqual(errorResponse);
      });
    });

    describe("setDefaultAIProvider", () => {
      it("デフォルトAIプロバイダーを設定できる", async () => {
        const mockProvider: AIProviderStatus = {
          provider_type: "anthropic",
          enabled: true,
          initialized: true,
          is_default: true,
          model: "claude-3-sonnet-20240229",
          error_message: null,
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockProvider });

        const result = await setDefaultAIProvider("anthropic");

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/ai-providers/anthropic/set-default",
        );
        expect(result.is_default).toBe(true);
        expect(result.provider_type).toBe("anthropic");
      });

      it("存在しないプロバイダーでエラー", async () => {
        const errorResponse: ImporterErrorResponse = {
          errors: [
            {
              code: "GS-308",
              message: "AIプロバイダー 'gemini' が見つかりません",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 404,
            data: errorResponse,
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(setDefaultAIProvider("gemini")).rejects.toEqual(
          errorResponse,
        );
      });
    });
  });

  // =============================================================================
  // インポート実行API（タスク10.3）
  // =============================================================================

  describe("インポート実行API", () => {
    describe("executeImport", () => {
      it("インポートを実行できる", async () => {
        const mockResult: ImportResult = {
          total_fetched: 10,
          total_imported: 8,
          total_skipped: 1,
          total_failed: 1,
          imported_inquiry_ids: [101, 102, 103, 104, 105, 106, 107, 108],
          errors: [
            {
              source_id: "<error-message@example.com>",
              error_code: "GS-304",
              error_message: "AI解析に失敗しました",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult });

        const result = await executeImport({ plugin_type: "email" });

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/importers/execute",
          { plugin_type: "email" },
        );
        expect(result.total_fetched).toBe(10);
        expect(result.total_imported).toBe(8);
        expect(result.imported_inquiry_ids).toHaveLength(8);
        expect(result.errors).toHaveLength(1);
      });

      it("AIプロバイダーを指定してインポートできる", async () => {
        const mockResult: ImportResult = {
          total_fetched: 5,
          total_imported: 5,
          total_skipped: 0,
          total_failed: 0,
          imported_inquiry_ids: [201, 202, 203, 204, 205],
          errors: [],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult });

        const result = await executeImport({
          plugin_type: "email",
          ai_provider_type: "anthropic",
        });

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/importers/execute",
          { plugin_type: "email", ai_provider_type: "anthropic" },
        );
        expect(result.total_imported).toBe(5);
      });

      it("プラグインが見つからない場合エラー", async () => {
        const errorResponse: ImporterErrorResponse = {
          errors: [
            {
              code: "GS-301",
              message: "プラグイン 'unknown' が見つかりません",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 404,
            data: errorResponse,
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(executeImport({ plugin_type: "unknown" })).rejects.toEqual(
          errorResponse,
        );
      });

      it("接続エラー時にエラーを返す", async () => {
        const errorResponse: ImporterErrorResponse = {
          errors: [
            {
              code: "GS-303",
              message: "データソースへの接続に失敗しました",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 500,
            data: errorResponse,
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(executeImport({ plugin_type: "email" })).rejects.toEqual(
          errorResponse,
        );
      });
    });

    describe("retryImport", () => {
      it("失敗したインポートをリトライできる", async () => {
        const mockResult: ImportResult = {
          total_fetched: 2,
          total_imported: 2,
          total_skipped: 0,
          total_failed: 0,
          imported_inquiry_ids: [301, 302],
          errors: [],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult });

        const result = await retryImport({
          plugin_type: "email",
          source_ids: ["<message-1@example.com>", "<message-2@example.com>"],
        });

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/importers/retry",
          {
            plugin_type: "email",
            source_ids: ["<message-1@example.com>", "<message-2@example.com>"],
          },
        );
        expect(result.total_imported).toBe(2);
      });

      it("AIプロバイダーを切り替えてリトライできる", async () => {
        const mockResult: ImportResult = {
          total_fetched: 1,
          total_imported: 1,
          total_skipped: 0,
          total_failed: 0,
          imported_inquiry_ids: [401],
          errors: [],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult });

        const result = await retryImport({
          plugin_type: "email",
          source_ids: ["<message-1@example.com>"],
          ai_provider_type: "anthropic",
        });

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/importers/retry",
          {
            plugin_type: "email",
            source_ids: ["<message-1@example.com>"],
            ai_provider_type: "anthropic",
          },
        );
        expect(result.total_imported).toBe(1);
      });

      it("リトライ失敗時にエラーを返す", async () => {
        const errorResponse: ImporterErrorResponse = {
          errors: [
            {
              code: "GS-306",
              message: "データ取得に失敗しました",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 500,
            data: errorResponse,
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(
          retryImport({
            plugin_type: "email",
            source_ids: ["<message-1@example.com>"],
          }),
        ).rejects.toEqual(errorResponse);
      });
    });
  });

  // =============================================================================
  // エラー統計API（タスク10.4）
  // =============================================================================

  describe("エラー統計API", () => {
    describe("getErrorStats", () => {
      it("エラー統計を取得できる", async () => {
        const mockStats: ErrorStats[] = [
          {
            error_code: "GS-304",
            count: 15,
            last_occurred: "2024-01-15T10:30:00+00:00",
          },
          {
            error_code: "GS-303",
            count: 5,
            last_occurred: "2024-01-14T14:20:00+00:00",
          },
        ];
        const mockResponse: ErrorStatsListResponse = {
          data: mockStats,
          timestamp: "2024-01-15T12:00:00+00:00",
        };

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

        const result = await getErrorStats();

        expect(mockAxiosInstance.get).toHaveBeenCalledWith(
          "/api/importers/stats",
          { params: {} },
        );
        expect(result.data).toHaveLength(2);
        expect(result.data[0].error_code).toBe("GS-304");
        expect(result.data[0].count).toBe(15);
      });

      it("プラグインでフィルタリングできる", async () => {
        const mockStats: ErrorStats[] = [
          {
            error_code: "GS-320",
            count: 3,
            last_occurred: "2024-01-15T10:30:00+00:00",
          },
        ];
        const mockResponse: ErrorStatsListResponse = {
          data: mockStats,
          timestamp: "2024-01-15T12:00:00+00:00",
        };

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

        const result = await getErrorStats("email");

        expect(mockAxiosInstance.get).toHaveBeenCalledWith(
          "/api/importers/stats",
          { params: { plugin_type: "email" } },
        );
        expect(result.data).toHaveLength(1);
      });

      it("エラーがない場合は空リストを返す", async () => {
        const mockResponse: ErrorStatsListResponse = {
          data: [],
          timestamp: "2024-01-15T12:00:00+00:00",
        };

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

        const result = await getErrorStats();

        expect(result.data).toHaveLength(0);
      });

      it("サーバーエラー時にエラーを返す", async () => {
        const errorResponse: ImporterErrorResponse = {
          errors: [
            {
              code: "GS-310",
              message: "エラー統計の取得に失敗しました",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 500,
            data: errorResponse,
          },
        };

        mockAxiosInstance.get.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(getErrorStats()).rejects.toEqual(errorResponse);
      });
    });
  });

  // =============================================================================
  // ネットワークエラー
  // =============================================================================

  describe("ネットワークエラー", () => {
    it("ネットワークエラー時に標準化されたエラーを返す", async () => {
      // Simulate a network error (no response from backend)
      const networkError = {
        message: "Network Error",
        // No response property - simulates connection failure
      };

      mockAxiosInstance.get.mockImplementationOnce(() =>
        applyErrorInterceptor(networkError),
      );

      await expect(listPlugins()).rejects.toMatchObject({
        errors: [
          {
            code: "NETWORK_ERROR",
            message: expect.stringContaining("ネットワークエラー"),
          },
        ],
        timestamp: expect.any(String),
      });
    });

    it("タイムアウトエラー時に標準化されたエラーを返す", async () => {
      // Simulate a timeout error
      const timeoutError = {
        code: "ECONNABORTED",
        message: "timeout of 30000ms exceeded",
      };

      mockAxiosInstance.post.mockImplementationOnce(() =>
        applyErrorInterceptor(timeoutError),
      );

      await expect(
        executeImport({ plugin_type: "email" }),
      ).rejects.toMatchObject({
        errors: [
          {
            code: "NETWORK_ERROR",
          },
        ],
        timestamp: expect.any(String),
      });
    });
  });
});

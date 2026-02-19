/**
 * PromptAPI テスト
 *
 * TDD: RED Phase - テスト先行
 * 要件: 1.1, 1.2, 2.2, 2.5, 3.1, 3.2, 3.4, 4.4
 */

import type {
  PromptResponse,
  PromptListResponse,
  TestPromptResult,
  LockResponse,
  PromptErrorResponse,
} from "../types/prompt";
import axios from "axios";
import {
  listPrompts,
  getPrompt,
  updatePrompt,
  testPrompt,
  resetPrompt,
  acquireLock,
  releaseLock,
} from "./promptApi";

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

// =============================================================================
// テストデータ
// =============================================================================

const mockPrompt: PromptResponse = {
  id: 1,
  key: "story_generation_system",
  name: "ストーリー生成システムプロンプト",
  description: "ストーリー生成に使用するシステムプロンプト",
  category: "story_generation",
  content:
    "以下の問い合わせから、ユーザーストーリーを生成してください。\n{inquiry_content}",
  default_content:
    "以下の問い合わせから、ユーザーストーリーを生成してください。\n{inquiry_content}",
  variables: ["inquiry_content", "template_content"],
  is_modified: false,
  editing_by: null,
  editing_since: null,
  created_at: "2024-01-01T00:00:00+00:00",
  updated_at: "2024-01-01T00:00:00+00:00",
};

const mockPrompt2: PromptResponse = {
  id: 2,
  key: "import_analysis_system",
  name: "インポート解析システムプロンプト",
  description: "インポート解析に使用するシステムプロンプト",
  category: "import_analysis",
  content: "以下の内容を解析してください。",
  default_content: "以下の内容を解析してください。",
  variables: ["content"],
  is_modified: false,
  editing_by: null,
  editing_since: null,
  created_at: "2024-01-01T00:00:00+00:00",
  updated_at: "2024-01-01T00:00:00+00:00",
};

describe("PromptAPI", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // =============================================================================
  // プロンプト一覧API（要件1.1, 1.3）
  // =============================================================================

  describe("プロンプト一覧API", () => {
    describe("listPrompts", () => {
      it("プロンプト一覧を取得できる", async () => {
        const mockResponse: PromptListResponse = {
          data: [mockPrompt, mockPrompt2],
          total: 2,
        };

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

        const result = await listPrompts();

        expect(mockAxiosInstance.get).toHaveBeenCalledWith("/api/prompts", {
          params: {},
        });
        expect(result.data).toHaveLength(2);
        expect(result.total).toBe(2);
        expect(result.data[0].key).toBe("story_generation_system");
        expect(result.data[1].key).toBe("import_analysis_system");
      });

      it("カテゴリでフィルタリングできる", async () => {
        const mockResponse: PromptListResponse = {
          data: [mockPrompt],
          total: 1,
        };

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

        const result = await listPrompts("story_generation");

        expect(mockAxiosInstance.get).toHaveBeenCalledWith("/api/prompts", {
          params: { category: "story_generation" },
        });
        expect(result.data).toHaveLength(1);
        expect(result.data[0].category).toBe("story_generation");
      });

      it("無効なカテゴリでエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-403",
              message: "無効なカテゴリです: invalid",
              field: "category",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 400,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.get.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(listPrompts("invalid" as any)).rejects.toEqual(
          errorResponse,
        );
      });

      it("サーバーエラー時にエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-010",
              message: "サーバーエラー",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 500,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.get.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(listPrompts()).rejects.toEqual(errorResponse);
      });
    });
  });

  // =============================================================================
  // プロンプト詳細API（要件1.2）
  // =============================================================================

  describe("プロンプト詳細API", () => {
    describe("getPrompt", () => {
      it("プロンプト詳細を取得できる", async () => {
        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockPrompt });

        const result = await getPrompt("story_generation_system");

        expect(mockAxiosInstance.get).toHaveBeenCalledWith(
          "/api/prompts/story_generation_system",
        );
        expect(result.key).toBe("story_generation_system");
        expect(result.name).toBe("ストーリー生成システムプロンプト");
        expect(result.variables).toEqual([
          "inquiry_content",
          "template_content",
        ]);
        expect(result.is_modified).toBe(false);
      });

      it("変更済みプロンプトの情報を取得できる", async () => {
        const modifiedPrompt: PromptResponse = {
          ...mockPrompt,
          content: "カスタムプロンプト内容",
          is_modified: true,
          updated_at: "2024-06-01T00:00:00+00:00",
        };

        mockAxiosInstance.get.mockResolvedValueOnce({ data: modifiedPrompt });

        const result = await getPrompt("story_generation_system");

        expect(result.is_modified).toBe(true);
        expect(result.content).toBe("カスタムプロンプト内容");
      });

      it("編集中のプロンプト情報を取得できる", async () => {
        const editingPrompt: PromptResponse = {
          ...mockPrompt,
          editing_by: "admin-user",
          editing_since: "2024-06-01T10:00:00+00:00",
        };

        mockAxiosInstance.get.mockResolvedValueOnce({ data: editingPrompt });

        const result = await getPrompt("story_generation_system");

        expect(result.editing_by).toBe("admin-user");
        expect(result.editing_since).toBe("2024-06-01T10:00:00+00:00");
      });

      it("存在しないプロンプトでエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-404",
              message: "プロンプトが見つかりません: unknown_key",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 404,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.get.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(getPrompt("unknown_key")).rejects.toEqual(errorResponse);
      });
    });
  });

  // =============================================================================
  // プロンプト更新API（要件2.2）
  // =============================================================================

  describe("プロンプト更新API", () => {
    describe("updatePrompt", () => {
      it("プロンプトを更新できる", async () => {
        const updatedPrompt: PromptResponse = {
          ...mockPrompt,
          content: "更新されたプロンプト内容\n{inquiry_content}",
          is_modified: true,
          updated_at: "2024-06-01T00:00:00+00:00",
        };

        mockAxiosInstance.put.mockResolvedValueOnce({ data: updatedPrompt });

        const result = await updatePrompt("story_generation_system", {
          content: "更新されたプロンプト内容\n{inquiry_content}",
        });

        expect(mockAxiosInstance.put).toHaveBeenCalledWith(
          "/api/prompts/story_generation_system",
          { content: "更新されたプロンプト内容\n{inquiry_content}" },
        );
        expect(result.content).toBe(
          "更新されたプロンプト内容\n{inquiry_content}",
        );
        expect(result.is_modified).toBe(true);
      });

      it("説明付きで更新できる", async () => {
        const updatedPrompt: PromptResponse = {
          ...mockPrompt,
          content: "新しい内容",
          description: "新しい説明",
          is_modified: true,
          updated_at: "2024-06-01T00:00:00+00:00",
        };

        mockAxiosInstance.put.mockResolvedValueOnce({ data: updatedPrompt });

        const result = await updatePrompt("story_generation_system", {
          content: "新しい内容",
          description: "新しい説明",
        });

        expect(mockAxiosInstance.put).toHaveBeenCalledWith(
          "/api/prompts/story_generation_system",
          { content: "新しい内容", description: "新しい説明" },
        );
        expect(result.description).toBe("新しい説明");
      });

      it("空の本文でバリデーションエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-401",
              message: "プロンプト本文が空です",
              field: "content",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 400,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.put.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(
          updatePrompt("story_generation_system", { content: "" }),
        ).rejects.toEqual(errorResponse);
      });

      it("存在しないプロンプトでエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-404",
              message: "プロンプトが見つかりません: unknown_key",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 404,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.put.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(
          updatePrompt("unknown_key", { content: "内容" }),
        ).rejects.toEqual(errorResponse);
      });

      it("編集ロック競合時にエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-405",
              message: "他のユーザーが編集中です",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 409,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.put.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(
          updatePrompt("story_generation_system", { content: "内容" }),
        ).rejects.toEqual(errorResponse);
      });
    });
  });

  // =============================================================================
  // テスト実行API（要件3.1, 3.2, 3.4）
  // =============================================================================

  describe("テスト実行API", () => {
    describe("testPrompt", () => {
      it("プロンプトをテスト実行できる", async () => {
        const mockResult: TestPromptResult = {
          output: "生成されたストーリー内容",
          provider: "openai",
          model: "gpt-4",
          elapsed_ms: 1500,
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult });

        const result = await testPrompt({
          content: "テストプロンプト {inquiry_content}",
          variables: { inquiry_content: "テスト問い合わせ" },
        });

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/prompts/test",
          {
            content: "テストプロンプト {inquiry_content}",
            variables: { inquiry_content: "テスト問い合わせ" },
          },
        );
        expect(result.output).toBe("生成されたストーリー内容");
        expect(result.provider).toBe("openai");
        expect(result.model).toBe("gpt-4");
        expect(result.elapsed_ms).toBe(1500);
      });

      it("AIプロバイダーを指定してテスト実行できる", async () => {
        const mockResult: TestPromptResult = {
          output: "Anthropicで生成された内容",
          provider: "anthropic",
          model: "claude-3-sonnet-20240229",
          elapsed_ms: 2000,
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResult });

        const result = await testPrompt({
          content: "テストプロンプト",
          variables: {},
          provider: "anthropic",
        });

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/prompts/test",
          {
            content: "テストプロンプト",
            variables: {},
            provider: "anthropic",
          },
        );
        expect(result.provider).toBe("anthropic");
      });

      it("タイムアウト時にエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-406",
              message: "テスト実行がタイムアウトしました（30秒）",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 504,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(
          testPrompt({
            content: "テストプロンプト",
            variables: {},
          }),
        ).rejects.toEqual(errorResponse);
      });

      it("AI API呼び出し失敗時にエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-407",
              message: "AI API呼び出しに失敗しました",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 500,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(
          testPrompt({
            content: "テストプロンプト",
            variables: {},
          }),
        ).rejects.toEqual(errorResponse);
      });
    });
  });

  // =============================================================================
  // デフォルトリセットAPI（要件4.4）
  // =============================================================================

  describe("デフォルトリセットAPI", () => {
    describe("resetPrompt", () => {
      it("プロンプトをデフォルトにリセットできる", async () => {
        const resetedPrompt: PromptResponse = {
          ...mockPrompt,
          content: mockPrompt.default_content,
          is_modified: false,
          updated_at: "2024-06-01T00:00:00+00:00",
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: resetedPrompt });

        const result = await resetPrompt("story_generation_system");

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/prompts/story_generation_system/reset",
        );
        expect(result.is_modified).toBe(false);
        expect(result.content).toBe(result.default_content);
      });

      it("存在しないプロンプトでエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-404",
              message: "プロンプトが見つかりません: unknown_key",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 404,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(resetPrompt("unknown_key")).rejects.toEqual(errorResponse);
      });
    });
  });

  // =============================================================================
  // 編集ロックAPI（要件2.5）
  // =============================================================================

  describe("編集ロックAPI", () => {
    describe("acquireLock", () => {
      it("編集ロックを取得できる", async () => {
        const mockLock: LockResponse = {
          acquired: true,
          locked_by: "admin-user",
          locked_since: "2024-06-01T10:00:00+00:00",
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockLock });

        const result = await acquireLock("story_generation_system", {
          user_id: "admin-user",
        });

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          "/api/prompts/story_generation_system/lock",
          { user_id: "admin-user" },
        );
        expect(result.acquired).toBe(true);
        expect(result.locked_by).toBe("admin-user");
      });

      it("他のユーザーが編集中の場合エラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-405",
              message: "他のユーザーが編集中です",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 409,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(
          acquireLock("story_generation_system", { user_id: "other-user" }),
        ).rejects.toEqual(errorResponse);
      });

      it("存在しないプロンプトでエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-404",
              message: "プロンプトが見つかりません: unknown_key",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 404,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.post.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(
          acquireLock("unknown_key", { user_id: "admin-user" }),
        ).rejects.toEqual(errorResponse);
      });
    });

    describe("releaseLock", () => {
      it("編集ロックを解放できる", async () => {
        mockAxiosInstance.delete.mockResolvedValueOnce({ status: 204 });

        await releaseLock("story_generation_system");

        expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
          "/api/prompts/story_generation_system/lock",
        );
      });

      it("存在しないプロンプトでエラーを返す", async () => {
        const errorResponse: PromptErrorResponse = {
          errors: [
            {
              code: "GS-404",
              message: "プロンプトが見つかりません: unknown_key",
            },
          ],
          timestamp: "2024-01-01T00:00:00+00:00",
        };

        const axiosError = {
          response: {
            status: 404,
            data: { detail: errorResponse },
          },
        };

        mockAxiosInstance.delete.mockImplementationOnce(() =>
          applyErrorInterceptor(axiosError),
        );

        await expect(releaseLock("unknown_key")).rejects.toEqual(errorResponse);
      });
    });
  });

  // =============================================================================
  // ネットワークエラー
  // =============================================================================

  describe("ネットワークエラー", () => {
    it("ネットワークエラー時に標準化されたエラーを返す", async () => {
      const networkError = {
        message: "Network Error",
      };

      mockAxiosInstance.get.mockImplementationOnce(() =>
        applyErrorInterceptor(networkError),
      );

      await expect(listPrompts()).rejects.toMatchObject({
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
      const timeoutError = {
        code: "ECONNABORTED",
        message: "timeout of 30000ms exceeded",
      };

      mockAxiosInstance.post.mockImplementationOnce(() =>
        applyErrorInterceptor(timeoutError),
      );

      await expect(
        testPrompt({
          content: "テストプロンプト",
          variables: {},
        }),
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

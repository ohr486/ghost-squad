/**
 * プロンプト管理機能 統合テスト（E2E）
 *
 * クリティカルパスの検証:
 * - 一覧表示 → 詳細遷移 → 編集 → 保存フロー
 * - テスト実行フロー（ローディング・結果表示・タイムアウト）
 * - デフォルトリセットフロー（確認ダイアログ・差分表示・リセット実行）
 *
 * 要件: 1.1, 1.2, 2.1, 2.2, 3.1, 3.3, 4.4, 4.6
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import toast from "react-hot-toast";
import PromptList from "./PromptList";
import PromptDetail from "./PromptDetail";
import * as promptApi from "../services/promptApi";
import { PromptResponse, TestPromptResult } from "../types/prompt";

// Mock APIs
jest.mock("../services/promptApi");
jest.mock("react-hot-toast");

const mockPromptApi = promptApi as jest.Mocked<typeof promptApi>;

describe("Prompt Integration Tests - Critical Paths", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    jest.clearAllMocks();
  });

  // テストデータ
  const mockPrompts: PromptResponse[] = [
    {
      id: 1,
      key: "story_generation_system",
      name: "ストーリー生成システムプロンプト",
      description: "ストーリー生成に使用するシステムプロンプト",
      category: "story_generation",
      content: "あなたはアジャイル開発の専門家です。",
      default_content: "あなたはアジャイル開発の専門家です。",
      variables: [],
      is_modified: false,
      editing_by: null,
      editing_since: null,
      created_at: "2024-01-01T10:00:00Z",
      updated_at: "2024-01-01T10:00:00Z",
    },
    {
      id: 2,
      key: "story_generation_user",
      name: "ストーリー生成ユーザープロンプト",
      description: "ユーザープロンプトテンプレート",
      category: "story_generation",
      content: "問い合わせ内容: {inquiry_content}",
      default_content: "問い合わせ内容: {inquiry_content}",
      variables: ["inquiry_content"],
      is_modified: false,
      editing_by: null,
      editing_since: null,
      created_at: "2024-01-01T10:00:00Z",
      updated_at: "2024-01-01T10:00:00Z",
    },
    {
      id: 3,
      key: "import_analysis_system",
      name: "インポート解析システムプロンプト",
      description: "解析用システムプロンプト",
      category: "import_analysis",
      content: "カスタマイズ済み解析プロンプト",
      default_content: "デフォルト解析プロンプト",
      variables: [],
      is_modified: true,
      editing_by: null,
      editing_since: null,
      created_at: "2024-01-01T11:00:00Z",
      updated_at: "2024-01-02T15:00:00Z",
    },
  ];

  const mockListResponse = {
    data: mockPrompts,
    total: 3,
  };

  /**
   * E2E テスト 1: 一覧表示 → 詳細遷移 → 編集 → 保存
   *
   * フロー: プロンプト一覧 → 行クリック → 詳細表示 → 編集ボタン → 内容変更 → 保存
   * 要件: 1.1, 1.2, 2.1, 2.2
   */
  describe("List → Detail → Edit → Save Flow", () => {
    test("navigates from list to detail via row click", async () => {
      // Arrange: 一覧APIモック
      mockPromptApi.listPrompts.mockResolvedValue(mockListResponse);

      const handlePromptClick = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <PromptList onPromptClick={handlePromptClick} />
        </QueryClientProvider>,
      );

      // Assert: 一覧が表示される
      await waitFor(() => {
        expect(
          screen.getByText("ストーリー生成システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Assert: 全プロンプトが表示される
      expect(
        screen.getByText("ストーリー生成ユーザープロンプト"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("インポート解析システムプロンプト"),
      ).toBeInTheDocument();

      // Act: 行をクリック
      await userEvent.click(
        screen.getByText("ストーリー生成システムプロンプト"),
      );

      // Assert: onPromptClickが正しいキーで呼ばれる
      expect(handlePromptClick).toHaveBeenCalledWith(
        "story_generation_system",
      );
    });

    test("displays prompt detail and enters edit mode", async () => {
      // Arrange: 詳細APIモック
      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[0]);
      mockPromptApi.acquireLock.mockResolvedValue({
        acquired: true,
        locked_by: "current_user",
        locked_since: "2024-01-01T10:00:00Z",
      });

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="story_generation_system" />
        </QueryClientProvider>,
      );

      // Assert: 詳細情報が表示される
      await waitFor(() => {
        expect(
          screen.getByText("ストーリー生成システムプロンプト"),
        ).toBeInTheDocument();
      });

      expect(
        screen.getByText("あなたはアジャイル開発の専門家です。"),
      ).toBeInTheDocument();

      // Act: 編集ボタンをクリック
      const editButton = screen.getByRole("button", { name: /編集/ });
      await userEvent.click(editButton);

      // Assert: ロック取得APIが呼ばれる
      await waitFor(() => {
        expect(mockPromptApi.acquireLock).toHaveBeenCalledWith(
          "story_generation_system",
          { user_id: "current_user" },
        );
      });

      // Assert: 編集モードのテキストエリアが表示される
      await waitFor(() => {
        expect(
          screen.getByLabelText("プロンプト本文を編集"),
        ).toBeInTheDocument();
      });
    });

    test("edits prompt content and saves successfully", async () => {
      // Arrange
      const updatedPrompt: PromptResponse = {
        ...mockPrompts[0],
        content: "更新後のシステムプロンプト",
        is_modified: true,
      };

      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[0]);
      mockPromptApi.acquireLock.mockResolvedValue({
        acquired: true,
        locked_by: "current_user",
        locked_since: "2024-01-01T10:00:00Z",
      });
      mockPromptApi.updatePrompt.mockResolvedValue(updatedPrompt);
      mockPromptApi.releaseLock.mockResolvedValue(undefined);

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="story_generation_system" />
        </QueryClientProvider>,
      );

      // Wait for detail to load
      await waitFor(() => {
        expect(
          screen.getByText("ストーリー生成システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Act: 編集モードに入る
      await userEvent.click(screen.getByRole("button", { name: /編集/ }));

      await waitFor(() => {
        expect(
          screen.getByLabelText("プロンプト本文を編集"),
        ).toBeInTheDocument();
      });

      // Act: テキストエリアの内容を変更
      const textarea = screen.getByLabelText("プロンプト本文を編集");
      await userEvent.clear(textarea);
      await userEvent.type(textarea, "更新後のシステムプロンプト");

      // Act: 保存ボタンをクリック
      const saveButton = screen.getByRole("button", { name: /保存/ });
      await userEvent.click(saveButton);

      // Assert: 更新APIが呼ばれる
      await waitFor(() => {
        expect(mockPromptApi.updatePrompt).toHaveBeenCalledWith(
          "story_generation_system",
          { content: "更新後のシステムプロンプト" },
        );
      });

      // Assert: 成功トーストが表示される
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("プロンプトを更新しました");
      });
    });

    test("cancels edit mode and releases lock", async () => {
      // Arrange
      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[0]);
      mockPromptApi.acquireLock.mockResolvedValue({
        acquired: true,
        locked_by: "current_user",
        locked_since: "2024-01-01T10:00:00Z",
      });
      mockPromptApi.releaseLock.mockResolvedValue(undefined);

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="story_generation_system" />
        </QueryClientProvider>,
      );

      await waitFor(() => {
        expect(
          screen.getByText("ストーリー生成システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Act: 編集モードに入る
      await userEvent.click(screen.getByRole("button", { name: /編集/ }));

      await waitFor(() => {
        expect(
          screen.getByLabelText("プロンプト本文を編集"),
        ).toBeInTheDocument();
      });

      // Act: キャンセルをクリック
      const cancelButton = screen.getByRole("button", { name: /キャンセル/ });
      await userEvent.click(cancelButton);

      // Assert: ロック解放APIが呼ばれる
      await waitFor(() => {
        expect(mockPromptApi.releaseLock).toHaveBeenCalledWith(
          "story_generation_system",
        );
      });
    });
  });

  /**
   * E2E テスト 2: テスト実行フロー
   *
   * フロー: 詳細表示 → 変数入力 → プロバイダー選択 → 実行 → 結果表示
   * 要件: 3.1, 3.3
   */
  describe("Test Execution Flow", () => {
    test("executes test with variables and displays result", async () => {
      // Arrange: 変数付きプロンプト
      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[1]);

      const mockTestResult: TestPromptResult = {
        output: "生成されたストーリー結果",
        provider: "openai",
        model: "gpt-4",
        elapsed_ms: 1500,
      };
      mockPromptApi.testPrompt.mockResolvedValue(mockTestResult);

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="story_generation_user" />
        </QueryClientProvider>,
      );

      // Assert: 詳細が表示される
      await waitFor(() => {
        expect(
          screen.getByText("ストーリー生成ユーザープロンプト"),
        ).toBeInTheDocument();
      });

      // Act: 変数に値を入力
      const variableInput = screen.getByLabelText("inquiry_content");
      await userEvent.type(variableInput, "ログイン機能を改善したい");

      // Act: プロバイダーを選択
      const providerSelect = screen.getByLabelText("AIプロバイダー");
      await userEvent.selectOptions(providerSelect, "openai");

      // Act: 実行ボタンをクリック
      const executeButton = screen.getByRole("button", { name: /実行/ });
      await userEvent.click(executeButton);

      // Assert: テスト実行APIが呼ばれる
      await waitFor(() => {
        expect(mockPromptApi.testPrompt).toHaveBeenCalledWith(
          expect.objectContaining({
            content: "問い合わせ内容: {inquiry_content}",
            variables: { inquiry_content: "ログイン機能を改善したい" },
            provider: "openai",
          }),
        );
      });

      // Assert: テスト結果が表示される
      await waitFor(() => {
        expect(
          screen.getByText("生成されたストーリー結果"),
        ).toBeInTheDocument();
      });

      expect(screen.getByText(/openai/)).toBeInTheDocument();
      expect(screen.getByText(/gpt-4/)).toBeInTheDocument();
      expect(screen.getByText(/1500ms/)).toBeInTheDocument();
    });

    test("shows loading state during test execution", async () => {
      // Arrange: 遅延レスポンス
      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[0]);
      mockPromptApi.testPrompt.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  output: "結果",
                  provider: "openai",
                  model: "gpt-4",
                  elapsed_ms: 5000,
                }),
              100,
            ),
          ),
      );

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="story_generation_system" />
        </QueryClientProvider>,
      );

      await waitFor(() => {
        expect(
          screen.getByText("ストーリー生成システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Act: 実行ボタンをクリック
      const executeButton = screen.getByRole("button", { name: /実行/ });
      await userEvent.click(executeButton);

      // Assert: ローディング状態が表示される
      expect(screen.getByText("実行中...")).toBeInTheDocument();

      // Assert: 結果が表示されてローディングが終了
      await waitFor(() => {
        expect(screen.getByText("結果")).toBeInTheDocument();
      });
    });

    test("shows error toast on test execution failure", async () => {
      // Arrange
      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[0]);
      mockPromptApi.testPrompt.mockRejectedValue(
        new Error("GS-406: タイムアウト"),
      );

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="story_generation_system" />
        </QueryClientProvider>,
      );

      await waitFor(() => {
        expect(
          screen.getByText("ストーリー生成システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Act: 実行ボタンをクリック
      const executeButton = screen.getByRole("button", { name: /実行/ });
      await userEvent.click(executeButton);

      // Assert: エラートーストが表示される
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith("テスト実行に失敗しました");
      });
    });
  });

  /**
   * E2E テスト 3: デフォルトリセットフロー
   *
   * フロー: 変更済みプロンプト詳細 → リセットボタン → 確認ダイアログ → 差分表示 → リセット実行
   * 要件: 4.4, 4.6
   */
  describe("Default Reset Flow", () => {
    test("shows reset button only for modified prompts", async () => {
      // Arrange: 変更済みプロンプト
      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[2]);

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="import_analysis_system" />
        </QueryClientProvider>,
      );

      await waitFor(() => {
        expect(
          screen.getByText("インポート解析システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Assert: 変更済みバッジが表示される
      expect(screen.getByText("変更済み")).toBeInTheDocument();

      // Assert: リセットボタンが表示される
      expect(
        screen.getByRole("button", { name: /デフォルトにリセット/ }),
      ).toBeInTheDocument();
    });

    test("hides reset button for unmodified prompts", async () => {
      // Arrange: 未変更プロンプト
      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[0]);

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="story_generation_system" />
        </QueryClientProvider>,
      );

      await waitFor(() => {
        expect(
          screen.getByText("ストーリー生成システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Assert: リセットボタンが非表示
      expect(
        screen.queryByRole("button", { name: /デフォルトにリセット/ }),
      ).not.toBeInTheDocument();
    });

    test("shows confirmation dialog with diff when reset clicked", async () => {
      // Arrange: 変更済みプロンプト
      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[2]);

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="import_analysis_system" />
        </QueryClientProvider>,
      );

      await waitFor(() => {
        expect(
          screen.getByText("インポート解析システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Act: リセットボタンをクリック
      await userEvent.click(
        screen.getByRole("button", { name: /デフォルトにリセット/ }),
      );

      // Assert: 確認ダイアログが表示される
      expect(
        screen.getByText("デフォルトにリセットしますか？"),
      ).toBeInTheDocument();

      // Assert: 現在の内容とデフォルト内容が差分表示される
      expect(screen.getByText("現在の内容:")).toBeInTheDocument();
      // プロンプト本文セクションとダイアログの両方に表示されるためgetAllByTextを使用
      const currentContentElements = screen.getAllByText(
        "カスタマイズ済み解析プロンプト",
      );
      expect(currentContentElements.length).toBeGreaterThanOrEqual(2);
      expect(screen.getByText("デフォルト内容:")).toBeInTheDocument();
      expect(
        screen.getByText("デフォルト解析プロンプト"),
      ).toBeInTheDocument();
    });

    test("executes reset and shows success message", async () => {
      // Arrange
      const resetPrompt: PromptResponse = {
        ...mockPrompts[2],
        content: "デフォルト解析プロンプト",
        is_modified: false,
      };

      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[2]);
      mockPromptApi.resetPrompt.mockResolvedValue(resetPrompt);

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="import_analysis_system" />
        </QueryClientProvider>,
      );

      await waitFor(() => {
        expect(
          screen.getByText("インポート解析システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Act: リセットボタン → 確認ダイアログ
      await userEvent.click(
        screen.getByRole("button", { name: /デフォルトにリセット/ }),
      );

      // Assert: ダイアログが表示される
      expect(
        screen.getByText("デフォルトにリセットしますか？"),
      ).toBeInTheDocument();

      // Act: リセット実行ボタンをクリック
      await userEvent.click(
        screen.getByRole("button", { name: /リセット実行/ }),
      );

      // Assert: リセットAPIが呼ばれる
      await waitFor(() => {
        expect(mockPromptApi.resetPrompt).toHaveBeenCalledWith(
          "import_analysis_system",
        );
      });

      // Assert: 成功トーストが表示される
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(
          "プロンプトをデフォルトにリセットしました",
        );
      });
    });

    test("cancels reset dialog without executing reset", async () => {
      // Arrange
      mockPromptApi.getPrompt.mockResolvedValue(mockPrompts[2]);

      render(
        <QueryClientProvider client={queryClient}>
          <PromptDetail promptKey="import_analysis_system" />
        </QueryClientProvider>,
      );

      await waitFor(() => {
        expect(
          screen.getByText("インポート解析システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Act: リセットボタン → ダイアログ表示
      await userEvent.click(
        screen.getByRole("button", { name: /デフォルトにリセット/ }),
      );

      expect(
        screen.getByText("デフォルトにリセットしますか？"),
      ).toBeInTheDocument();

      // Act: キャンセルボタンをクリック
      await userEvent.click(
        screen.getByRole("button", { name: /キャンセル/ }),
      );

      // Assert: ダイアログが閉じる
      await waitFor(() => {
        expect(
          screen.queryByText("デフォルトにリセットしますか？"),
        ).not.toBeInTheDocument();
      });

      // Assert: リセットAPIは呼ばれない
      expect(mockPromptApi.resetPrompt).not.toHaveBeenCalled();
    });
  });

  /**
   * E2E テスト 4: カテゴリフィルタリングフロー
   *
   * フロー: 一覧表示 → カテゴリフィルター選択 → フィルタリング結果表示
   * 要件: 1.1
   */
  describe("Category Filtering Flow", () => {
    test("filters prompts by category selection", async () => {
      mockPromptApi.listPrompts.mockResolvedValue(mockListResponse);

      const handlePromptClick = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <PromptList onPromptClick={handlePromptClick} />
        </QueryClientProvider>,
      );

      // Assert: 全プロンプトが表示される
      await waitFor(() => {
        expect(
          screen.getByText("ストーリー生成システムプロンプト"),
        ).toBeInTheDocument();
      });

      // Act: カテゴリフィルターを選択
      const filterSelect = screen.getByLabelText("カテゴリフィルター");
      await userEvent.selectOptions(filterSelect, "import_analysis");

      // Assert: フィルターAPIが呼ばれる
      await waitFor(() => {
        expect(mockPromptApi.listPrompts).toHaveBeenCalledWith(
          "import_analysis",
        );
      });
    });
  });
});

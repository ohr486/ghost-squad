/**
 * Importer機能 統合テスト（E2E）
 *
 * クリティカルパスの検証:
 * - インポート実行フロー（プラグイン選択 → AIプロバイダー選択 → 実行 → 結果確認）
 * - プラグイン有効/無効切り替えフロー（トグル → API呼び出し → 一覧更新）
 * - AIプロバイダーデフォルト設定フロー（ラジオ選択 → API呼び出し → 一覧更新）
 * - エラー発生時のUI状態遷移
 *
 * 要件: 1.1, 1.2, 2.1, 2.2, 3.1, 4.1, 5.4
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ImporterPage from "./ImporterPage";
import * as importerApi from "../../services/importerApi";
import type {
  PluginListResponse,
  AIProviderListResponse,
  ErrorStatsListResponse,
  ImportResult,
  PluginStatus,
  AIProviderStatus,
} from "../../types/importer";

// Mock APIs
jest.mock("../../services/importerApi");

const mockedListPlugins = importerApi.listPlugins as jest.MockedFunction<
  typeof importerApi.listPlugins
>;
const mockedListAIProviders =
  importerApi.listAIProviders as jest.MockedFunction<
    typeof importerApi.listAIProviders
  >;
const mockedGetErrorStats = importerApi.getErrorStats as jest.MockedFunction<
  typeof importerApi.getErrorStats
>;
const mockedExecuteImport = importerApi.executeImport as jest.MockedFunction<
  typeof importerApi.executeImport
>;
const mockedEnablePlugin = importerApi.enablePlugin as jest.MockedFunction<
  typeof importerApi.enablePlugin
>;
const mockedDisablePlugin = importerApi.disablePlugin as jest.MockedFunction<
  typeof importerApi.disablePlugin
>;
const mockedSetDefaultAIProvider =
  importerApi.setDefaultAIProvider as jest.MockedFunction<
    typeof importerApi.setDefaultAIProvider
  >;

describe("Importer Integration Tests - Critical Paths", () => {
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
  const mockPlugins: PluginListResponse = {
    data: [
      {
        plugin_type: "email",
        enabled: true,
        initialized: true,
        error_message: null,
      },
      {
        plugin_type: "sentry",
        enabled: false,
        initialized: true,
        error_message: null,
      },
    ],
    timestamp: "2025-12-01T00:00:00Z",
  };

  const mockProviders: AIProviderListResponse = {
    data: [
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
    ],
    timestamp: "2025-12-01T00:00:00Z",
  };

  const mockErrorStats: ErrorStatsListResponse = {
    data: [],
    timestamp: "2025-12-01T00:00:00Z",
  };

  const mockImportResult: ImportResult = {
    total_fetched: 10,
    total_imported: 8,
    total_skipped: 1,
    total_failed: 1,
    imported_inquiry_ids: [1, 2, 3, 4, 5, 6, 7, 8],
    errors: [
      {
        source_id: "message-id-123",
        error_code: "GS-304",
        error_message: "AI解析に失敗しました",
      },
    ],
    timestamp: "2025-12-01T00:00:00Z",
  };

  const renderPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ImporterPage />
      </QueryClientProvider>,
    );
  };

  /**
   * E2E テスト 1: インポート実行フロー
   *
   * フロー: ImporterPage → プラグイン選択 → インポート実行 → 結果表示
   * 要件: 2.1, 2.2, 4.1
   */
  describe("Import Execution Flow", () => {
    beforeEach(() => {
      mockedListPlugins.mockResolvedValue(mockPlugins);
      mockedListAIProviders.mockResolvedValue(mockProviders);
      mockedGetErrorStats.mockResolvedValue(mockErrorStats);
    });

    test("executes import with plugin selection and displays results", async () => {
      mockedExecuteImport.mockResolvedValue(mockImportResult);

      renderPage();

      // Assert: データソース選択が表示されるまで待機（ローディング完了）
      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      // Assert: インポート実行セクションが表示される
      expect(
        screen.getByRole("heading", { level: 2, name: "インポート実行" }),
      ).toBeInTheDocument();

      // Act: プラグインを選択
      const pluginSelect = screen.getByLabelText("データソース");
      await userEvent.selectOptions(pluginSelect, "email");

      // Assert: 実行ボタンが有効化される
      const executeButton = screen.getByRole("button", {
        name: "インポート実行",
      });
      expect(executeButton).not.toBeDisabled();

      // Act: インポート実行
      await userEvent.click(executeButton);

      // Assert: APIが呼ばれる
      await waitFor(() => {
        expect(mockedExecuteImport).toHaveBeenCalled();
      });

      // Assert: APIの引数を確認
      expect(mockedExecuteImport.mock.calls[0][0]).toEqual({
        plugin_type: "email",
        ai_provider_type: null,
      });

      // Assert: 結果が表示される
      await waitFor(() => {
        expect(screen.getByText("実行結果")).toBeInTheDocument();
      });

      // Assert: 結果サマリーの確認
      expect(screen.getByText("取得件数")).toBeInTheDocument();
      expect(screen.getByText("10")).toBeInTheDocument();
      expect(screen.getByText("インポート成功")).toBeInTheDocument();
      expect(screen.getByText("8")).toBeInTheDocument();
    });

    test("executes import with AI provider selection", async () => {
      mockedExecuteImport.mockResolvedValue(mockImportResult);

      renderPage();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      // Act: プラグインとAIプロバイダーを選択
      const pluginSelect = screen.getByLabelText("データソース");
      await userEvent.selectOptions(pluginSelect, "email");

      const providerSelect =
        screen.getByLabelText("AIプロバイダー（オプション）");
      await userEvent.selectOptions(providerSelect, "anthropic");

      // Act: インポート実行
      const executeButton = screen.getByRole("button", {
        name: "インポート実行",
      });
      await userEvent.click(executeButton);

      // Assert: APIが呼ばれる
      await waitFor(() => {
        expect(mockedExecuteImport).toHaveBeenCalled();
      });

      // Assert: AIプロバイダーが指定されてAPIが呼ばれる
      expect(mockedExecuteImport.mock.calls[0][0]).toEqual({
        plugin_type: "email",
        ai_provider_type: "anthropic",
      });
    });

    test("displays error details when import has failures", async () => {
      mockedExecuteImport.mockResolvedValue(mockImportResult);

      renderPage();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const pluginSelect = screen.getByLabelText("データソース");
      await userEvent.selectOptions(pluginSelect, "email");

      const executeButton = screen.getByRole("button", {
        name: "インポート実行",
      });
      await userEvent.click(executeButton);

      // Assert: エラー詳細が表示される
      await waitFor(() => {
        expect(screen.getByText("エラー詳細")).toBeInTheDocument();
      });

      expect(screen.getByText("AI解析に失敗しました")).toBeInTheDocument();
      expect(screen.getByText("[GS-304]")).toBeInTheDocument();
    });

    test("shows loading state during import execution", async () => {
      mockedExecuteImport.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockImportResult), 100),
          ),
      );

      renderPage();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const pluginSelect = screen.getByLabelText("データソース");
      await userEvent.selectOptions(pluginSelect, "email");

      const executeButton = screen.getByRole("button", {
        name: "インポート実行",
      });
      await userEvent.click(executeButton);

      // Assert: ローディング状態が表示される
      expect(screen.getByText("実行中...")).toBeInTheDocument();
      expect(executeButton).toBeDisabled();

      // Assert: 完了後にローディングが解除される
      await waitFor(() => {
        expect(screen.queryByText("実行中...")).not.toBeInTheDocument();
      });
    });
  });

  /**
   * E2E テスト 2: プラグイン有効/無効切り替えフロー
   *
   * フロー: プラグイン一覧 → トグル切り替え → API呼び出し → 一覧更新
   * 要件: 1.1, 1.2
   */
  describe("Plugin Toggle Flow", () => {
    beforeEach(() => {
      mockedListPlugins.mockResolvedValue(mockPlugins);
      mockedListAIProviders.mockResolvedValue(mockProviders);
      mockedGetErrorStats.mockResolvedValue(mockErrorStats);
    });

    test("enables plugin through toggle switch", async () => {
      const enabledPlugin: PluginStatus = {
        plugin_type: "sentry",
        enabled: true,
        initialized: true,
        error_message: null,
      };
      mockedEnablePlugin.mockResolvedValue(enabledPlugin);

      renderPage();

      // Assert: プラグイン一覧が表示されるまで待機
      await waitFor(() => {
        expect(screen.getByText("sentry")).toBeInTheDocument();
      });

      // Assert: sentryプラグインが無効状態
      const sentryToggle = screen.getByRole("checkbox", {
        name: "sentryプラグインの有効/無効切り替え",
      });
      expect(sentryToggle).not.toBeChecked();

      // Act: トグルをクリックして有効化
      await userEvent.click(sentryToggle);

      // Assert: API呼び出しを確認
      await waitFor(() => {
        expect(mockedEnablePlugin).toHaveBeenCalled();
      });
      expect(mockedEnablePlugin.mock.calls[0][0]).toBe("sentry");
    });

    test("disables plugin through toggle switch", async () => {
      const disabledPlugin: PluginStatus = {
        plugin_type: "email",
        enabled: false,
        initialized: true,
        error_message: null,
      };
      mockedDisablePlugin.mockResolvedValue(disabledPlugin);

      renderPage();

      // Wait for the checkbox to appear (more specific selector)
      await waitFor(() => {
        expect(
          screen.getByRole("checkbox", {
            name: "emailプラグインの有効/無効切り替え",
          }),
        ).toBeInTheDocument();
      });

      // Act: emailプラグインのトグルをクリックして無効化
      const emailToggle = screen.getByRole("checkbox", {
        name: "emailプラグインの有効/無効切り替え",
      });
      expect(emailToggle).toBeChecked();

      await userEvent.click(emailToggle);

      // Assert: API呼び出しを確認
      await waitFor(() => {
        expect(mockedDisablePlugin).toHaveBeenCalled();
      });
      expect(mockedDisablePlugin.mock.calls[0][0]).toBe("email");
    });

    test("shows error message when toggle operation fails", async () => {
      mockedEnablePlugin.mockRejectedValue({
        errors: [
          {
            code: "GS-302",
            message: "プラグインの初期化に失敗しました",
          },
        ],
        timestamp: "2025-12-01T00:00:00Z",
      });

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("sentry")).toBeInTheDocument();
      });

      const sentryToggle = screen.getByRole("checkbox", {
        name: "sentryプラグインの有効/無効切り替え",
      });
      await userEvent.click(sentryToggle);

      // Assert: エラーメッセージが表示される
      await waitFor(() => {
        expect(
          screen.getByText("プラグインの初期化に失敗しました"),
        ).toBeInTheDocument();
      });
    });

    test("disables toggle during operation", async () => {
      mockedEnablePlugin.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  plugin_type: "sentry",
                  enabled: true,
                  initialized: true,
                  error_message: null,
                }),
              100,
            ),
          ),
      );

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("sentry")).toBeInTheDocument();
      });

      const sentryToggle = screen.getByRole("checkbox", {
        name: "sentryプラグインの有効/無効切り替え",
      });
      await userEvent.click(sentryToggle);

      // Assert: ローディング中はトグルが無効化される
      expect(sentryToggle).toBeDisabled();

      await waitFor(() => {
        expect(sentryToggle).not.toBeDisabled();
      });
    });
  });

  /**
   * E2E テスト 3: AIプロバイダーデフォルト設定フロー
   *
   * フロー: AIプロバイダー一覧 → ラジオ選択 → API呼び出し → 一覧更新
   * 要件: 3.1
   */
  describe("AI Provider Default Setting Flow", () => {
    beforeEach(() => {
      mockedListPlugins.mockResolvedValue(mockPlugins);
      mockedListAIProviders.mockResolvedValue(mockProviders);
      mockedGetErrorStats.mockResolvedValue(mockErrorStats);
    });

    test("sets default AI provider through radio selection", async () => {
      const updatedProvider: AIProviderStatus = {
        provider_type: "anthropic",
        enabled: true,
        initialized: true,
        is_default: true,
        model: "claude-3-sonnet-20240229",
        error_message: null,
      };
      mockedSetDefaultAIProvider.mockResolvedValue(updatedProvider);

      renderPage();

      // Assert: AIプロバイダー一覧が表示される
      await waitFor(() => {
        expect(screen.getByText("openai")).toBeInTheDocument();
      });

      // Assert: openaiがデフォルト
      const openaiRadio = screen.getByRole("radio", {
        name: "openaiをデフォルトに設定",
      });
      expect(openaiRadio).toBeChecked();

      // Act: anthropicをデフォルトに設定
      const anthropicRadio = screen.getByRole("radio", {
        name: "anthropicをデフォルトに設定",
      });
      await userEvent.click(anthropicRadio);

      // Assert: API呼び出しを確認
      await waitFor(() => {
        expect(mockedSetDefaultAIProvider).toHaveBeenCalled();
      });
      expect(mockedSetDefaultAIProvider.mock.calls[0][0]).toBe("anthropic");
    });

    test("shows error message when setting default fails", async () => {
      mockedSetDefaultAIProvider.mockRejectedValue({
        errors: [
          {
            code: "GS-309",
            message: "AIプロバイダーの設定に失敗しました",
          },
        ],
        timestamp: "2025-12-01T00:00:00Z",
      });

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("anthropic")).toBeInTheDocument();
      });

      const anthropicRadio = screen.getByRole("radio", {
        name: "anthropicをデフォルトに設定",
      });
      await userEvent.click(anthropicRadio);

      // Assert: エラーメッセージが表示される
      await waitFor(() => {
        expect(
          screen.getByText("AIプロバイダーの設定に失敗しました"),
        ).toBeInTheDocument();
      });
    });
  });

  /**
   * E2E テスト 4: エラー統計表示
   *
   * フロー: ページ読み込み → エラー統計取得 → テーブル表示
   * 要件: 5.4
   */
  describe("Error Statistics Display", () => {
    test("displays error statistics when errors exist", async () => {
      const errorStatsWithData: ErrorStatsListResponse = {
        data: [
          {
            error_code: "GS-303",
            count: 5,
            last_occurred: "2025-12-01T10:30:00Z",
          },
          {
            error_code: "GS-304",
            count: 3,
            last_occurred: "2025-12-01T09:15:00Z",
          },
        ],
        timestamp: "2025-12-01T00:00:00Z",
      };
      mockedListPlugins.mockResolvedValue(mockPlugins);
      mockedListAIProviders.mockResolvedValue(mockProviders);
      mockedGetErrorStats.mockResolvedValue(errorStatsWithData);

      renderPage();

      // Assert: エラー統計セクションが表示される
      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "エラー統計" }),
        ).toBeInTheDocument();
      });

      // Assert: エラーコードが表示される
      expect(screen.getByText("GS-303")).toBeInTheDocument();
      expect(screen.getByText("GS-304")).toBeInTheDocument();

      // Assert: 発生回数が表示される
      expect(screen.getByText("5")).toBeInTheDocument();
      expect(screen.getByText("3")).toBeInTheDocument();
    });

    test("displays no errors message when no errors exist", async () => {
      mockedListPlugins.mockResolvedValue(mockPlugins);
      mockedListAIProviders.mockResolvedValue(mockProviders);
      mockedGetErrorStats.mockResolvedValue(mockErrorStats);

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("エラーはありません")).toBeInTheDocument();
      });
    });
  });

  /**
   * E2E テスト 5: エラー発生時のUI状態遷移
   *
   * フロー: インポート実行 → API失敗 → エラーメッセージ表示 → 再実行可能
   * 要件: 4.1, 5.4
   */
  describe("Error State Transitions", () => {
    beforeEach(() => {
      mockedListPlugins.mockResolvedValue(mockPlugins);
      mockedListAIProviders.mockResolvedValue(mockProviders);
      mockedGetErrorStats.mockResolvedValue(mockErrorStats);
    });

    test("displays error message and allows retry after import failure", async () => {
      // 最初は失敗、2回目は成功
      mockedExecuteImport
        .mockRejectedValueOnce({
          errors: [
            {
              code: "GS-303",
              message: "メールサーバーへの接続に失敗しました",
            },
          ],
          timestamp: "2025-12-01T00:00:00Z",
        })
        .mockResolvedValueOnce({
          ...mockImportResult,
          total_failed: 0,
          errors: [],
        });

      renderPage();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      // Act: プラグイン選択とインポート実行
      const pluginSelect = screen.getByLabelText("データソース");
      await userEvent.selectOptions(pluginSelect, "email");

      const executeButton = screen.getByRole("button", {
        name: "インポート実行",
      });
      await userEvent.click(executeButton);

      // Assert: エラーメッセージが表示される
      await waitFor(() => {
        expect(
          screen.getByText("メールサーバーへの接続に失敗しました"),
        ).toBeInTheDocument();
      });

      // Assert: 実行ボタンは有効のまま（再試行可能）
      expect(executeButton).not.toBeDisabled();

      // Act: 再実行
      await userEvent.click(executeButton);

      // Assert: 2回目は成功
      await waitFor(() => {
        expect(screen.getByText("実行結果")).toBeInTheDocument();
      });
    });

    test("clears previous result when starting new import", async () => {
      mockedExecuteImport.mockResolvedValue(mockImportResult);

      renderPage();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      // Act: 1回目のインポート実行
      const pluginSelect = screen.getByLabelText("データソース");
      await userEvent.selectOptions(pluginSelect, "email");

      const executeButton = screen.getByRole("button", {
        name: "インポート実行",
      });
      await userEvent.click(executeButton);

      await waitFor(() => {
        expect(screen.getByText("実行結果")).toBeInTheDocument();
      });

      // Assert: 1回目の結果が表示される（エラー詳細があることを確認）
      expect(screen.getByText("エラー詳細")).toBeInTheDocument();

      // Act: 2回目のインポート実行（結果がクリアされることを確認）
      const successOnlyResult: ImportResult = {
        total_fetched: 25,
        total_imported: 23,
        total_skipped: 2,
        total_failed: 0,
        imported_inquiry_ids: [9, 10, 11, 12, 13],
        errors: [],
        timestamp: "2025-12-01T00:00:00Z",
      };
      mockedExecuteImport.mockResolvedValue(successOnlyResult);

      await userEvent.click(executeButton);

      // Assert: 新しい結果が表示される（25という数値は2回目のみ）
      await waitFor(() => {
        expect(screen.getByText("25")).toBeInTheDocument(); // total_fetched
      });

      // Assert: 前回のエラー詳細が表示されない
      expect(screen.queryByText("エラー詳細")).not.toBeInTheDocument();
    });
  });

  /**
   * E2E テスト 6: 全セクションの統合表示
   *
   * フロー: ページ読み込み → 全セクション表示確認
   * 要件: MVP UI
   */
  describe("Full Page Integration", () => {
    beforeEach(() => {
      mockedListPlugins.mockResolvedValue(mockPlugins);
      mockedListAIProviders.mockResolvedValue(mockProviders);
      mockedGetErrorStats.mockResolvedValue(mockErrorStats);
    });

    test("displays all sections on page load", async () => {
      renderPage();

      // Assert: データがロードされるまで待機
      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      // Assert: 全セクションが表示される（getAllByTextで複数要素対応）
      expect(screen.getByText("インポーター管理")).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { level: 2, name: "インポート実行" }),
      ).toBeInTheDocument();
      expect(screen.getByText("データソースプラグイン")).toBeInTheDocument();
      expect(screen.getByText("AIプロバイダー")).toBeInTheDocument();
      expect(screen.getByText("エラー統計")).toBeInTheDocument();
    });

    test("plugin selection in executor reflects plugins from list", async () => {
      renderPage();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      // Assert: プラグイン一覧に表示されているプラグインがドロップダウンにも表示される
      const pluginSelect = screen.getByLabelText(
        "データソース",
      ) as HTMLSelectElement;

      // email（有効）がオプションにある
      const options = Array.from(pluginSelect.options).map(
        (opt) => opt.textContent,
      );
      expect(options).toContain("email");

      // プラグイン一覧にも同じプラグインが表示される（emailは複数箇所に表示される）
      const emailElements = screen.getAllByText("email");
      expect(emailElements.length).toBeGreaterThanOrEqual(1);
    });

    test("AI provider selection in executor reflects providers from list", async () => {
      renderPage();

      await waitFor(() => {
        expect(
          screen.getByLabelText("AIプロバイダー（オプション）"),
        ).toBeInTheDocument();
      });

      // Assert: AIプロバイダー一覧に表示されているプロバイダーがドロップダウンにも表示される
      const providerSelect = screen.getByLabelText(
        "AIプロバイダー（オプション）",
      ) as HTMLSelectElement;

      const options = Array.from(providerSelect.options).map(
        (opt) => opt.textContent,
      );
      expect(options).toContain("openai");
      expect(options).toContain("anthropic");

      // AIプロバイダー一覧にも同じプロバイダーが表示される（複数箇所に表示される）
      const openaiElements = screen.getAllByText("openai");
      expect(openaiElements.length).toBeGreaterThanOrEqual(1);
      const anthropicElements = screen.getAllByText("anthropic");
      expect(anthropicElements.length).toBeGreaterThanOrEqual(1);
    });
  });

  /**
   * E2E テスト 7: 無効なプラグイン・プロバイダーの除外
   *
   * 無効化されたプラグインはインポート実行のドロップダウンに表示されない
   * 要件: 1.1, 1.2
   */
  describe("Disabled Plugin/Provider Exclusion", () => {
    test("excludes disabled plugins from import executor dropdown", async () => {
      mockedListPlugins.mockResolvedValue(mockPlugins);
      mockedListAIProviders.mockResolvedValue(mockProviders);
      mockedGetErrorStats.mockResolvedValue(mockErrorStats);

      renderPage();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const pluginSelect = screen.getByLabelText(
        "データソース",
      ) as HTMLSelectElement;

      // Assert: enabled=trueのemailのみがオプションに表示される
      // HTMLSelectElementのoptionsプロパティを使用
      const optionTexts = Array.from(pluginSelect.options).map(
        (opt) => opt.textContent,
      );
      expect(optionTexts).toContain("email");

      // Assert: enabled=falseのsentryはオプションに表示されない
      expect(optionTexts).not.toContain("sentry");
    });

    test("excludes uninitialized plugins from import executor dropdown", async () => {
      const pluginsWithUninitialized: PluginListResponse = {
        data: [
          {
            plugin_type: "email",
            enabled: true,
            initialized: true,
            error_message: null,
          },
          {
            plugin_type: "broken",
            enabled: true,
            initialized: false,
            error_message: "初期化に失敗しました",
          },
        ],
        timestamp: "2025-12-01T00:00:00Z",
      };
      mockedListPlugins.mockResolvedValue(pluginsWithUninitialized);
      mockedListAIProviders.mockResolvedValue(mockProviders);
      mockedGetErrorStats.mockResolvedValue(mockErrorStats);

      renderPage();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const pluginSelect = screen.getByLabelText(
        "データソース",
      ) as HTMLSelectElement;

      // Assert: initialized=falseのbrokenはオプションに表示されない
      // HTMLSelectElementのoptionsプロパティを使用
      const optionTexts = Array.from(pluginSelect.options).map(
        (opt) => opt.textContent,
      );
      expect(optionTexts).toContain("email");
      expect(optionTexts).not.toContain("broken");
    });
  });
});

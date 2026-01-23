/**
 * ImportExecutorComponent コンポーネントテスト
 *
 * TDD: REDフェーズ - テストを先に作成
 * 要件: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ImportExecutorComponent from "./ImportExecutorComponent";
import * as importerApi from "../../services/importerApi";
import type {
  PluginListResponse,
  AIProviderListResponse,
  ImportResult,
} from "../../types/importer";

// Mock importer API
jest.mock("../../services/importerApi");
const mockedListPlugins = importerApi.listPlugins as jest.MockedFunction<
  typeof importerApi.listPlugins
>;
const mockedListAIProviders =
  importerApi.listAIProviders as jest.MockedFunction<
    typeof importerApi.listAIProviders
  >;
const mockedExecuteImport = importerApi.executeImport as jest.MockedFunction<
  typeof importerApi.executeImport
>;

describe("ImportExecutorComponent", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    jest.clearAllMocks();
  });

  const mockPluginsData: PluginListResponse = {
    data: [
      {
        plugin_type: "email",
        enabled: true,
        initialized: true,
        error_message: null,
      },
      {
        plugin_type: "sentry",
        enabled: true,
        initialized: true,
        error_message: null,
      },
    ],
    timestamp: "2025-12-01T00:00:00Z",
  };

  const mockProvidersData: AIProviderListResponse = {
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

  const mockImportResult: ImportResult = {
    total_fetched: 10,
    total_imported: 7,
    total_skipped: 2,
    total_failed: 1,
    imported_inquiry_ids: [1, 2, 3, 4, 5, 6, 7],
    errors: [
      {
        source_id: "message-id-123",
        error_code: "GS-304",
        error_message: "AI解析に失敗しました",
      },
    ],
    timestamp: "2025-12-01T00:00:00Z",
  };

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ImportExecutorComponent />
      </QueryClientProvider>,
    );
  };

  describe("ローディング状態", () => {
    it("プラグイン一覧取得中にローディングメッセージを表示する", async () => {
      mockedListPlugins.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockPluginsData), 100),
          ),
      );
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      expect(screen.getByText("読み込み中...")).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByText("読み込み中...")).not.toBeInTheDocument();
      });
    });
  });

  describe("エラー状態", () => {
    it("プラグイン一覧取得エラー時にエラーメッセージを表示する", async () => {
      mockedListPlugins.mockRejectedValue(new Error("プラグイン取得に失敗"));
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText(/プラグイン取得に失敗/i)).toBeInTheDocument();
      });
    });
  });

  describe("フォーム表示", () => {
    beforeEach(() => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);
      mockedListAIProviders.mockResolvedValue(mockProvidersData);
    });

    it("セクション見出しが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "インポート実行" }),
        ).toBeInTheDocument();
      });
    });

    it("データソース選択ドロップダウンが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });
    });

    it("データソースドロップダウンにプラグイン一覧が表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("email")).toBeInTheDocument();
      });

      const select = screen.getByLabelText("データソース");
      expect(select).toContainHTML("email");
      expect(select).toContainHTML("sentry");
    });

    it("AIプロバイダー選択ドロップダウンが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByLabelText("AIプロバイダー（オプション）"),
        ).toBeInTheDocument();
      });
    });

    it("AIプロバイダードロップダウンにデフォルト使用オプションがある", async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("デフォルトを使用")).toBeInTheDocument();
      });
    });

    it("インポート実行ボタンが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "インポート実行" }),
        ).toBeInTheDocument();
      });
    });

    it("データソース未選択時はインポート実行ボタンが無効化される", async () => {
      renderComponent();

      await waitFor(() => {
        const button = screen.getByRole("button", { name: "インポート実行" });
        expect(button).toBeDisabled();
      });
    });

    it("データソース選択時はインポート実行ボタンが有効化される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const select = screen.getByLabelText("データソース");
      await userEvent.selectOptions(select, "email");

      const button = screen.getByRole("button", { name: "インポート実行" });
      expect(button).not.toBeDisabled();
    });
  });

  describe("インポート実行", () => {
    beforeEach(() => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);
      mockedListAIProviders.mockResolvedValue(mockProvidersData);
    });

    it("インポート実行ボタンをクリックするとAPIが呼ばれる", async () => {
      mockedExecuteImport.mockResolvedValue(mockImportResult);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const select = screen.getByLabelText("データソース");
      await userEvent.selectOptions(select, "email");

      const button = screen.getByRole("button", { name: "インポート実行" });
      await userEvent.click(button);

      await waitFor(() => {
        expect(mockedExecuteImport).toHaveBeenCalled();
        expect(mockedExecuteImport.mock.calls[0][0]).toEqual({
          plugin_type: "email",
          ai_provider_type: null,
        });
      });
    });

    it("AIプロバイダーを指定してインポートを実行できる", async () => {
      mockedExecuteImport.mockResolvedValue(mockImportResult);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const pluginSelect = screen.getByLabelText("データソース");
      await userEvent.selectOptions(pluginSelect, "email");

      const providerSelect =
        screen.getByLabelText("AIプロバイダー（オプション）");
      await userEvent.selectOptions(providerSelect, "anthropic");

      const button = screen.getByRole("button", { name: "インポート実行" });
      await userEvent.click(button);

      await waitFor(() => {
        expect(mockedExecuteImport).toHaveBeenCalled();
        expect(mockedExecuteImport.mock.calls[0][0]).toEqual({
          plugin_type: "email",
          ai_provider_type: "anthropic",
        });
      });
    });

    it("実行中はローディング表示される", async () => {
      mockedExecuteImport.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockImportResult), 100),
          ),
      );

      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const select = screen.getByLabelText("データソース");
      await userEvent.selectOptions(select, "email");

      const button = screen.getByRole("button", { name: "インポート実行" });
      await userEvent.click(button);

      // ローディング中はボタンが無効化され、テキストが変わる
      expect(button).toBeDisabled();
      expect(screen.getByText("実行中...")).toBeInTheDocument();

      await waitFor(() => {
        expect(button).not.toBeDisabled();
      });
    });
  });

  describe("実行結果表示", () => {
    beforeEach(() => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);
      mockedListAIProviders.mockResolvedValue(mockProvidersData);
    });

    it("インポート成功時に結果サマリーを表示する", async () => {
      mockedExecuteImport.mockResolvedValue(mockImportResult);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const select = screen.getByLabelText("データソース");
      await userEvent.selectOptions(select, "email");

      const button = screen.getByRole("button", { name: "インポート実行" });
      await userEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText("実行結果")).toBeInTheDocument();
      });

      // 結果サマリーの確認
      expect(screen.getByText("取得件数")).toBeInTheDocument();
      expect(screen.getByText("10")).toBeInTheDocument();
      expect(screen.getByText("インポート成功")).toBeInTheDocument();
      expect(screen.getByText("7")).toBeInTheDocument();
      expect(screen.getByText("スキップ（重複）")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
      expect(screen.getByText("失敗")).toBeInTheDocument();
      expect(screen.getByText("1")).toBeInTheDocument();
    });

    it("エラーがある場合にエラー詳細を表示する", async () => {
      mockedExecuteImport.mockResolvedValue(mockImportResult);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const select = screen.getByLabelText("データソース");
      await userEvent.selectOptions(select, "email");

      const button = screen.getByRole("button", { name: "インポート実行" });
      await userEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText("エラー詳細")).toBeInTheDocument();
      });

      expect(screen.getByText("AI解析に失敗しました")).toBeInTheDocument();
    });

    it("エラーがない場合はエラー詳細セクションを表示しない", async () => {
      const successResult: ImportResult = {
        ...mockImportResult,
        total_failed: 0,
        errors: [],
      };
      mockedExecuteImport.mockResolvedValue(successResult);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const select = screen.getByLabelText("データソース");
      await userEvent.selectOptions(select, "email");

      const button = screen.getByRole("button", { name: "インポート実行" });
      await userEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText("実行結果")).toBeInTheDocument();
      });

      expect(screen.queryByText("エラー詳細")).not.toBeInTheDocument();
    });
  });

  describe("エラーハンドリング", () => {
    beforeEach(() => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);
      mockedListAIProviders.mockResolvedValue(mockProvidersData);
    });

    it("インポート実行失敗時にエラーメッセージを表示する", async () => {
      mockedExecuteImport.mockRejectedValue({
        errors: [
          { code: "GS-303", message: "メールサーバーへの接続に失敗しました" },
        ],
        timestamp: "2025-12-01T00:00:00Z",
      });

      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });

      const select = screen.getByLabelText("データソース");
      await userEvent.selectOptions(select, "email");

      const button = screen.getByRole("button", { name: "インポート実行" });
      await userEvent.click(button);

      await waitFor(() => {
        expect(
          screen.getByText("メールサーバーへの接続に失敗しました"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("アクセシビリティ", () => {
    beforeEach(() => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);
      mockedListAIProviders.mockResolvedValue(mockProvidersData);
    });

    it("フォーム要素に適切なlabelが設定されている", async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
        expect(
          screen.getByLabelText("AIプロバイダー（オプション）"),
        ).toBeInTheDocument();
      });
    });
  });
});

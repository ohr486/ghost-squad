/**
 * ImporterPage コンポーネントテスト
 *
 * TDD: REDフェーズ - テストを先に作成
 * 要件: MVP UI
 */

import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ImporterPage from "./ImporterPage";
import * as importerApi from "../../services/importerApi";
import type {
  PluginListResponse,
  AIProviderListResponse,
  ErrorStatsListResponse,
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
const mockedGetErrorStats = importerApi.getErrorStats as jest.MockedFunction<
  typeof importerApi.getErrorStats
>;

describe("ImporterPage", () => {
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
    ],
    timestamp: "2025-12-01T00:00:00Z",
  };

  const mockErrorStatsData: ErrorStatsListResponse = {
    data: [],
    timestamp: "2025-12-01T00:00:00Z",
  };

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ImporterPage />
      </QueryClientProvider>,
    );
  };

  beforeEach(() => {
    mockedListPlugins.mockResolvedValue(mockPluginsData);
    mockedListAIProviders.mockResolvedValue(mockProvidersData);
    mockedGetErrorStats.mockResolvedValue(mockErrorStatsData);
  });

  describe("ページ構造", () => {
    it("ページタイトルが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("インポーター管理")).toBeInTheDocument();
      });
    });

    it("インポート実行セクションが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "インポート実行" }),
        ).toBeInTheDocument();
      });
    });

    it("プラグイン一覧セクションが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "データソースプラグイン" }),
        ).toBeInTheDocument();
      });
    });

    it("AIプロバイダー一覧セクションが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "AIプロバイダー" }),
        ).toBeInTheDocument();
      });
    });

    it("エラー統計セクションが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "エラー統計" }),
        ).toBeInTheDocument();
      });
    });
  });

  describe("子コンポーネントの統合", () => {
    it("ImportExecutorComponentが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("データソース")).toBeInTheDocument();
      });
    });

    it("PluginListComponentが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        // PluginListComponentはデータソースプラグインのテーブルを表示
        // テーブル内のaria-labelを確認
        expect(
          screen.getByRole("table", { name: "データソースプラグイン一覧" }),
        ).toBeInTheDocument();
      });
    });

    it("AIProviderListComponentが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("openai")).toBeInTheDocument();
      });
    });

    it("ErrorStatsComponentが表示される", async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("エラーはありません")).toBeInTheDocument();
      });
    });
  });

  describe("レイアウト", () => {
    it("各セクションがセクション要素で囲まれている", async () => {
      renderComponent();

      await waitFor(() => {
        const sections = document.querySelectorAll("section");
        expect(sections.length).toBe(4); // Executor, Plugin, AIProvider, ErrorStats
      });
    });

    it("セクション間に適切な余白がある", async () => {
      renderComponent();

      await waitFor(() => {
        const pageContainer = document.querySelector(".importer-page");
        expect(pageContainer).toHaveClass("space-y-8");
      });
    });
  });

  describe("アクセシビリティ", () => {
    it("メインコンテンツとしてのロールが設定されている", async () => {
      renderComponent();

      await waitFor(() => {
        const main = screen.getByRole("main");
        expect(main).toBeInTheDocument();
      });
    });
  });
});

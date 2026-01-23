/**
 * PluginListComponent コンポーネントテスト
 *
 * TDD: REDフェーズ - テストを先に作成
 * 要件: 1.1, 1.2
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PluginListComponent from "./PluginListComponent";
import * as importerApi from "../../services/importerApi";
import type { PluginListResponse, PluginStatus } from "../../types/importer";

// Mock importer API
jest.mock("../../services/importerApi");
const mockedListPlugins = importerApi.listPlugins as jest.MockedFunction<
  typeof importerApi.listPlugins
>;
const mockedEnablePlugin = importerApi.enablePlugin as jest.MockedFunction<
  typeof importerApi.enablePlugin
>;
const mockedDisablePlugin = importerApi.disablePlugin as jest.MockedFunction<
  typeof importerApi.disablePlugin
>;

describe("PluginListComponent", () => {
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
        enabled: false,
        initialized: true,
        error_message: null,
      },
      {
        plugin_type: "slack",
        enabled: false,
        initialized: false,
        error_message: "接続に失敗しました",
      },
    ],
    timestamp: "2025-12-01T00:00:00Z",
  };

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <PluginListComponent />
      </QueryClientProvider>,
    );
  };

  describe("ローディング状態", () => {
    it("データ取得中にローディングメッセージを表示する", async () => {
      mockedListPlugins.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockPluginsData), 100),
          ),
      );

      renderComponent();

      expect(screen.getByText("読み込み中...")).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByText("読み込み中...")).not.toBeInTheDocument();
      });
    });
  });

  describe("エラー状態", () => {
    it("API呼び出しエラー時にエラーメッセージを表示する", async () => {
      const errorMessage = "プラグインの読み込みに失敗しました";
      mockedListPlugins.mockRejectedValue(new Error(errorMessage));

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByText(new RegExp(errorMessage, "i")),
        ).toBeInTheDocument();
      });
    });
  });

  describe("プラグイン一覧表示", () => {
    it("プラグイン一覧を正しく表示する", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("email")).toBeInTheDocument();
      });

      expect(screen.getByText("sentry")).toBeInTheDocument();
      expect(screen.getByText("slack")).toBeInTheDocument();
    });

    it("プラグインの初期化状態を日本語で表示する", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("email")).toBeInTheDocument();
      });

      // 初期化済みのプラグインと初期化失敗のプラグインを確認
      const initializedElements = screen.getAllByText("初期化済み");
      expect(initializedElements.length).toBe(2);

      const errorElements = screen.getAllByText("エラー");
      expect(errorElements.length).toBe(1);
    });

    it("エラーメッセージがある場合に表示する", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("接続に失敗しました")).toBeInTheDocument();
      });
    });

    it("プラグインが0件の場合、メッセージを表示する", async () => {
      const emptyData: PluginListResponse = {
        data: [],
        timestamp: "2025-12-01T00:00:00Z",
      };
      mockedListPlugins.mockResolvedValue(emptyData);

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByText("登録されているプラグインはありません"),
        ).toBeInTheDocument();
      });
    });

    it("テーブルヘッダーが正しく表示される", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("プラグイン")).toBeInTheDocument();
      });

      expect(screen.getByText("状態")).toBeInTheDocument();
      expect(screen.getByText("有効/無効")).toBeInTheDocument();
    });

    it("セクション見出しが表示される", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("データソースプラグイン")).toBeInTheDocument();
      });
    });
  });

  describe("有効/無効トグル", () => {
    it("有効なプラグインのトグルがオンになっている", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("email")).toBeInTheDocument();
      });

      // email プラグインのトグルを探す（aria-labelで特定）
      const emailToggle = screen.getByRole("checkbox", {
        name: "emailプラグインの有効/無効切り替え",
      });
      expect(emailToggle).toBeChecked();
    });

    it("無効なプラグインのトグルがオフになっている", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("sentry")).toBeInTheDocument();
      });

      const sentryToggle = screen.getByRole("checkbox", {
        name: "sentryプラグインの有効/無効切り替え",
      });
      expect(sentryToggle).not.toBeChecked();
    });

    it("トグルをクリックするとプラグインを有効化するAPIが呼ばれる", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);
      const updatedPlugin: PluginStatus = {
        plugin_type: "sentry",
        enabled: true,
        initialized: true,
        error_message: null,
      };
      mockedEnablePlugin.mockResolvedValue(updatedPlugin);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("sentry")).toBeInTheDocument();
      });

      const sentryToggle = screen.getByRole("checkbox", {
        name: "sentryプラグインの有効/無効切り替え",
      });
      await userEvent.click(sentryToggle);

      await waitFor(() => {
        expect(mockedEnablePlugin).toHaveBeenCalled();
        expect(mockedEnablePlugin.mock.calls[0][0]).toBe("sentry");
      });
    });

    it("トグルをクリックするとプラグインを無効化するAPIが呼ばれる", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);
      const updatedPlugin: PluginStatus = {
        plugin_type: "email",
        enabled: false,
        initialized: true,
        error_message: null,
      };
      mockedDisablePlugin.mockResolvedValue(updatedPlugin);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("email")).toBeInTheDocument();
      });

      const emailToggle = screen.getByRole("checkbox", {
        name: "emailプラグインの有効/無効切り替え",
      });
      await userEvent.click(emailToggle);

      await waitFor(() => {
        expect(mockedDisablePlugin).toHaveBeenCalled();
        expect(mockedDisablePlugin.mock.calls[0][0]).toBe("email");
      });
    });

    it("トグル操作中はローディング状態を表示する", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);
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

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("sentry")).toBeInTheDocument();
      });

      const sentryToggle = screen.getByRole("checkbox", {
        name: "sentryプラグインの有効/無効切り替え",
      });
      await userEvent.click(sentryToggle);

      // ローディング中はトグルが無効化される
      expect(sentryToggle).toBeDisabled();

      await waitFor(() => {
        expect(sentryToggle).not.toBeDisabled();
      });
    });

    it("トグル操作失敗時にエラーメッセージを表示する", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);
      mockedEnablePlugin.mockRejectedValue({
        errors: [
          { code: "GS-301", message: "プラグインの有効化に失敗しました" },
        ],
        timestamp: "2025-12-01T00:00:00Z",
      });

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("sentry")).toBeInTheDocument();
      });

      const sentryToggle = screen.getByRole("checkbox", {
        name: "sentryプラグインの有効/無効切り替え",
      });
      await userEvent.click(sentryToggle);

      await waitFor(() => {
        expect(
          screen.getByText("プラグインの有効化に失敗しました"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("アクセシビリティ", () => {
    it("テーブルに適切なaria属性が設定されている", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);

      renderComponent();

      await waitFor(() => {
        const table = screen.getByRole("table");
        expect(table).toHaveAttribute(
          "aria-label",
          "データソースプラグイン一覧",
        );
      });
    });

    it("各トグルに適切なaria-labelが設定されている", async () => {
      mockedListPlugins.mockResolvedValue(mockPluginsData);

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByRole("checkbox", {
            name: "emailプラグインの有効/無効切り替え",
          }),
        ).toBeInTheDocument();
        expect(
          screen.getByRole("checkbox", {
            name: "sentryプラグインの有効/無効切り替え",
          }),
        ).toBeInTheDocument();
        expect(
          screen.getByRole("checkbox", {
            name: "slackプラグインの有効/無効切り替え",
          }),
        ).toBeInTheDocument();
      });
    });
  });
});

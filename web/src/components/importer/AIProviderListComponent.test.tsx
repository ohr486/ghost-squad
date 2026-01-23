/**
 * AIProviderListComponent コンポーネントテスト
 *
 * TDD: REDフェーズ - テストを先に作成
 * 要件: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AIProviderListComponent from "./AIProviderListComponent";
import * as importerApi from "../../services/importerApi";
import type {
  AIProviderListResponse,
  AIProviderStatus,
} from "../../types/importer";

// Mock importer API
jest.mock("../../services/importerApi");
const mockedListAIProviders =
  importerApi.listAIProviders as jest.MockedFunction<
    typeof importerApi.listAIProviders
  >;
const mockedSetDefaultAIProvider =
  importerApi.setDefaultAIProvider as jest.MockedFunction<
    typeof importerApi.setDefaultAIProvider
  >;

describe("AIProviderListComponent", () => {
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
      {
        provider_type: "gemini",
        enabled: false,
        initialized: false,
        is_default: false,
        model: "gemini-pro",
        error_message: "API Keyが設定されていません",
      },
    ],
    timestamp: "2025-12-01T00:00:00Z",
  };

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AIProviderListComponent />
      </QueryClientProvider>,
    );
  };

  describe("ローディング状態", () => {
    it("データ取得中にローディングメッセージを表示する", async () => {
      mockedListAIProviders.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockProvidersData), 100),
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
      const errorMessage = "AIプロバイダーの読み込みに失敗しました";
      mockedListAIProviders.mockRejectedValue(new Error(errorMessage));

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByText(new RegExp(errorMessage, "i")),
        ).toBeInTheDocument();
      });
    });
  });

  describe("プロバイダー一覧表示", () => {
    it("プロバイダー一覧を正しく表示する", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("openai")).toBeInTheDocument();
      });

      expect(screen.getByText("anthropic")).toBeInTheDocument();
      expect(screen.getByText("gemini")).toBeInTheDocument();
    });

    it("プロバイダーのモデル名を表示する", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("gpt-4")).toBeInTheDocument();
      });

      expect(screen.getByText("claude-3-sonnet-20240229")).toBeInTheDocument();
      expect(screen.getByText("gemini-pro")).toBeInTheDocument();
    });

    it("プロバイダーの初期化状態を日本語で表示する", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("openai")).toBeInTheDocument();
      });

      // 接続済みのプロバイダーと初期化失敗のプロバイダーを確認
      const connectedElements = screen.getAllByText("接続済み");
      expect(connectedElements.length).toBe(2);

      const errorElements = screen.getAllByText("エラー");
      expect(errorElements.length).toBe(1);
    });

    it("エラーメッセージがある場合に表示する", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByText("API Keyが設定されていません"),
        ).toBeInTheDocument();
      });
    });

    it("プロバイダーが0件の場合、メッセージを表示する", async () => {
      const emptyData: AIProviderListResponse = {
        data: [],
        timestamp: "2025-12-01T00:00:00Z",
      };
      mockedListAIProviders.mockResolvedValue(emptyData);

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByText("登録されているAIプロバイダーはありません"),
        ).toBeInTheDocument();
      });
    });

    it("テーブルヘッダーが正しく表示される", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("プロバイダー")).toBeInTheDocument();
      });

      expect(screen.getByText("モデル")).toBeInTheDocument();
      expect(screen.getByText("状態")).toBeInTheDocument();
      expect(screen.getByText("デフォルト")).toBeInTheDocument();
    });

    it("セクション見出しが表示される", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("AIプロバイダー")).toBeInTheDocument();
      });
    });
  });

  describe("デフォルト選択ラジオボタン", () => {
    it("デフォルトプロバイダーのラジオボタンが選択されている", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("openai")).toBeInTheDocument();
      });

      // openai がデフォルトのラジオボタンを探す
      const openaiRadio = screen.getByRole("radio", {
        name: "openaiをデフォルトに設定",
      });
      expect(openaiRadio).toBeChecked();
    });

    it("デフォルトでないプロバイダーのラジオボタンは選択されていない", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("anthropic")).toBeInTheDocument();
      });

      const anthropicRadio = screen.getByRole("radio", {
        name: "anthropicをデフォルトに設定",
      });
      expect(anthropicRadio).not.toBeChecked();
    });

    it("ラジオボタンをクリックするとデフォルト設定APIが呼ばれる", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);
      const updatedProvider: AIProviderStatus = {
        provider_type: "anthropic",
        enabled: true,
        initialized: true,
        is_default: true,
        model: "claude-3-sonnet-20240229",
        error_message: null,
      };
      mockedSetDefaultAIProvider.mockResolvedValue(updatedProvider);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("anthropic")).toBeInTheDocument();
      });

      const anthropicRadio = screen.getByRole("radio", {
        name: "anthropicをデフォルトに設定",
      });
      await userEvent.click(anthropicRadio);

      await waitFor(() => {
        expect(mockedSetDefaultAIProvider).toHaveBeenCalled();
      });
      expect(mockedSetDefaultAIProvider.mock.calls[0][0]).toBe("anthropic");
    });

    it("デフォルト設定中はローディング状態を表示する", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);
      mockedSetDefaultAIProvider.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  provider_type: "anthropic",
                  enabled: true,
                  initialized: true,
                  is_default: true,
                  model: "claude-3-sonnet-20240229",
                  error_message: null,
                }),
              100,
            ),
          ),
      );

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("anthropic")).toBeInTheDocument();
      });

      const anthropicRadio = screen.getByRole("radio", {
        name: "anthropicをデフォルトに設定",
      });
      await userEvent.click(anthropicRadio);

      // ローディング中は全てのラジオボタンが無効化される
      const allRadios = screen.getAllByRole("radio");
      allRadios.forEach((radio) => {
        expect(radio).toBeDisabled();
      });

      await waitFor(() => {
        const allRadiosAfter = screen.getAllByRole("radio");
        allRadiosAfter.forEach((radio) => {
          expect(radio).not.toBeDisabled();
        });
      });
    });

    it("デフォルト設定失敗時にエラーメッセージを表示する", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);
      mockedSetDefaultAIProvider.mockRejectedValue({
        errors: [{ code: "GS-308", message: "デフォルト設定に失敗しました" }],
        timestamp: "2025-12-01T00:00:00Z",
      });

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("anthropic")).toBeInTheDocument();
      });

      const anthropicRadio = screen.getByRole("radio", {
        name: "anthropicをデフォルトに設定",
      });
      await userEvent.click(anthropicRadio);

      await waitFor(() => {
        expect(
          screen.getByText("デフォルト設定に失敗しました"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("アクセシビリティ", () => {
    it("テーブルに適切なaria属性が設定されている", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        const table = screen.getByRole("table");
        expect(table).toHaveAttribute("aria-label", "AIプロバイダー一覧");
      });
    });

    it("各ラジオボタンに適切なaria-labelが設定されている", async () => {
      mockedListAIProviders.mockResolvedValue(mockProvidersData);

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByRole("radio", { name: "openaiをデフォルトに設定" }),
        ).toBeInTheDocument();
      });
      expect(
        screen.getByRole("radio", { name: "anthropicをデフォルトに設定" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("radio", { name: "geminiをデフォルトに設定" }),
      ).toBeInTheDocument();
    });
  });
});

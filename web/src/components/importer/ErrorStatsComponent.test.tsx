/**
 * ErrorStatsComponent コンポーネントテスト
 *
 * TDD: REDフェーズ - テストを先に作成
 * 要件: 5.4
 */

import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ErrorStatsComponent from "./ErrorStatsComponent";
import * as importerApi from "../../services/importerApi";
import type { ErrorStatsListResponse } from "../../types/importer";

// Mock importer API
jest.mock("../../services/importerApi");
const mockedGetErrorStats = importerApi.getErrorStats as jest.MockedFunction<
  typeof importerApi.getErrorStats
>;

describe("ErrorStatsComponent", () => {
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

  const mockErrorStatsData: ErrorStatsListResponse = {
    data: [
      {
        error_code: "GS-303",
        count: 15,
        last_occurred: "2025-12-01T10:30:00Z",
      },
      {
        error_code: "GS-304",
        count: 8,
        last_occurred: "2025-12-01T09:00:00Z",
      },
      {
        error_code: "GS-306",
        count: 3,
        last_occurred: "2025-11-30T23:45:00Z",
      },
    ],
    timestamp: "2025-12-01T12:00:00Z",
  };

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ErrorStatsComponent />
      </QueryClientProvider>,
    );
  };

  describe("ローディング状態", () => {
    it("データ取得中にローディングメッセージを表示する", async () => {
      mockedGetErrorStats.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockErrorStatsData), 100),
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
      const errorMessage = "エラー統計の読み込みに失敗しました";
      mockedGetErrorStats.mockRejectedValue(new Error(errorMessage));

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByText(new RegExp(errorMessage, "i")),
        ).toBeInTheDocument();
      });
    });
  });

  describe("統計一覧表示", () => {
    it("セクション見出しが表示される", async () => {
      mockedGetErrorStats.mockResolvedValue(mockErrorStatsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("エラー統計")).toBeInTheDocument();
      });
    });

    it("エラー統計一覧を正しく表示する", async () => {
      mockedGetErrorStats.mockResolvedValue(mockErrorStatsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("GS-303")).toBeInTheDocument();
      });

      expect(screen.getByText("GS-304")).toBeInTheDocument();
      expect(screen.getByText("GS-306")).toBeInTheDocument();
    });

    it("エラー発生回数を表示する", async () => {
      mockedGetErrorStats.mockResolvedValue(mockErrorStatsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("15")).toBeInTheDocument();
      });

      expect(screen.getByText("8")).toBeInTheDocument();
      expect(screen.getByText("3")).toBeInTheDocument();
    });

    it("最終発生日時を日本語形式で表示する", async () => {
      mockedGetErrorStats.mockResolvedValue(mockErrorStatsData);

      renderComponent();

      await waitFor(() => {
        // 日本語ロケールでの日時表示を確認
        // 複数の日時が表示されるため、getAllByTextを使用
        const dateTexts = screen.getAllByText(/2025/);
        expect(dateTexts.length).toBe(3);
      });
    });

    it("テーブルヘッダーが正しく表示される", async () => {
      mockedGetErrorStats.mockResolvedValue(mockErrorStatsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("エラーコード")).toBeInTheDocument();
      });

      expect(screen.getByText("発生回数")).toBeInTheDocument();
      expect(screen.getByText("最終発生")).toBeInTheDocument();
    });
  });

  describe("エラーなし状態", () => {
    it("エラーがない場合にメッセージを表示する", async () => {
      const emptyData: ErrorStatsListResponse = {
        data: [],
        timestamp: "2025-12-01T00:00:00Z",
      };
      mockedGetErrorStats.mockResolvedValue(emptyData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("エラーはありません")).toBeInTheDocument();
      });
    });

    it("エラーがない場合はテーブルを表示しない", async () => {
      const emptyData: ErrorStatsListResponse = {
        data: [],
        timestamp: "2025-12-01T00:00:00Z",
      };
      mockedGetErrorStats.mockResolvedValue(emptyData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("エラーはありません")).toBeInTheDocument();
      });

      expect(screen.queryByRole("table")).not.toBeInTheDocument();
    });
  });

  describe("アクセシビリティ", () => {
    it("テーブルに適切なaria属性が設定されている", async () => {
      mockedGetErrorStats.mockResolvedValue(mockErrorStatsData);

      renderComponent();

      await waitFor(() => {
        const table = screen.getByRole("table");
        expect(table).toHaveAttribute("aria-label", "エラー統計一覧");
      });
    });
  });

  describe("自動更新", () => {
    it("定期的にデータを更新する", async () => {
      jest.useFakeTimers();
      mockedGetErrorStats.mockResolvedValue(mockErrorStatsData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("GS-303")).toBeInTheDocument();
      });

      // 初回呼び出し
      expect(mockedGetErrorStats).toHaveBeenCalledTimes(1);

      // 30秒進める（refetchInterval想定）
      jest.advanceTimersByTime(30000);

      await waitFor(() => {
        expect(mockedGetErrorStats).toHaveBeenCalledTimes(2);
      });

      jest.useRealTimers();
    });
  });
});

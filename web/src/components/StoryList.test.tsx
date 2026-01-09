/**
 * StoryList コンポーネントテスト
 *
 * 要件: 5.1, 5.4, 5.5, 5.10, 5.11, 5.12
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StoryList from "./StoryList";
import * as storyApi from "../services/storyApi";
import type { PaginatedResponse, StoryResponse } from "../types";

// Mock story API
jest.mock("../services/storyApi");
const mockedListStories = storyApi.listStories as jest.MockedFunction<
  typeof storyApi.listStories
>;

describe("StoryList Component", () => {
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

  const mockStoriesData: PaginatedResponse<StoryResponse> = {
    data: [
      {
        id: 1,
        inquiry_id: 100,
        title: "ユーザー登録機能の実装",
        description: "As a user, I want to register...",
        priority: "high",
        status: "waiting_review",
        estimated_effort: 5,
        deadline: "2025-12-31T00:00:00Z",
        assignee: "田中太郎",
        story_metadata: {},
        created_at: "2025-12-01T00:00:00Z",
        updated_at: "2025-12-01T00:00:00Z",
      },
      {
        id: 2,
        inquiry_id: 101,
        title: "ログイン機能の改善",
        description: "As a user, I want to login...",
        priority: "medium",
        status: "approved",
        estimated_effort: null,
        deadline: null,
        assignee: null,
        story_metadata: {},
        created_at: "2025-12-02T00:00:00Z",
        updated_at: "2025-12-02T00:00:00Z",
      },
    ],
    meta: {
      page: 1,
      limit: 20,
      total: 2,
      has_next: false,
    },
    timestamp: "2025-12-01T00:00:00Z",
  };

  const renderComponent = (props = {}) => {
    const defaultProps = {
      onStoryClick: jest.fn(),
      onCreateStoryClick: jest.fn(),
      ...props,
    };

    return {
      ...render(
        <QueryClientProvider client={queryClient}>
          <StoryList {...defaultProps} />
        </QueryClientProvider>,
      ),
      props: defaultProps,
    };
  };

  describe("ローディング状態", () => {
    it("データ取得中にローディングメッセージを表示する", async () => {
      mockedListStories.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockStoriesData), 100),
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
      const errorMessage = "ストーリーの読み込みに失敗しました";
      mockedListStories.mockRejectedValue(new Error(errorMessage));

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByText(new RegExp(errorMessage, "i")),
        ).toBeInTheDocument();
      });
    });

    it("エラー時でもステータスフィルターは表示される", async () => {
      mockedListStories.mockRejectedValue(new Error("API Error"));

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByLabelText("ステータスフィルター"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("ストーリー一覧表示", () => {
    it("ストーリー一覧を正しく表示する", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("#1")).toBeInTheDocument();
      });

      expect(screen.getByText("ユーザー登録機能の実装")).toBeInTheDocument();
      expect(screen.getByText("#2")).toBeInTheDocument();
      expect(screen.getByText("ログイン機能の改善")).toBeInTheDocument();
    });

    it("ストーリーのステータスを日本語で表示する", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("#1")).toBeInTheDocument();
      });

      const waitingReviewElements = screen.getAllByText("レビュー待ち");
      expect(waitingReviewElements.length).toBeGreaterThan(0);

      const approvedElements = screen.getAllByText("承認済み");
      expect(approvedElements.length).toBeGreaterThan(0);
    });

    it("ストーリーの優先度を日本語で表示する", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("高")).toBeInTheDocument();
      });

      expect(screen.getByText("中")).toBeInTheDocument();
    });

    it("説明文を100文字で省略表示する", async () => {
      const longDescription = "A".repeat(150);
      const storiesWithLongDesc: PaginatedResponse<StoryResponse> = {
        ...mockStoriesData,
        data: [
          {
            ...mockStoriesData.data[0],
            description: longDescription,
          },
        ],
      };
      mockedListStories.mockResolvedValue(storiesWithLongDesc);

      renderComponent();

      await waitFor(() => {
        const descriptionText = screen.getByText(/^A+\.\.\.$/);
        expect(descriptionText.textContent?.length).toBeLessThanOrEqual(103); // 100 + '...'
      });
    });

    it("ストーリーが0件の場合、メッセージを表示する", async () => {
      const emptyData: PaginatedResponse<StoryResponse> = {
        data: [],
        meta: {
          page: 1,
          limit: 20,
          total: 0,
          has_next: false,
        },
        timestamp: "2025-12-01T00:00:00Z",
      };
      mockedListStories.mockResolvedValue(emptyData);

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByText("ストーリーが見つかりませんでした。"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("「新規ストーリー作成」ボタン", () => {
    it("「新規ストーリー作成」ボタンが表示される", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText("新規ストーリー作成")).toBeInTheDocument();
      });
    });

    it("「新規ストーリー作成」ボタンをクリックするとコールバックが呼ばれる", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);
      const onCreateStoryClick = jest.fn();

      renderComponent({ onCreateStoryClick });

      await waitFor(() => {
        expect(screen.getByText("新規ストーリー作成")).toBeInTheDocument();
      });

      const createButton = screen.getByText("新規ストーリー作成");
      await userEvent.click(createButton);

      expect(onCreateStoryClick).toHaveBeenCalledTimes(1);
    });
  });

  describe("ページネーション", () => {
    it("ページネーションコントロールが表示される", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);

      renderComponent();

      // Wait for the story list to load first
      await waitFor(() => {
        expect(screen.getByText("#1")).toBeInTheDocument();
      });

      // Then check pagination controls
      const prevButtons = screen.getAllByText("前へ");
      expect(prevButtons.length).toBeGreaterThan(0);

      const nextButtons = screen.getAllByText("次へ");
      expect(nextButtons.length).toBeGreaterThan(0);

      // Check that pagination is present by checking for aria-label
      expect(screen.getByLabelText("Pagination")).toBeInTheDocument();
    });

    it("次ページボタンをクリックするとページが進む", async () => {
      const page1Data = {
        ...mockStoriesData,
        meta: { ...mockStoriesData.meta, has_next: true },
      };
      const page2Data = {
        ...mockStoriesData,
        meta: { page: 2, limit: 20, total: 25, has_next: false },
      };

      mockedListStories.mockResolvedValueOnce(page1Data);
      mockedListStories.mockResolvedValueOnce(page2Data);

      renderComponent();

      await waitFor(() => {
        expect(screen.getAllByText("次へ").length).toBeGreaterThan(0);
      });

      const nextButtons = screen.getAllByText("次へ");
      await userEvent.click(nextButtons[0]);

      await waitFor(() => {
        expect(mockedListStories).toHaveBeenCalledTimes(2);
      });

      expect(mockedListStories).toHaveBeenLastCalledWith({
        page: 2,
        limit: 20,
        sort_by: "created_at",
        sort_order: "desc",
      });
    });

    it("前ページボタンは1ページ目では無効化される", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);

      renderComponent();

      await waitFor(() => {
        const prevButtons = screen.getAllByText("前へ");
        prevButtons.forEach((button) => {
          expect(button).toBeDisabled();
        });
      });
    });

    it("次ページがない場合、次ページボタンは無効化される", async () => {
      const lastPageData = {
        ...mockStoriesData,
        meta: { ...mockStoriesData.meta, has_next: false },
      };
      mockedListStories.mockResolvedValue(lastPageData);

      renderComponent();

      await waitFor(() => {
        const nextButtons = screen.getAllByText("次へ");
        nextButtons.forEach((button) => {
          expect(button).toBeDisabled();
        });
      });
    });
  });

  describe("ステータスフィルタリング", () => {
    it("ステータスフィルターが表示される", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByLabelText("ステータスフィルター"),
        ).toBeInTheDocument();
      });
    });

    it("ステータスフィルターを変更すると、フィルタリングされたデータを取得する", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);

      renderComponent();

      await waitFor(() => {
        expect(
          screen.getByLabelText("ステータスフィルター"),
        ).toBeInTheDocument();
      });

      const statusFilter = screen.getByLabelText("ステータスフィルター");
      await userEvent.selectOptions(statusFilter, "approved");

      await waitFor(() => {
        expect(mockedListStories).toHaveBeenCalledWith({
          page: 1,
          limit: 20,
          status: "approved",
          sort_by: "created_at",
          sort_order: "desc",
        });
      });
    });

    it("ステータスフィルター変更時、ページは1ページ目にリセットされる", async () => {
      const page1Data = {
        ...mockStoriesData,
        meta: { ...mockStoriesData.meta, has_next: true },
      };
      mockedListStories.mockResolvedValue(page1Data);

      renderComponent();

      await waitFor(() => {
        expect(screen.getAllByText("次へ").length).toBeGreaterThan(0);
      });

      // Navigate to page 2
      const nextButtons = screen.getAllByText("次へ");
      await userEvent.click(nextButtons[0]);

      await waitFor(() => {
        expect(mockedListStories).toHaveBeenCalledWith({
          page: 2,
          limit: 20,
          sort_by: "created_at",
          sort_order: "desc",
        });
      });

      // Change status filter
      const statusFilter = screen.getByLabelText("ステータスフィルター");
      await userEvent.selectOptions(statusFilter, "approved");

      await waitFor(() => {
        expect(mockedListStories).toHaveBeenLastCalledWith({
          page: 1,
          limit: 20,
          status: "approved",
          sort_by: "created_at",
          sort_order: "desc",
        });
      });
    });
  });

  describe("行クリックとキーボードナビゲーション", () => {
    it("ストーリー行をクリックすると、コールバックが呼ばれる", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);
      const onStoryClick = jest.fn();

      renderComponent({ onStoryClick });

      await waitFor(() => {
        expect(screen.getByText("#1")).toBeInTheDocument();
      });

      // Use getByRole to find the row
      const rows = screen.getAllByRole("row");
      const firstDataRow = rows[1]; // Skip header row
      await userEvent.click(firstDataRow);

      expect(onStoryClick).toHaveBeenCalledWith(1);
    });

    it("Enterキーでストーリー詳細に遷移する", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);
      const onStoryClick = jest.fn();

      renderComponent({ onStoryClick });

      await waitFor(() => {
        expect(screen.getByText("#1")).toBeInTheDocument();
      });

      // Use getByRole to find the row
      const rows = screen.getAllByRole("row");
      const firstDataRow = rows[1]; // Skip header row
      firstDataRow.focus();
      await userEvent.keyboard("{Enter}");

      expect(onStoryClick).toHaveBeenCalledWith(1);
    });

    it("スペースキーでストーリー詳細に遷移する", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);
      const onStoryClick = jest.fn();

      renderComponent({ onStoryClick });

      await waitFor(() => {
        expect(screen.getByText("#1")).toBeInTheDocument();
      });

      // Use getByRole to find the row
      const rows = screen.getAllByRole("row");
      const firstDataRow = rows[1]; // Skip header row
      firstDataRow.focus();
      await userEvent.keyboard(" ");

      expect(onStoryClick).toHaveBeenCalledWith(1);
    });
  });

  describe("ソート機能", () => {
    it("ソート順セレクトボックスが表示される", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("ソート順")).toBeInTheDocument();
      });
    });

    it("ソート順を変更すると、ソートされたデータを取得する", async () => {
      mockedListStories.mockResolvedValue(mockStoriesData);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByLabelText("ソート順")).toBeInTheDocument();
      });

      const sortSelect = screen.getByLabelText("ソート順");
      await userEvent.selectOptions(sortSelect, "priority");

      await waitFor(() => {
        expect(mockedListStories).toHaveBeenCalledWith({
          page: 1,
          limit: 20,
          sort_by: "priority",
          sort_order: "desc",
        });
      });
    });
  });
});

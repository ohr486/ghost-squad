import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import InquiryList from "./InquiryList";
import * as inquiryApi from "../services/inquiryApi";

// Mock the inquiry API
jest.mock("../services/inquiryApi");

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const mockInquiries = [
  {
    id: 1,
    user_id: "user_001",
    content: "ログイン機能が欲しい",
    source_system: "manual",
    timestamp: "2024-01-01T10:00:00Z",
    status: "received" as const,
    created_at: "2024-01-01T10:00:00Z",
    updated_at: "2024-01-01T10:00:00Z",
  },
  {
    id: 2,
    user_id: "user_002",
    content: "ダッシュボードを改善してください",
    source_system: "manual",
    timestamp: "2024-01-01T11:00:00Z",
    status: "task_working" as const,
    created_at: "2024-01-01T11:00:00Z",
    updated_at: "2024-01-01T11:00:00Z",
  },
];

const mockEmailInquiry = {
  id: 3,
  user_id: "importer:email",
  content: "メールからインポートされた内容です",
  source_system: "importer:email",
  timestamp: "2024-01-02T10:00:00Z",
  status: "received" as const,
  created_at: "2024-01-02T10:00:00Z",
  updated_at: "2024-01-02T10:00:00Z",
  inquiry_metadata: {
    importer: {
      source_type: "email",
      source_id: "<message-id@example.com>",
      original_subject: "【重要】システム障害のお知らせ",
      original_sender: "support@example.com",
      imported_at: "2024-01-02T10:00:00Z",
    },
  },
};

const mockPaginatedResponse = {
  data: mockInquiries,
  meta: {
    page: 1,
    limit: 20,
    total: 2,
    has_next: false,
  },
  timestamp: "2024-01-01T12:00:00Z",
};

describe("InquiryList", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("問い合わせ一覧を表示する", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue(
      mockPaginatedResponse,
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("ログイン機能が欲しい")).toBeInTheDocument();
    });

    expect(
      screen.getByText("ダッシュボードを改善してください"),
    ).toBeInTheDocument();
  });

  it("問い合わせID、内容（省略表示）、ステータス、タイムスタンプを表示する", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue(
      mockPaginatedResponse,
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("#1")).toBeInTheDocument();
    });

    expect(screen.getByText("#2")).toBeInTheDocument();

    // Use getAllByText to get all instances and check table status badges
    const statusBadges = screen.getAllByText("受付済み");
    expect(statusBadges.length).toBeGreaterThan(0);

    const taskWorkingBadges = screen.getAllByText("タスク作業中");
    expect(taskWorkingBadges.length).toBeGreaterThan(0);
  });

  it("デフォルトページサイズ20件で一覧を取得する", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue(
      mockPaginatedResponse,
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(inquiryApi.listInquiries).toHaveBeenCalledWith({
        page: 1,
        limit: 20,
      });
    });
  });

  it("ページネーション操作をサポートする", async () => {
    const firstPageResponse = {
      ...mockPaginatedResponse,
      meta: {
        page: 1,
        limit: 20,
        total: 30,
        has_next: true,
      },
    };

    const secondPageResponse = {
      data: [
        {
          id: 3,
          user_id: "user_003",
          content: "新しい問い合わせ",
          source_system: "manual",
          timestamp: "2024-01-02T10:00:00Z",
          status: "received" as const,
          created_at: "2024-01-02T10:00:00Z",
          updated_at: "2024-01-02T10:00:00Z",
        },
      ],
      meta: {
        page: 2,
        limit: 20,
        total: 30,
        has_next: false,
      },
      timestamp: "2024-01-02T12:00:00Z",
    };

    (inquiryApi.listInquiries as jest.Mock)
      .mockResolvedValueOnce(firstPageResponse)
      .mockResolvedValueOnce(secondPageResponse);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("ログイン機能が欲しい")).toBeInTheDocument();
    });

    const nextButton = screen.getAllByText("次へ")[0];
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(inquiryApi.listInquiries).toHaveBeenCalledWith({
        page: 2,
        limit: 20,
      });
    });
  });

  it("ステータスフィルタリングをサポートする", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue(
      mockPaginatedResponse,
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("ログイン機能が欲しい")).toBeInTheDocument();
    });

    const filterSelect = screen.getByLabelText("ステータスフィルター");
    fireEvent.change(filterSelect, { target: { value: "received" } });

    await waitFor(() => {
      expect(inquiryApi.listInquiries).toHaveBeenCalledWith({
        page: 1,
        limit: 20,
        status: "received",
      });
    });
  });

  it("行クリックで詳細ページへ遷移する", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue(
      mockPaginatedResponse,
    );

    const handleInquiryClick = jest.fn();
    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={handleInquiryClick} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("ログイン機能が欲しい")).toBeInTheDocument();
    });

    // Get the table and find the row with the first inquiry
    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");
    // Skip header row (index 0), click first data row (index 1)
    fireEvent.click(rows[1]);

    expect(handleInquiryClick).toHaveBeenCalledWith(1);
  });

  it("ローディング状態を表示する", () => {
    (inquiryApi.listInquiries as jest.Mock).mockImplementation(
      () => new Promise(() => {}), // Never resolves
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    expect(screen.getByText("読み込み中...")).toBeInTheDocument();
  });

  it("エラー状態を表示する", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockRejectedValue(
      new Error("API Error"),
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(/問い合わせの読み込みに失敗しました/),
      ).toBeInTheDocument();
    });
  });

  it("前へボタンが1ページ目で無効になる", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue(
      mockPaginatedResponse,
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("ログイン機能が欲しい")).toBeInTheDocument();
    });

    const prevButton = screen.getAllByText("前へ")[0];
    expect(prevButton).toBeDisabled();
  });

  it("次へボタンが最終ページで無効になる", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue(
      mockPaginatedResponse,
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("ログイン機能が欲しい")).toBeInTheDocument();
    });

    const nextButton = screen.getAllByText("次へ")[0];
    expect(nextButton).toBeDisabled();
  });

  it("内容を100文字で省略表示する", async () => {
    const longContentInquiry = {
      ...mockInquiries[0],
      content: "あ".repeat(150),
    };

    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue({
      ...mockPaginatedResponse,
      data: [longContentInquiry],
    });

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      const content = screen.getByText(/^あ+\.\.\.$/);
      expect(content.textContent?.length).toBeLessThanOrEqual(103); // 100 + '...'
    });
  });

  it("データがない場合でもステータスフィルターを表示する", async () => {
    // Empty response
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue({
      data: [],
      meta: {
        page: 1,
        limit: 20,
        total: 0,
        has_next: false,
      },
      timestamp: new Date().toISOString(),
    });

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("問い合わせが見つかりませんでした。"),
      ).toBeInTheDocument();
    });

    // ステータスフィルターが表示されていることを確認
    const filterSelect = screen.getByLabelText("ステータスフィルター");
    expect(filterSelect).toBeInTheDocument();
    expect(filterSelect).toBeEnabled();

    // フィルターを変更できることを確認
    fireEvent.change(filterSelect, { target: { value: "received" } });
    expect(filterSelect).toHaveValue("received");
  });

  it("エラー時でもステータスフィルターを表示する", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockRejectedValue(
      new Error("API Error"),
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(/問い合わせの読み込みに失敗しました/),
      ).toBeInTheDocument();
    });

    // エラー時でもステータスフィルターが表示されていることを確認
    const filterSelect = screen.getByLabelText("ステータスフィルター");
    expect(filterSelect).toBeInTheDocument();
    expect(filterSelect).toBeEnabled();
  });

  it("メールインポートの場合、タイトルと送信者を表示する", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue({
      data: [mockEmailInquiry],
      meta: {
        page: 1,
        limit: 20,
        total: 1,
        has_next: false,
      },
      timestamp: "2024-01-02T12:00:00Z",
    });

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("【重要】システム障害のお知らせ"),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("support@example.com")).toBeInTheDocument();
  });

  it("手動作成の場合、タイトルと送信者は「-」を表示する", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue(
      mockPaginatedResponse,
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("ログイン機能が欲しい")).toBeInTheDocument();
    });

    // タイトルと送信者の「-」が表示されていることを確認
    const dashElements = screen.getAllByText("-");
    expect(dashElements.length).toBeGreaterThanOrEqual(2);
  });

  it("テーブルヘッダーにタイトルと送信者の列が表示される", async () => {
    (inquiryApi.listInquiries as jest.Mock).mockResolvedValue(
      mockPaginatedResponse,
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <InquiryList onInquiryClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("ログイン機能が欲しい")).toBeInTheDocument();
    });

    expect(screen.getByText("タイトル")).toBeInTheDocument();
    expect(screen.getByText("送信者")).toBeInTheDocument();
  });
});

import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PromptList from "./PromptList";
import * as promptApi from "../services/promptApi";

// Mock the prompt API
jest.mock("../services/promptApi");

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const mockPrompts = [
  {
    id: 1,
    key: "story_generation_system",
    name: "ストーリー生成システムプロンプト",
    description: "ストーリー生成に使用するシステムプロンプト",
    category: "story_generation" as const,
    content: "あなたはストーリー生成AIです。",
    default_content: "あなたはストーリー生成AIです。",
    variables: ["inquiry_content", "template_content"],
    is_modified: false,
    editing_by: null,
    editing_since: null,
    created_at: "2024-01-01T10:00:00Z",
    updated_at: "2024-01-01T10:00:00Z",
  },
  {
    id: 2,
    key: "import_analysis_system",
    name: "インポート解析システムプロンプト",
    description: "インポートデータの解析に使用するシステムプロンプト",
    category: "import_analysis" as const,
    content: "あなたはデータ解析AIです。カスタマイズ済み。",
    default_content: "あなたはデータ解析AIです。",
    variables: ["raw_data"],
    is_modified: true,
    editing_by: null,
    editing_since: null,
    created_at: "2024-01-01T11:00:00Z",
    updated_at: "2024-01-02T15:00:00Z",
  },
  {
    id: 3,
    key: "general_assistant",
    name: "汎用アシスタントプロンプト",
    description: null,
    category: "general" as const,
    content: "汎用アシスタントです。",
    default_content: "汎用アシスタントです。",
    variables: [],
    is_modified: false,
    editing_by: null,
    editing_since: null,
    created_at: "2024-01-01T12:00:00Z",
    updated_at: "2024-01-01T12:00:00Z",
  },
];

const mockListResponse = {
  data: mockPrompts,
  total: 3,
};

describe("PromptList", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("プロンプト一覧を表示する", async () => {
    (promptApi.listPrompts as jest.Mock).mockResolvedValue(mockListResponse);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("ストーリー生成システムプロンプト"),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText("インポート解析システムプロンプト"),
    ).toBeInTheDocument();
    expect(screen.getByText("汎用アシスタントプロンプト")).toBeInTheDocument();
  });

  it("テーブルヘッダーに名前、カテゴリ、最終更新日時、変更状態を表示する", async () => {
    (promptApi.listPrompts as jest.Mock).mockResolvedValue(mockListResponse);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("名前")).toBeInTheDocument();
    });

    expect(screen.getByText("カテゴリ")).toBeInTheDocument();
    expect(screen.getByText("最終更新日時")).toBeInTheDocument();
    expect(screen.getByText("変更状態")).toBeInTheDocument();
  });

  it("カテゴリのラベルを日本語で表示する", async () => {
    (promptApi.listPrompts as jest.Mock).mockResolvedValue(mockListResponse);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      // フィルタードロップダウンとテーブルの両方にカテゴリラベルが表示される
      const storyGenLabels = screen.getAllByText("ストーリー生成");
      expect(storyGenLabels.length).toBeGreaterThanOrEqual(2); // filter + table
    });

    const importAnalysisLabels = screen.getAllByText("インポート解析");
    expect(importAnalysisLabels.length).toBeGreaterThanOrEqual(2);

    const generalLabels = screen.getAllByText("汎用");
    expect(generalLabels.length).toBeGreaterThanOrEqual(2);
  });

  it("デフォルトから変更されたプロンプトに変更済みバッジを表示する", async () => {
    (promptApi.listPrompts as jest.Mock).mockResolvedValue(mockListResponse);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("変更済み")).toBeInTheDocument();
    });

    // デフォルトのままのプロンプトは「デフォルト」と表示
    const defaultBadges = screen.getAllByText("デフォルト");
    expect(defaultBadges.length).toBe(2);
  });

  it("カテゴリフィルタードロップダウンを表示する", async () => {
    (promptApi.listPrompts as jest.Mock).mockResolvedValue(mockListResponse);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("ストーリー生成システムプロンプト"),
      ).toBeInTheDocument();
    });

    const filterSelect = screen.getByLabelText("カテゴリフィルター");
    expect(filterSelect).toBeInTheDocument();
  });

  it("カテゴリフィルタリングをサポートする", async () => {
    (promptApi.listPrompts as jest.Mock).mockResolvedValue(mockListResponse);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("ストーリー生成システムプロンプト"),
      ).toBeInTheDocument();
    });

    const filterSelect = screen.getByLabelText("カテゴリフィルター");
    fireEvent.change(filterSelect, {
      target: { value: "story_generation" },
    });

    await waitFor(() => {
      expect(promptApi.listPrompts).toHaveBeenCalledWith("story_generation");
    });
  });

  it("行クリックで詳細画面に遷移する", async () => {
    (promptApi.listPrompts as jest.Mock).mockResolvedValue(mockListResponse);

    const handlePromptClick = jest.fn();
    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={handlePromptClick} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("ストーリー生成システムプロンプト"),
      ).toBeInTheDocument();
    });

    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");
    // Skip header row (index 0), click first data row (index 1)
    fireEvent.click(rows[1]);

    expect(handlePromptClick).toHaveBeenCalledWith("story_generation_system");
  });

  it("キーボードナビゲーション（Enter/Space）で詳細画面に遷移する", async () => {
    (promptApi.listPrompts as jest.Mock).mockResolvedValue(mockListResponse);

    const handlePromptClick = jest.fn();
    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={handlePromptClick} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("ストーリー生成システムプロンプト"),
      ).toBeInTheDocument();
    });

    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");
    fireEvent.keyDown(rows[1], { key: "Enter" });

    expect(handlePromptClick).toHaveBeenCalledWith("story_generation_system");
  });

  it("ローディング状態を表示する", () => {
    (promptApi.listPrompts as jest.Mock).mockImplementation(
      () => new Promise(() => {}), // Never resolves
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={jest.fn()} />
      </QueryClientProvider>,
    );

    expect(screen.getByText("読み込み中...")).toBeInTheDocument();
  });

  it("エラー状態を表示する", async () => {
    (promptApi.listPrompts as jest.Mock).mockRejectedValue(
      new Error("API Error"),
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(/プロンプトの読み込みに失敗しました/),
      ).toBeInTheDocument();
    });
  });

  it("データがない場合でもカテゴリフィルターを表示する", async () => {
    (promptApi.listPrompts as jest.Mock).mockResolvedValue({
      data: [],
      total: 0,
    });

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("プロンプトが見つかりませんでした。"),
      ).toBeInTheDocument();
    });

    const filterSelect = screen.getByLabelText("カテゴリフィルター");
    expect(filterSelect).toBeInTheDocument();
    expect(filterSelect).toBeEnabled();
  });

  it("エラー時でもカテゴリフィルターを表示する", async () => {
    (promptApi.listPrompts as jest.Mock).mockRejectedValue(
      new Error("API Error"),
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptList onPromptClick={jest.fn()} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(/プロンプトの読み込みに失敗しました/),
      ).toBeInTheDocument();
    });

    const filterSelect = screen.getByLabelText("カテゴリフィルター");
    expect(filterSelect).toBeInTheDocument();
    expect(filterSelect).toBeEnabled();
  });
});

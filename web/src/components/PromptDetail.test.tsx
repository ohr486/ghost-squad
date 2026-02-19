import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PromptDetail from "./PromptDetail";
import * as promptApi from "../services/promptApi";

// Mock the prompt API
jest.mock("../services/promptApi");

// Mock react-hot-toast
jest.mock("react-hot-toast", () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const mockPrompt = {
  id: 1,
  key: "story_generation_system",
  name: "ストーリー生成システムプロンプト",
  description: "ストーリー生成に使用するシステムプロンプト",
  category: "story_generation" as const,
  content: "あなたはストーリー生成AIです。\n{inquiry_content}\n{template_content}",
  default_content:
    "あなたはストーリー生成AIです。\n{inquiry_content}\n{template_content}",
  variables: ["inquiry_content", "template_content"],
  is_modified: false,
  editing_by: null,
  editing_since: null,
  created_at: "2024-01-01T10:00:00Z",
  updated_at: "2024-01-01T10:00:00Z",
};

const mockModifiedPrompt = {
  ...mockPrompt,
  content: "カスタマイズされたプロンプト\n{inquiry_content}",
  is_modified: true,
  updated_at: "2024-01-02T15:00:00Z",
};

const mockLockedPrompt = {
  ...mockPrompt,
  editing_by: "other_user",
  editing_since: "2024-01-01T12:00:00Z",
};

describe("PromptDetail", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // =========================================================================
  // 詳細表示テスト（要件1.2）
  // =========================================================================

  it("プロンプトの詳細情報を表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("プロンプト詳細")).toBeInTheDocument();
    });

    expect(
      screen.getByText("ストーリー生成システムプロンプト"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("ストーリー生成に使用するシステムプロンプト"),
    ).toBeInTheDocument();
    expect(screen.getByText("story_generation_system")).toBeInTheDocument();
  });

  it("プロンプトの変数リストを表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      // 変数セクションとテスト実行パネルの両方に表示される
      const inquiryLabels = screen.getAllByText("inquiry_content");
      expect(inquiryLabels.length).toBeGreaterThanOrEqual(2);
    });

    const templateLabels = screen.getAllByText("template_content");
    expect(templateLabels.length).toBeGreaterThanOrEqual(2);
  });

  it("デフォルトから変更されていないプロンプトにデフォルトバッジを表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      // 変更状態バッジとプロバイダー選択のデフォルトオプションの両方に表示される
      const defaultLabels = screen.getAllByText("デフォルト");
      expect(defaultLabels.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("デフォルトから変更されたプロンプトに変更済みバッジを表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockModifiedPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("変更済み")).toBeInTheDocument();
    });
  });

  // =========================================================================
  // 編集モードテスト（要件2.1, 2.2）
  // =========================================================================

  it("編集ボタンクリックで編集モードに切り替わる", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);
    (promptApi.acquireLock as jest.Mock).mockResolvedValue({
      acquired: true,
      locked_by: "current_user",
      locked_since: new Date().toISOString(),
    });

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("編集")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("編集"));

    await waitFor(() => {
      expect(
        screen.getByLabelText("プロンプト本文を編集"),
      ).toBeInTheDocument();
    });
  });

  it("編集モードで保存ボタンとキャンセルボタンを表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);
    (promptApi.acquireLock as jest.Mock).mockResolvedValue({
      acquired: true,
      locked_by: "current_user",
      locked_since: new Date().toISOString(),
    });

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("編集")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("編集"));

    await waitFor(() => {
      expect(screen.getByText("保存")).toBeInTheDocument();
    });
    expect(screen.getByText("キャンセル")).toBeInTheDocument();
  });

  it("編集内容を保存できる", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);
    (promptApi.acquireLock as jest.Mock).mockResolvedValue({
      acquired: true,
      locked_by: "current_user",
      locked_since: new Date().toISOString(),
    });
    (promptApi.updatePrompt as jest.Mock).mockResolvedValue({
      ...mockPrompt,
      content: "更新されたプロンプト",
    });
    (promptApi.releaseLock as jest.Mock).mockResolvedValue(undefined);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("編集")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("編集"));

    await waitFor(() => {
      expect(
        screen.getByLabelText("プロンプト本文を編集"),
      ).toBeInTheDocument();
    });

    const textarea = screen.getByLabelText("プロンプト本文を編集");
    fireEvent.change(textarea, { target: { value: "更新されたプロンプト" } });
    fireEvent.click(screen.getByText("保存"));

    await waitFor(() => {
      expect(promptApi.updatePrompt).toHaveBeenCalledWith(
        "story_generation_system",
        { content: "更新されたプロンプト" },
      );
    });
  });

  it("キャンセルボタンで編集モードを終了する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);
    (promptApi.acquireLock as jest.Mock).mockResolvedValue({
      acquired: true,
      locked_by: "current_user",
      locked_since: new Date().toISOString(),
    });
    (promptApi.releaseLock as jest.Mock).mockResolvedValue(undefined);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("編集")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("編集"));

    await waitFor(() => {
      expect(screen.getByText("キャンセル")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("キャンセル"));

    await waitFor(() => {
      expect(screen.getByText("編集")).toBeInTheDocument();
    });
  });

  // =========================================================================
  // 編集ロックテスト（要件2.5）
  // =========================================================================

  it("他のユーザーが編集中の場合に警告を表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockLockedPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/other_user.*が編集中/)).toBeInTheDocument();
    });
  });

  // =========================================================================
  // ローディング・エラーテスト
  // =========================================================================

  it("ローディング状態を表示する", () => {
    (promptApi.getPrompt as jest.Mock).mockImplementation(
      () => new Promise(() => {}),
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    expect(screen.getByText("読み込み中...")).toBeInTheDocument();
  });

  it("エラー状態を表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockRejectedValue(
      new Error("API Error"),
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("プロンプトの取得に失敗しました"),
      ).toBeInTheDocument();
    });
  });

  // =========================================================================
  // テスト実行テスト（要件3.1, 3.2, 3.3, 3.4）
  // =========================================================================

  it("テスト実行パネルを表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("テスト実行")).toBeInTheDocument();
    });
  });

  it("テスト実行で変数入力フィールドを表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("テスト実行")).toBeInTheDocument();
    });

    expect(
      screen.getByLabelText("inquiry_content"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("template_content"),
    ).toBeInTheDocument();
  });

  it("AIプロバイダー選択を表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByLabelText("AIプロバイダー")).toBeInTheDocument();
    });
  });

  it("テスト実行ボタンをクリックするとAPIを呼び出す", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);
    (promptApi.testPrompt as jest.Mock).mockResolvedValue({
      output: "テスト結果の出力",
      provider: "openai",
      model: "gpt-4",
      elapsed_ms: 1500,
    });

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("テスト実行")).toBeInTheDocument();
    });

    // 変数を入力
    const inquiryInput = screen.getByLabelText("inquiry_content");
    fireEvent.change(inquiryInput, { target: { value: "テスト問い合わせ" } });

    // 実行ボタンをクリック
    fireEvent.click(screen.getByText("実行"));

    await waitFor(() => {
      expect(promptApi.testPrompt).toHaveBeenCalled();
    });
  });

  it("テスト実行結果を表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);
    (promptApi.testPrompt as jest.Mock).mockResolvedValue({
      output: "テスト結果の出力",
      provider: "openai",
      model: "gpt-4",
      elapsed_ms: 1500,
    });

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("テスト実行")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("実行"));

    await waitFor(() => {
      expect(screen.getByText("テスト結果の出力")).toBeInTheDocument();
    });

    expect(screen.getByText(/openai/)).toBeInTheDocument();
    expect(screen.getByText(/gpt-4/)).toBeInTheDocument();
    expect(screen.getByText(/1500ms/)).toBeInTheDocument();
  });

  it("テスト実行中にローディングインジケーターを表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);
    (promptApi.testPrompt as jest.Mock).mockImplementation(
      () => new Promise(() => {}), // Never resolves
    );

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("テスト実行")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("実行"));

    await waitFor(() => {
      expect(screen.getByText("実行中...")).toBeInTheDocument();
    });
  });

  // =========================================================================
  // デフォルトリセットテスト（要件4.4, 4.5, 4.6）
  // =========================================================================

  it("変更済みプロンプトにリセットボタンを表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockModifiedPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("デフォルトにリセット")).toBeInTheDocument();
    });
  });

  it("デフォルトのプロンプトにはリセットボタンを表示しない", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("プロンプト詳細")).toBeInTheDocument();
    });

    expect(
      screen.queryByText("デフォルトにリセット"),
    ).not.toBeInTheDocument();
  });

  it("リセットボタンクリックで確認ダイアログを表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockModifiedPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("デフォルトにリセット")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("デフォルトにリセット"));

    await waitFor(() => {
      expect(
        screen.getByText("デフォルトにリセットしますか？"),
      ).toBeInTheDocument();
    });
  });

  it("リセット確認ダイアログで現在の内容とデフォルト内容を表示する", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockModifiedPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("デフォルトにリセット")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("デフォルトにリセット"));

    await waitFor(() => {
      expect(screen.getByText("現在の内容:")).toBeInTheDocument();
    });
    expect(screen.getByText("デフォルト内容:")).toBeInTheDocument();
  });

  it("リセット確認でAPIを呼び出す", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockModifiedPrompt);
    (promptApi.resetPrompt as jest.Mock).mockResolvedValue({
      ...mockPrompt,
      is_modified: false,
    });

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("デフォルトにリセット")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("デフォルトにリセット"));

    await waitFor(() => {
      expect(
        screen.getByText("デフォルトにリセットしますか？"),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("リセット実行"));

    await waitFor(() => {
      expect(promptApi.resetPrompt).toHaveBeenCalledWith(
        "story_generation_system",
      );
    });
  });

  it("リセット確認ダイアログでキャンセルできる", async () => {
    (promptApi.getPrompt as jest.Mock).mockResolvedValue(mockModifiedPrompt);

    const queryClient = createQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PromptDetail promptKey="story_generation_system" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("デフォルトにリセット")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("デフォルトにリセット"));

    await waitFor(() => {
      expect(
        screen.getByText("デフォルトにリセットしますか？"),
      ).toBeInTheDocument();
    });

    // ダイアログ内のキャンセルボタン
    const dialog = screen.getByRole("dialog");
    const cancelButton = within(dialog).getByText("キャンセル");
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(
        screen.queryByText("デフォルトにリセットしますか？"),
      ).not.toBeInTheDocument();
    });
  });
});

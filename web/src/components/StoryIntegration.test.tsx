/**
 * ストーリー機能 統合テスト（E2E）
 *
 * クリティカルパスの検証:
 * - ストーリー生成フロー（問い合わせ選択 → AI生成 → レビュー待ち表示）
 * - 手動作成フロー（フォーム入力 → 作成 → 詳細ページ遷移）
 * - ストーリー承認・却下フロー（モーダル → 確認 → ステータス更新）
 *
 * 要件: 1.1, 1.5, 2.11, 2.14, 3.1, 3.4, 5.21
 */

import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import toast from "react-hot-toast";
import InquiryDetail from "./InquiryDetail";
import StoryDetail from "./StoryDetail";
import StoryList from "./StoryList";
import { StoryForm } from "./StoryForm";
import * as inquiryApi from "../services/inquiryApi";
import * as storyApi from "../services/storyApi";
import type {
  InquiryResponse,
  StoryResponse,
  StoryStatus,
  Priority,
} from "../types";

// Mock APIs
jest.mock("../services/inquiryApi");
jest.mock("../services/storyApi");
jest.mock("react-hot-toast");

const mockInquiryApi = inquiryApi as jest.Mocked<typeof inquiryApi>;
const mockStoryApi = storyApi as jest.Mocked<typeof storyApi>;

describe("Story Integration Tests - Critical Paths", () => {
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
  const mockInquiry: InquiryResponse = {
    id: 1,
    user_id: "test_user",
    content: "ログイン機能の改善について問い合わせします",
    source_system: "manual",
    timestamp: "2025-01-01T00:00:00Z",
    status: "task_working",
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  };

  const mockStory: StoryResponse = {
    id: 1,
    inquiry_id: 1,
    title: "ログイン機能の改善",
    description:
      "ユーザーがログイン時にエラーメッセージを明確に表示できるようにする",
    priority: "medium" as Priority,
    status: "waiting_review" as StoryStatus,
    estimated_effort: 8,
    deadline: null,
    assignee: null,
    story_metadata: {},
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  };

  /**
   * E2E テスト 1: ストーリー生成フロー
   *
   * フロー: 問い合わせ詳細ページ → AI生成ボタンクリック → ストーリー生成成功 → レビュー待ちステータス表示
   * 要件: 1.1, 1.5
   */
  describe("Story Generation Flow", () => {
    test("generates story from inquiry and displays waiting_review status", async () => {
      // Arrange: task_working状態の問い合わせを表示
      mockInquiryApi.getInquiry.mockResolvedValue(mockInquiry);
      mockStoryApi.generateStory.mockResolvedValue(mockStory);

      render(
        <QueryClientProvider client={queryClient}>
          <InquiryDetail inquiryId={1} />
        </QueryClientProvider>,
      );

      // Assert: 問い合わせ詳細が表示される
      await waitFor(() => {
        expect(
          screen.getByText("ログイン機能の改善について問い合わせします"),
        ).toBeInTheDocument();
      });

      // Assert: ストーリー生成ボタンが表示される（task_working状態）
      const generateButton = screen.getByRole("button", {
        name: /ストーリー生成/,
      });
      expect(generateButton).toBeInTheDocument();

      // Act: ストーリー生成ボタンをクリック
      fireEvent.click(generateButton);

      // Assert: API呼び出しとトースト表示を確認
      await waitFor(() => {
        expect(mockStoryApi.generateStory).toHaveBeenCalledWith(1);
      });

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("ストーリーを生成しました");
      });
    });

    test("displays generated story with waiting_review status in story list", async () => {
      // Arrange: 生成されたストーリー一覧をモック
      mockStoryApi.listStories.mockResolvedValue({
        data: [mockStory],
        meta: {
          page: 1,
          limit: 20,
          total: 1,
          has_next: false,
        },
        timestamp: new Date().toISOString(),
      });

      render(
        <QueryClientProvider client={queryClient}>
          <StoryList
            onStoryClick={jest.fn()}
            onCreateStoryClick={jest.fn()}
          />
        </QueryClientProvider>,
      );

      // Assert: ストーリー一覧にレビュー待ちステータスで表示される
      await waitFor(() => {
        expect(screen.getByText("ログイン機能の改善")).toBeInTheDocument();
      });

      // レビュー待ちはフィルタードロップダウンとテーブル両方に表示されるためgetAllByTextを使用
      const waitingReviewElements = screen.getAllByText("レビュー待ち");
      expect(waitingReviewElements.length).toBeGreaterThanOrEqual(1);
    });
  });

  /**
   * E2E テスト 2: 手動作成フロー
   *
   * フロー: ストーリー作成フォーム → 入力 → 作成 → 成功メッセージ表示
   * 要件: 2.11, 2.14, 5.21
   */
  describe("Manual Creation Flow", () => {
    test("creates story manually with form input and shows success message", async () => {
      // Arrange: 問い合わせ一覧とモック
      const mockInquiries: InquiryResponse[] = [mockInquiry];
      const mockOnSubmit = jest.fn().mockResolvedValue(undefined);
      const mockOnClose = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <StoryForm
            isOpen={true}
            inquiries={mockInquiries}
            onSubmit={mockOnSubmit}
            onClose={mockOnClose}
            onCancel={jest.fn()}
          />
        </QueryClientProvider>,
      );

      // Assert: フォームが表示される
      expect(screen.getByText("新規ストーリー作成")).toBeInTheDocument();

      // Act: フォーム入力
      // 問い合わせ選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/);
      fireEvent.change(inquirySelect, { target: { value: "1" } });

      // タイトル入力
      const titleInput = screen.getByLabelText(/タイトル/);
      fireEvent.change(titleInput, { target: { value: "テストストーリー" } });

      // 説明入力
      const descriptionInput = screen.getByLabelText(/説明/);
      fireEvent.change(descriptionInput, {
        target: { value: "テスト説明文です" },
      });

      // 優先度選択（デフォルトは中）

      // Act: 作成ボタンクリック
      const submitButton = screen.getByRole("button", { name: /作成/ });
      fireEvent.click(submitButton);

      // Assert: onSubmitが呼ばれる
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          1,
          expect.objectContaining({
            title: "テストストーリー",
            description: "テスト説明文です",
            priority: "medium",
          }),
        );
      });
    });

    test("shows validation error when required fields are empty", async () => {
      const mockOnSubmit = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <StoryForm
            isOpen={true}
            inquiries={[mockInquiry]}
            onSubmit={mockOnSubmit}
            onClose={jest.fn()}
            onCancel={jest.fn()}
          />
        </QueryClientProvider>,
      );

      // Act: 何も入力せずに作成ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/ });
      fireEvent.click(submitButton);

      // Assert: バリデーションエラーが表示される（すべてのエラーが同時に表示されるのを待つ）
      await waitFor(() => {
        expect(screen.getByText("問い合わせを選択してください")).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText("タイトルは必須です")).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText("説明は必須です")).toBeInTheDocument();
      });

      // Assert: onSubmitは呼ばれない
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  /**
   * E2E テスト 3: ストーリー承認フロー
   *
   * フロー: ストーリー詳細ページ → 承認ボタン → 確認ダイアログ → 承認完了 → ステータス更新
   * 要件: 3.1
   */
  describe("Story Approval Flow", () => {
    test("approves story through confirmation dialog and updates status", async () => {
      const approvedStory: StoryResponse = {
        ...mockStory,
        status: "approved" as StoryStatus,
        story_metadata: {
          approval: {
            approved_at: "2025-01-02T00:00:00Z",
            approver: "current_user",
          },
        },
      };

      mockStoryApi.getStory
        .mockResolvedValueOnce(mockStory)
        .mockResolvedValueOnce(approvedStory);
      mockStoryApi.approveStory.mockResolvedValue(approvedStory);

      render(
        <QueryClientProvider client={queryClient}>
          <StoryDetail storyId={1} />
        </QueryClientProvider>,
      );

      // Assert: ストーリー詳細が表示される
      await waitFor(() => {
        expect(screen.getByText("ログイン機能の改善")).toBeInTheDocument();
      });

      // Assert: レビュー待ちステータスで承認ボタンが表示される
      expect(screen.getByText("レビュー待ち")).toBeInTheDocument();
      const approveButton = screen.getByRole("button", { name: /承認/ });
      expect(approveButton).toBeInTheDocument();

      // Act: 承認ボタンをクリック
      fireEvent.click(approveButton);

      // Assert: 確認ダイアログが表示される
      expect(screen.getByText("ストーリーの承認")).toBeInTheDocument();
      expect(
        screen.getByText("このストーリーを承認してもよろしいですか？"),
      ).toBeInTheDocument();

      // Act: 確認ボタンをクリック
      const confirmButton = screen.getByRole("button", { name: /確認/ });
      fireEvent.click(confirmButton);

      // Assert: API呼び出しと成功メッセージ
      await waitFor(() => {
        expect(mockStoryApi.approveStory).toHaveBeenCalledWith(1, {
          approver: "current_user",
        });
      });

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("ストーリーを承認しました");
      });
    });
  });

  /**
   * E2E テスト 4: ストーリー却下フロー
   *
   * フロー: ストーリー詳細ページ → 却下ボタン → 理由入力モーダル → 却下完了 → ステータス更新
   * 要件: 3.4
   */
  describe("Story Rejection Flow", () => {
    test("rejects story with reason through modal and updates status", async () => {
      const rejectedStory: StoryResponse = {
        ...mockStory,
        status: "rejected" as StoryStatus,
        story_metadata: {
          rejection: {
            rejected_at: "2025-01-02T00:00:00Z",
            rejector: "current_user",
            reason: "要件が不十分です",
          },
        },
      };

      mockStoryApi.getStory
        .mockResolvedValueOnce(mockStory)
        .mockResolvedValueOnce(rejectedStory);
      mockStoryApi.rejectStory.mockResolvedValue(rejectedStory);

      render(
        <QueryClientProvider client={queryClient}>
          <StoryDetail storyId={1} />
        </QueryClientProvider>,
      );

      // Assert: ストーリー詳細が表示される
      await waitFor(() => {
        expect(screen.getByText("ログイン機能の改善")).toBeInTheDocument();
      });

      // Act: 却下ボタンをクリック
      const rejectButton = screen.getByRole("button", { name: /却下/ });
      fireEvent.click(rejectButton);

      // Assert: 却下理由入力モーダルが表示される
      expect(screen.getByText("ストーリーの却下")).toBeInTheDocument();
      const reasonInput = screen.getByLabelText(/却下理由/);
      expect(reasonInput).toBeInTheDocument();

      // Act: 却下理由を入力
      fireEvent.change(reasonInput, { target: { value: "要件が不十分です" } });

      // Act: 確認ボタンをクリック
      const confirmButton = screen.getByRole("button", { name: /確認/ });
      fireEvent.click(confirmButton);

      // Assert: API呼び出しと成功メッセージ
      await waitFor(() => {
        expect(mockStoryApi.rejectStory).toHaveBeenCalledWith(1, {
          rejector: "current_user",
          reason: "要件が不十分です",
        });
      });

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("ストーリーを却下しました");
      });
    });

    test("shows validation error when reject reason is empty", async () => {
      mockStoryApi.getStory.mockResolvedValue(mockStory);

      render(
        <QueryClientProvider client={queryClient}>
          <StoryDetail storyId={1} />
        </QueryClientProvider>,
      );

      // Assert: ストーリー詳細が表示される
      await waitFor(() => {
        expect(screen.getByText("ログイン機能の改善")).toBeInTheDocument();
      });

      // Act: 却下ボタンをクリック
      const rejectButton = screen.getByRole("button", { name: /却下/ });
      fireEvent.click(rejectButton);

      // Act: 理由を入力せずに確認ボタンをクリック
      const confirmButton = screen.getByRole("button", { name: /確認/ });
      fireEvent.click(confirmButton);

      // Assert: バリデーションエラーが表示される
      await waitFor(() => {
        expect(screen.getByText("却下理由は必須です")).toBeInTheDocument();
      });

      // Assert: APIは呼び出されない
      expect(mockStoryApi.rejectStory).not.toHaveBeenCalled();
    });
  });

  /**
   * E2E テスト 5: ストーリー一覧からの詳細遷移
   *
   * フロー: ストーリー一覧 → 行クリック → onStoryClickコールバック実行
   */
  describe("Story List to Detail Navigation", () => {
    test("navigates to story detail when clicking on a story row", async () => {
      const mockOnStoryClick = jest.fn();
      mockStoryApi.listStories.mockResolvedValue({
        data: [mockStory],
        meta: {
          page: 1,
          limit: 20,
          total: 1,
          has_next: false,
        },
        timestamp: new Date().toISOString(),
      });

      render(
        <QueryClientProvider client={queryClient}>
          <StoryList
            onStoryClick={mockOnStoryClick}
            onCreateStoryClick={jest.fn()}
          />
        </QueryClientProvider>,
      );

      // Assert: ストーリー一覧が表示される
      await waitFor(() => {
        expect(screen.getByText("ログイン機能の改善")).toBeInTheDocument();
      });

      // Act: ストーリータイトルをクリック（イベントは親の行にバブルアップ）
      fireEvent.click(screen.getByText("ログイン機能の改善"));

      // Assert: onStoryClickが呼ばれる
      expect(mockOnStoryClick).toHaveBeenCalledWith(1);
    });
  });

  /**
   * E2E テスト 6: ステータスに応じたボタン表示
   *
   * 承認済みストーリーでは承認・却下ボタンが非表示になることを確認
   */
  describe("Status-based UI behavior", () => {
    test("hides approve/reject buttons for approved stories", async () => {
      const approvedStory: StoryResponse = {
        ...mockStory,
        status: "approved" as StoryStatus,
        story_metadata: {
          approval: {
            approved_at: "2025-01-02T00:00:00Z",
            approver: "admin",
          },
        },
      };

      mockStoryApi.getStory.mockResolvedValue(approvedStory);

      render(
        <QueryClientProvider client={queryClient}>
          <StoryDetail storyId={1} />
        </QueryClientProvider>,
      );

      // Assert: ストーリー詳細が表示される
      await waitFor(() => {
        expect(screen.getByText("ログイン機能の改善")).toBeInTheDocument();
      });

      // Assert: 承認済みステータスが表示される
      expect(screen.getByText("承認済み")).toBeInTheDocument();

      // Assert: 承認・却下ボタンが非表示
      expect(
        screen.queryByRole("button", { name: /承認/ }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /却下/ }),
      ).not.toBeInTheDocument();

      // Assert: 承認情報が表示される
      expect(screen.getByText("承認情報")).toBeInTheDocument();
      expect(screen.getByText("admin")).toBeInTheDocument();
    });

    test("hides approve/reject buttons for rejected stories", async () => {
      const rejectedStory: StoryResponse = {
        ...mockStory,
        status: "rejected" as StoryStatus,
        story_metadata: {
          rejection: {
            rejected_at: "2025-01-02T00:00:00Z",
            rejector: "admin",
            reason: "不適切な内容",
          },
        },
      };

      mockStoryApi.getStory.mockResolvedValue(rejectedStory);

      render(
        <QueryClientProvider client={queryClient}>
          <StoryDetail storyId={1} />
        </QueryClientProvider>,
      );

      // Assert: ストーリー詳細が表示される
      await waitFor(() => {
        expect(screen.getByText("ログイン機能の改善")).toBeInTheDocument();
      });

      // Assert: 却下ステータスが表示される
      expect(screen.getByText("却下")).toBeInTheDocument();

      // Assert: 承認・却下ボタンが非表示
      expect(
        screen.queryByRole("button", { name: /^承認$/ }),
      ).not.toBeInTheDocument();
      // 却下ボタンは「却下」テキストがヘッダーにもあるのでボタンロールでチェック
      const rejectButtons = screen.queryAllByRole("button", { name: /却下/ });
      expect(rejectButtons).toHaveLength(0);

      // Assert: 却下情報が表示される
      expect(screen.getByText("却下情報")).toBeInTheDocument();
      expect(screen.getByText("不適切な内容")).toBeInTheDocument();
    });
  });
});

/**
 * StoryFormコンポーネント テスト
 *
 * 要件: 2.11, 2.12, 2.13, 5.15, 5.16, 5.17, 5.18, 5.19, 5.20, 5.21, 5.22
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StoryForm, StoryFormProps } from "./StoryForm";
import type {
  CreateStoryRequest,
  ErrorResponse,
  InquiryResponse,
} from "../types";

// React Hot Toastのモック
jest.mock("react-hot-toast", () => {
  const mockToast: any = jest.fn();
  mockToast.success = jest.fn();
  mockToast.error = jest.fn();
  return {
    __esModule: true,
    default: mockToast,
    toast: mockToast,
    Toaster: () => null,
  };
});

// テスト用の問い合わせデータ
const mockInquiries: InquiryResponse[] = [
  {
    id: 1,
    user_id: "user_001",
    content: "ログイン機能を追加してほしい",
    source_system: "manual",
    timestamp: "2024-01-01T00:00:00Z",
    status: "task_working",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    user_id: "user_002",
    content: "検索機能の改善をお願いします",
    source_system: "email",
    timestamp: "2024-01-02T00:00:00Z",
    status: "received",
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
  {
    id: 3,
    user_id: "user_003",
    content: "エラーハンドリングの強化が必要",
    source_system: "manual",
    timestamp: "2024-01-03T00:00:00Z",
    status: "completed",
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-03T00:00:00Z",
  },
];

describe("StoryForm", () => {
  // テストユーティリティ
  let user: ReturnType<typeof userEvent.setup>;

  // モック関数
  let mockOnSubmit: jest.Mock<
    Promise<void>,
    [number, CreateStoryRequest | undefined]
  >;
  let mockOnCancel: jest.Mock;

  // デフォルトのプロパティ
  const defaultProps: StoryFormProps = {
    inquiries: mockInquiries,
    onSubmit: jest.fn(),
  };

  beforeEach(() => {
    user = userEvent.setup();
    mockOnSubmit = jest.fn();
    mockOnCancel = jest.fn();
    jest.clearAllMocks();
  });

  describe("レンダリング", () => {
    test("モーダルダイアログとしてフォームが表示されること", () => {
      render(<StoryForm {...defaultProps} isOpen={true} />);

      // モーダルが表示されること
      expect(
        screen.getByRole("dialog", { name: /新規ストーリー作成/i }),
      ).toBeInTheDocument();

      // フォームタイトルが表示されること
      expect(screen.getByText(/新規ストーリー作成/i)).toBeInTheDocument();
    });

    test("isOpenがfalseの場合、モーダルが表示されないこと", () => {
      render(<StoryForm {...defaultProps} isOpen={false} />);

      // モーダルが表示されないこと
      expect(
        screen.queryByRole("dialog", { name: /新規ストーリー作成/i }),
      ).not.toBeInTheDocument();
    });

    test("必要なフォームフィールドがすべて表示されること", () => {
      render(<StoryForm {...defaultProps} isOpen={true} />);

      // 問い合わせ選択フィールド
      expect(screen.getByLabelText(/問い合わせ/i)).toBeInTheDocument();

      // タイトルフィールド
      expect(screen.getByLabelText(/タイトル/i)).toBeInTheDocument();

      // 説明フィールド
      expect(screen.getByLabelText(/説明/i)).toBeInTheDocument();

      // 優先度フィールド
      expect(screen.getByLabelText(/優先度/i)).toBeInTheDocument();

      // 推定工数フィールド（オプショナル）
      expect(screen.getByLabelText(/推定工数/i)).toBeInTheDocument();

      // 担当者フィールド（オプショナル）
      expect(screen.getByLabelText(/担当者/i)).toBeInTheDocument();

      // 期限フィールド（オプショナル）
      expect(screen.getByLabelText(/期限/i)).toBeInTheDocument();
    });

    test("送信ボタンとキャンセルボタンが表示されること", () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onCancel={mockOnCancel} />,
      );

      expect(screen.getByRole("button", { name: /作成/i })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /キャンセル/i }),
      ).toBeInTheDocument();
    });
  });

  describe("問い合わせ選択", () => {
    test("問い合わせリストがドロップダウンで表示されること", async () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせ選択フィールドをクリック
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.click(inquirySelect);

      // すべての問い合わせが表示されること
      expect(
        screen.getByText(/ログイン機能を追加してほしい/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/検索機能の改善をお願いします/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/エラーハンドリングの強化が必要/i),
      ).toBeInTheDocument();
    });

    test("問い合わせを選択すると、タイトルとステータスがプレビュー表示されること", async () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択（selectを変更）
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // プレビュー表示を確認（ステータス表示）
      await waitFor(() => {
        expect(screen.getByText(/タスク作業中/i)).toBeInTheDocument();
      });
    });

    test("問い合わせが選択されていない場合、フォームを送信できないこと", async () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 他のフィールドを入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      const descriptionTextarea = screen.getByLabelText(/説明/i);

      await user.type(titleInput, "テストストーリー");
      await user.type(descriptionTextarea, "テストの説明です");

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // バリデーションエラーが表示されること
      await waitFor(() => {
        expect(
          screen.getByText(/問い合わせを選択してください/i),
        ).toBeInTheDocument();
      });

      // onSubmitが呼ばれていないこと
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    test("問い合わせリストが空の場合、プレースホルダーのみ表示されること", () => {
      const emptyInquiriesProps: StoryFormProps = {
        ...defaultProps,
        inquiries: [],
      };

      render(<StoryForm {...emptyInquiriesProps} isOpen={true} />);

      // ドロップダウンを取得
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);

      // プレースホルダーオプションのみ存在すること
      const options = inquirySelect.querySelectorAll("option");
      expect(options).toHaveLength(1);
      expect(options[0]).toHaveTextContent("問い合わせを選択してください");
    });
  });

  describe("バリデーション", () => {
    test("タイトルが空の場合、バリデーションエラーが表示されること", async () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // 説明のみ入力し、タイトルは空のまま
      const descriptionTextarea = screen.getByLabelText(/説明/i);
      await user.type(descriptionTextarea, "テストの説明です");

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // バリデーションエラーメッセージが表示されること
      await waitFor(() => {
        expect(screen.getByText(/タイトルは必須です/i)).toBeInTheDocument();
      });

      // onSubmitが呼ばれていないこと
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    test("タイトルが500文字を超える場合、バリデーションエラーが表示されること", async () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // 501文字のタイトルを入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      const longTitle = "あ".repeat(501);
      await user.click(titleInput);
      await user.paste(longTitle);

      const descriptionTextarea = screen.getByLabelText(/説明/i);
      await user.type(descriptionTextarea, "テストの説明です");

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // バリデーションエラーメッセージが表示されること
      await waitFor(() => {
        expect(
          screen.getByText(/タイトルは500文字以内で入力してください/i),
        ).toBeInTheDocument();
      });

      // onSubmitが呼ばれていないこと
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    test("説明が空の場合、バリデーションエラーが表示されること", async () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // タイトルのみ入力し、説明は空のまま
      const titleInput = screen.getByLabelText(/タイトル/i);
      await user.type(titleInput, "テストストーリー");

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // バリデーションエラーメッセージが表示されること
      await waitFor(() => {
        expect(screen.getByText(/説明は必須です/i)).toBeInTheDocument();
      });

      // onSubmitが呼ばれていないこと
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    test("推定工数が負の値の場合、バリデーションエラーが表示されること", async () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // フォームに入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      const descriptionTextarea = screen.getByLabelText(/説明/i);
      const estimatedEffortInput = screen.getByLabelText(/推定工数/i);

      await user.type(titleInput, "テストストーリー");
      await user.type(descriptionTextarea, "テストの説明です");
      await user.clear(estimatedEffortInput);
      await user.type(estimatedEffortInput, "-1");

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // バリデーションエラーメッセージが表示されること
      await waitFor(() => {
        expect(
          screen.getByText(/推定工数は0以上の数値を入力してください/i),
        ).toBeInTheDocument();
      });

      // onSubmitが呼ばれていないこと
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    test("担当者が50文字を超える場合、バリデーションエラーが表示されること", async () => {
      const ASSIGNEE_MAX_LENGTH_PLUS_ONE = 51;

      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // フォームに入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      const descriptionTextarea = screen.getByLabelText(/説明/i);
      const assigneeInput = screen.getByLabelText(/担当者/i);

      await user.type(titleInput, "テストストーリー");
      await user.type(descriptionTextarea, "テストの説明です");
      // 最大長を超える担当者名を入力（50文字を超える51文字）
      await user.type(assigneeInput, "a".repeat(ASSIGNEE_MAX_LENGTH_PLUS_ONE));

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // バリデーションエラーメッセージが表示されること
      await waitFor(() => {
        expect(
          screen.getByText(/担当者は50文字以内で入力してください/i),
        ).toBeInTheDocument();
      });

      // onSubmitが呼ばれていないこと
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe("フォーム送信", () => {
    test("正常なフォーム送信が成功すること", async () => {
      mockOnSubmit.mockResolvedValue(undefined);

      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // フォームに入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      const descriptionTextarea = screen.getByLabelText(/説明/i);

      await user.type(titleInput, "ログイン機能の実装");
      await user.type(
        descriptionTextarea,
        "ユーザーがメールとパスワードでログインできる機能を実装する",
      );

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // onSubmitが正しいデータで呼ばれることを確認
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(1, {
          title: "ログイン機能の実装",
          description:
            "ユーザーがメールとパスワードでログインできる機能を実装する",
          priority: "medium", // デフォルト値
        });
      });
    });

    test("オプションフィールドを含む正常なフォーム送信が成功すること", async () => {
      mockOnSubmit.mockResolvedValue(undefined);

      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // フォームに入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      const descriptionTextarea = screen.getByLabelText(/説明/i);
      const prioritySelect = screen.getByLabelText(/優先度/i);
      const estimatedEffortInput = screen.getByLabelText(/推定工数/i);
      const assigneeInput = screen.getByLabelText(/担当者/i);
      const deadlineInput = screen.getByLabelText(/期限/i);

      await user.type(titleInput, "ログイン機能の実装");
      await user.type(descriptionTextarea, "詳細な説明");

      // 優先度を選択
      await user.selectOptions(prioritySelect, "high");

      await user.type(estimatedEffortInput, "8");
      await user.type(assigneeInput, "developer_001");
      await user.type(deadlineInput, "2027-12-31");

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // onSubmitが正しいデータで呼ばれることを確認
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(1, {
          title: "ログイン機能の実装",
          description: "詳細な説明",
          priority: "high",
          estimated_effort: 8,
          assignee: "developer_001",
          deadline: "2027-12-31T00:00:00.000Z",
        });
      });
    });

    test("送信成功後にフォームがリセットされてモーダルが閉じること", async () => {
      mockOnSubmit.mockResolvedValue(undefined);
      const mockOnClose = jest.fn();

      render(
        <StoryForm
          {...defaultProps}
          isOpen={true}
          onSubmit={mockOnSubmit}
          onClose={mockOnClose}
        />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // フォームに入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      const descriptionTextarea = screen.getByLabelText(/説明/i);

      await user.type(titleInput, "テストストーリー");
      await user.type(descriptionTextarea, "テストの説明");

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // onCloseが呼ばれることを確認
      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });
  });

  describe("エラーハンドリング", () => {
    test("サーバーエラー時にエラーバナーが表示されること", async () => {
      const serverError: ErrorResponse = {
        errors: [
          {
            code: "GS-201",
            message: "タイトルは500文字以内で入力してください",
          },
        ],
        timestamp: new Date().toISOString(),
      };
      mockOnSubmit.mockRejectedValue(serverError);

      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // フォームに入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      const descriptionTextarea = screen.getByLabelText(/説明/i);

      await user.type(titleInput, "テストストーリー");
      await user.type(descriptionTextarea, "テストの説明");

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // エラーメッセージが表示されることを確認
      await waitFor(() => {
        expect(
          screen.getByText(/タイトルは500文字以内で入力してください/i),
        ).toBeInTheDocument();
      });
    });

    test("ネットワークエラー時にエラーバナーが表示されること", async () => {
      mockOnSubmit.mockRejectedValue(new Error("Network error"));

      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // フォームに入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      const descriptionTextarea = screen.getByLabelText(/説明/i);

      await user.type(titleInput, "テストストーリー");
      await user.type(descriptionTextarea, "テストの説明");

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // エラーメッセージが表示されることを確認
      await waitFor(() => {
        expect(
          screen.getByText(/エラーが発生しました。もう一度お試しください。/i),
        ).toBeInTheDocument();
      });
    });
  });

  describe("ローディング状態", () => {
    test("送信中はボタンが無効化され、ローディング状態が表示されること", async () => {
      let resolveSubmit: () => void = () => {};
      const submitPromise = new Promise<void>((resolve) => {
        resolveSubmit = resolve;
      });
      mockOnSubmit.mockReturnValue(submitPromise);

      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      // 問い合わせを選択
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      await user.selectOptions(inquirySelect, "1");

      // フォームに入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      const descriptionTextarea = screen.getByLabelText(/説明/i);

      await user.type(titleInput, "テストストーリー");
      await user.type(descriptionTextarea, "テストの説明");

      // 送信ボタンをクリック
      const submitButton = screen.getByRole("button", { name: /作成/i });
      await user.click(submitButton);

      // ボタンが無効化されることを確認
      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });

      // ローディングテキストが表示されることを確認
      expect(screen.getByText(/作成中/i)).toBeInTheDocument();

      // Promiseを解決してクリーンアップ
      resolveSubmit();
    });

    test("isLoadingプロパティがtrueの場合、ボタンが無効化されること", () => {
      render(<StoryForm {...defaultProps} isOpen={true} isLoading={true} />);

      const submitButton = screen.getByRole("button", { name: /作成中/i });
      expect(submitButton).toBeDisabled();
    });
  });

  describe("キャンセル機能", () => {
    test("キャンセルボタンクリックでonCancelが呼ばれること", async () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onCancel={mockOnCancel} />,
      );

      const cancelButton = screen.getByRole("button", { name: /キャンセル/i });
      await user.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    test("モーダル背景クリックでonCancelが呼ばれること", async () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onCancel={mockOnCancel} />,
      );

      // 背景オーバーレイをクリック
      const overlay = screen.getByTestId("modal-overlay");
      await user.click(overlay);

      expect(mockOnCancel).toHaveBeenCalled();
    });
  });

  describe("優先度選択", () => {
    test("すべての優先度オプションが選択可能であること", async () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      const prioritySelect = screen.getByLabelText(/優先度/i);
      await user.click(prioritySelect);

      // すべての優先度オプションが表示されること
      expect(screen.getByRole("option", { name: /低/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /中/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /高/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /緊急/i })).toBeInTheDocument();
    });

    test("デフォルトの優先度が中であること", () => {
      render(
        <StoryForm {...defaultProps} isOpen={true} onSubmit={mockOnSubmit} />,
      );

      const prioritySelect = screen.getByLabelText(
        /優先度/i,
      ) as HTMLSelectElement;
      expect(prioritySelect.value).toBe("medium");
    });
  });

  describe("初期データ", () => {
    test("initialInquiryIdが提供されている場合、その問い合わせが選択されていること", () => {
      render(
        <StoryForm
          {...defaultProps}
          isOpen={true}
          initialInquiryId={1}
          onSubmit={mockOnSubmit}
        />,
      );

      // 問い合わせプレビューが表示されていること
      expect(screen.getByText(/タスク作業中/i)).toBeInTheDocument();
    });

    test("モーダルが閉じられた時にフォームがリセットされること", async () => {
      const { rerender } = render(
        <StoryForm
          {...defaultProps}
          isOpen={true}
          onSubmit={mockOnSubmit}
        />,
      );

      // フォームにデータを入力
      const inquirySelect = screen.getByLabelText(/問い合わせ/i);
      const titleInput = screen.getByLabelText(/タイトル/i);
      const descriptionTextarea = screen.getByLabelText(/説明/i);

      await user.selectOptions(inquirySelect, "1");
      await user.type(titleInput, "テストタイトル");
      await user.type(descriptionTextarea, "テスト説明");

      // データが入力されていることを確認
      expect((inquirySelect as HTMLSelectElement).value).toBe("1");
      expect((titleInput as HTMLInputElement).value).toBe("テストタイトル");
      expect((descriptionTextarea as HTMLTextAreaElement).value).toBe(
        "テスト説明",
      );

      // モーダルを閉じる
      rerender(
        <StoryForm
          {...defaultProps}
          isOpen={false}
          onSubmit={mockOnSubmit}
        />,
      );

      // モーダルを再度開く
      rerender(
        <StoryForm
          {...defaultProps}
          isOpen={true}
          onSubmit={mockOnSubmit}
        />,
      );

      // フォームがリセットされていることを確認
      const newInquirySelect = screen.getByLabelText(/問い合わせ/i);
      const newTitleInput = screen.getByLabelText(/タイトル/i);
      const newDescriptionTextarea = screen.getByLabelText(/説明/i);

      expect((newInquirySelect as HTMLSelectElement).value).toBe("");
      expect((newTitleInput as HTMLInputElement).value).toBe("");
      expect((newDescriptionTextarea as HTMLTextAreaElement).value).toBe("");
    });
  });
});

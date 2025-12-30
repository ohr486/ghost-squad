/**
 * InquiryFormコンポーネント テスト
 *
 * 要件: 4.2, 4.3 - フォームバリデーション、エラー表示
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InquiryForm } from "./InquiryForm";
import type { CreateInquiryRequest, ErrorResponse } from "../types";

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

describe("InquiryForm", () => {
  // テストユーティリティ
  const user = userEvent.setup();

  // モック関数
  let mockOnSubmit: jest.Mock<Promise<void>, [CreateInquiryRequest]>;
  let mockOnCancel: jest.Mock;

  beforeEach(() => {
    mockOnSubmit = jest.fn();
    mockOnCancel = jest.fn();
    jest.clearAllMocks();
  });

  describe("バリデーション", () => {
    test("空のcontentでバリデーションエラーが表示されること", async () => {
      render(<InquiryForm onSubmit={mockOnSubmit} />);

      // フォームフィールドを取得
      const userIdInput = screen.getByLabelText(/ユーザーID/i);
      const submitButton = screen.getByRole("button", { name: /送信/i });

      // ユーザーIDのみ入力し、contentは空のまま
      await user.type(userIdInput, "test_user");

      // 送信ボタンをクリック
      await user.click(submitButton);

      // バリデーションエラーメッセージが表示されることを確認
      await waitFor(() => {
        expect(
          screen.getByText(/問い合わせ内容は必須です/i),
        ).toBeInTheDocument();
      });

      // onSubmitが呼ばれていないことを確認
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    test("contentが10,000文字を超える場合のバリデーションエラーが表示されること", async () => {
      render(<InquiryForm onSubmit={mockOnSubmit} />);

      const userIdInput = screen.getByLabelText(/ユーザーID/i);
      const contentTextarea = screen.getByLabelText(/問い合わせ内容/i);
      const submitButton = screen.getByRole("button", { name: /送信/i });

      // 10,001文字の文字列を生成
      const longContent = "あ".repeat(10001);

      // フォームに入力（pasteを使用して高速化）
      await user.type(userIdInput, "test_user");
      await user.click(contentTextarea);
      await user.paste(longContent);

      // 送信ボタンをクリック
      await user.click(submitButton);

      // バリデーションエラーメッセージが表示されることを確認
      await waitFor(() => {
        expect(
          screen.getByText(/問い合わせ内容は10,000文字以内で入力してください/i),
        ).toBeInTheDocument();
      });

      // onSubmitが呼ばれていないことを確認
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    test("user_idが空の場合のバリデーションエラーが表示されること", async () => {
      render(<InquiryForm onSubmit={mockOnSubmit} />);

      const userIdInput = screen.getByLabelText(/ユーザーID/i);
      const contentTextarea = screen.getByLabelText(/問い合わせ内容/i);
      const submitButton = screen.getByRole("button", { name: /送信/i });

      // contentのみ入力し、user_idは空のまま（フォーカスして抜けることでバリデーション発火）
      await user.click(userIdInput);
      await user.tab(); // user_idフィールドから抜ける
      await user.type(contentTextarea, "テストの問い合わせ内容");

      // 送信ボタンをクリック
      await user.click(submitButton);

      // バリデーションエラーメッセージが表示されることを確認
      await waitFor(
        () => {
          expect(screen.getByText(/ユーザーIDは必須です/i)).toBeInTheDocument();
        },
        { timeout: 2000 },
      );

      // onSubmitが呼ばれていないことを確認
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    test("user_idが不正な形式の場合のバリデーションエラーが表示されること", async () => {
      render(<InquiryForm onSubmit={mockOnSubmit} />);

      const userIdInput = screen.getByLabelText(/ユーザーID/i);
      const contentTextarea = screen.getByLabelText(/問い合わせ内容/i);
      const submitButton = screen.getByRole("button", { name: /送信/i });

      // 不正な文字を含むuser_idを入力（記号を含む）
      await user.type(userIdInput, "test-user@123");
      await user.type(contentTextarea, "テストの問い合わせ内容");

      // 送信ボタンをクリック
      await user.click(submitButton);

      // バリデーションエラーメッセージが表示されることを確認
      await waitFor(() => {
        expect(
          screen.getByText(
            /ユーザーIDは英数字とアンダースコアのみ使用できます/i,
          ),
        ).toBeInTheDocument();
      });

      // onSubmitが呼ばれていないことを確認
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe("フォーム送信", () => {
    test("正常なフォーム送信が成功すること", async () => {
      // onSubmitを成功する関数としてモック
      mockOnSubmit.mockResolvedValue(undefined);

      render(<InquiryForm onSubmit={mockOnSubmit} />);

      const userIdInput = screen.getByLabelText(/ユーザーID/i);
      const contentTextarea = screen.getByLabelText(/問い合わせ内容/i);
      const submitButton = screen.getByRole("button", { name: /送信/i });

      // フォームに入力
      await user.type(userIdInput, "test_user");
      await user.type(contentTextarea, "ログイン機能が欲しい");

      // 送信ボタンをクリック
      await user.click(submitButton);

      // onSubmitが正しいデータで呼ばれることを確認
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          user_id: "test_user",
          content: "ログイン機能が欲しい",
          source_system: "manual",
        });
      });
    });

    test("送信成功後にフォームがリセットされること", async () => {
      mockOnSubmit.mockResolvedValue(undefined);

      render(<InquiryForm onSubmit={mockOnSubmit} />);

      const userIdInput = screen.getByLabelText(
        /ユーザーID/i,
      ) as HTMLInputElement;
      const contentTextarea = screen.getByLabelText(
        /問い合わせ内容/i,
      ) as HTMLTextAreaElement;
      const submitButton = screen.getByRole("button", { name: /送信/i });

      // フォームに入力
      await user.type(userIdInput, "test_user");
      await user.type(contentTextarea, "テスト問い合わせ");

      // 送信ボタンをクリック
      await user.click(submitButton);

      // 送信後、フォームがリセットされることを確認
      await waitFor(() => {
        expect(userIdInput.value).toBe("");
      });
      expect(contentTextarea.value).toBe("");
    });
  });

  describe("エラーハンドリング", () => {
    test("サーバーエラー時にエラーバナーが表示されること", async () => {
      // onSubmitがErrorResponseを拒否するようにモック
      const serverError: ErrorResponse = {
        errors: [
          {
            code: "GS-010",
            message: "データベース操作に失敗しました",
          },
        ],
        timestamp: new Date().toISOString(),
      };
      mockOnSubmit.mockRejectedValue(serverError);

      render(<InquiryForm onSubmit={mockOnSubmit} />);

      const userIdInput = screen.getByLabelText(/ユーザーID/i);
      const contentTextarea = screen.getByLabelText(/問い合わせ内容/i);
      const submitButton = screen.getByRole("button", { name: /送信/i });

      // フォームに入力
      await user.type(userIdInput, "test_user");
      await user.type(contentTextarea, "テスト問い合わせ");

      // 送信ボタンをクリック
      await user.click(submitButton);

      // エラーメッセージがフォーム上部に表示されることを確認
      await waitFor(() => {
        expect(
          screen.getByText(/データベース操作に失敗しました/i),
        ).toBeInTheDocument();
      });
    });

    test("ネットワークエラー時にエラーバナーが表示されること", async () => {
      // onSubmitが一般的なエラーを拒否するようにモック
      mockOnSubmit.mockRejectedValue(new Error("Network error"));

      render(<InquiryForm onSubmit={mockOnSubmit} />);

      const userIdInput = screen.getByLabelText(/ユーザーID/i);
      const contentTextarea = screen.getByLabelText(/問い合わせ内容/i);
      const submitButton = screen.getByRole("button", { name: /送信/i });

      // フォームに入力
      await user.type(userIdInput, "test_user");
      await user.type(contentTextarea, "テスト問い合わせ");

      // 送信ボタンをクリック
      await user.click(submitButton);

      // エラーメッセージがフォーム上部に表示されることを確認（より具体的なテキストで確認）
      await waitFor(() => {
        expect(
          screen.getByText(/エラーが発生しました。もう一度お試しください。/i),
        ).toBeInTheDocument();
      });
    });
  });

  describe("ローディング状態", () => {
    test("送信中はボタンが無効化され、ローディング状態が表示されること", async () => {
      // onSubmitが完了しないPromiseを返すようにモック（ローディング状態を保持）
      let resolveSubmit: () => void;
      const submitPromise = new Promise<void>((resolve) => {
        resolveSubmit = resolve;
      });
      mockOnSubmit.mockReturnValue(submitPromise);

      render(<InquiryForm onSubmit={mockOnSubmit} />);

      const userIdInput = screen.getByLabelText(/ユーザーID/i);
      const contentTextarea = screen.getByLabelText(/問い合わせ内容/i);
      const submitButton = screen.getByRole("button", { name: /送信/i });

      // フォームに入力
      await user.type(userIdInput, "test_user");
      await user.type(contentTextarea, "テスト問い合わせ");

      // 送信ボタンをクリック
      await user.click(submitButton);

      // ボタンが無効化されることを確認
      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });

      // ローディングテキストが表示されることを確認
      expect(screen.getByText(/送信中/i)).toBeInTheDocument();

      // Promiseを解決してクリーンアップ
      resolveSubmit!();
    });

    test("isLoadingプロパティがtrueの場合、ボタンが無効化されること", () => {
      render(<InquiryForm onSubmit={mockOnSubmit} isLoading={true} />);

      const submitButton = screen.getByRole("button", { name: /送信中/i });

      // ボタンが無効化されることを確認
      expect(submitButton).toBeDisabled();
    });
  });

  describe("キャンセル機能", () => {
    test("onCancelが提供されている場合、キャンセルボタンが表示されクリックできること", async () => {
      render(<InquiryForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const cancelButton = screen.getByRole("button", { name: /キャンセル/i });

      // キャンセルボタンをクリック
      await user.click(cancelButton);

      // onCancelが呼ばれることを確認
      expect(mockOnCancel).toHaveBeenCalled();
    });

    test("onCancelが提供されていない場合、キャンセルボタンが表示されないこと", () => {
      render(<InquiryForm onSubmit={mockOnSubmit} />);

      // キャンセルボタンが存在しないことを確認
      const cancelButton = screen.queryByRole("button", {
        name: /キャンセル/i,
      });
      expect(cancelButton).not.toBeInTheDocument();
    });
  });

  describe("初期データ", () => {
    test("initialDataが提供されている場合、フォームが初期値で表示されること", () => {
      const initialData = {
        user_id: "initial_user",
        content: "初期問い合わせ内容",
        source_system: "email",
      };

      render(<InquiryForm onSubmit={mockOnSubmit} initialData={initialData} />);

      const userIdInput = screen.getByLabelText(
        /ユーザーID/i,
      ) as HTMLInputElement;
      const contentTextarea = screen.getByLabelText(
        /問い合わせ内容/i,
      ) as HTMLTextAreaElement;

      // 初期値が設定されていることを確認
      expect(userIdInput.value).toBe("initial_user");
      expect(contentTextarea.value).toBe("初期問い合わせ内容");
    });
  });
});

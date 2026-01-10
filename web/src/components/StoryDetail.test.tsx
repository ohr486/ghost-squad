/**
 * StoryDetail コンポーネントテスト
 *
 * TDD: RED phase - 先にテストを書く
 *
 * 要件: 2.5, 2.6, 3.1, 3.4, 5.2, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12
 */

import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import toast from "react-hot-toast";
import StoryDetail from "./StoryDetail";
import * as storyApi from "../services/storyApi";
import type { StoryResponse, StoryStatus, Priority } from "../types";

// APIモック
jest.mock("../services/storyApi");
jest.mock("react-hot-toast");

const mockStoryApi = storyApi as jest.Mocked<typeof storyApi>;

describe("StoryDetail", () => {
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

  const mockStory: StoryResponse = {
    id: 1,
    inquiry_id: 10,
    title: "テストストーリータイトル",
    description: "テストストーリー説明文",
    priority: "medium" as Priority,
    status: "waiting_review" as StoryStatus,
    estimated_effort: 8,
    deadline: "2025-02-01T00:00:00Z",
    assignee: "developer_001",
    story_metadata: {},
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  };

  const renderComponent = (storyId: number, onBack?: () => void) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <StoryDetail storyId={storyId} onBack={onBack} />
      </QueryClientProvider>,
    );
  };

  // ストーリー詳細表示テスト
  describe("Display story details", () => {
    test("displays story details when loaded", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      expect(screen.getByText("テストストーリー説明文")).toBeInTheDocument();
      expect(screen.getByText(/優先度:/)).toBeInTheDocument();
      expect(screen.getByText(/ステータス:/)).toBeInTheDocument();
    });

    test("displays loading state while fetching", () => {
      mockStoryApi.getStory.mockImplementationOnce(
        () => new Promise(() => {}), // Never resolves
      );

      renderComponent(1);

      expect(screen.getByText(/読み込み中/)).toBeInTheDocument();
    });

    test("displays error message when fetch fails", async () => {
      mockStoryApi.getStory.mockRejectedValueOnce(new Error("Network error"));

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText(/ストーリーの取得に失敗しました/),
        ).toBeInTheDocument();
      });
    });
  });

  // 編集モード切り替えテスト
  describe("Edit mode toggle", () => {
    test("switches to edit mode when edit button is clicked", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      const editButton = screen.getByRole("button", { name: /編集/ });
      fireEvent.click(editButton);

      // 編集フォームが表示されることを確認
      expect(screen.getByLabelText(/タイトル/)).toBeInTheDocument();
      expect(screen.getByLabelText(/説明/)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /保存/ })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /キャンセル/ }),
      ).toBeInTheDocument();
    });

    test("cancels edit mode when cancel button is clicked", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 編集モードに切り替え
      fireEvent.click(screen.getByRole("button", { name: /編集/ }));
      expect(screen.getByLabelText(/タイトル/)).toBeInTheDocument();

      // キャンセル
      fireEvent.click(screen.getByRole("button", { name: /キャンセル/ }));

      // 読み取りモードに戻ることを確認
      expect(screen.queryByLabelText(/タイトル/)).not.toBeInTheDocument();
      expect(screen.getByRole("button", { name: /編集/ })).toBeInTheDocument();
    });
  });

  // インライン編集と保存テスト
  describe("Inline edit and save", () => {
    test("updates story when saved", async () => {
      const updatedStory = {
        ...mockStory,
        title: "更新されたタイトル",
        description: "更新された説明文",
        updated_at: "2025-01-02T00:00:00Z",
      };

      mockStoryApi.getStory
        .mockResolvedValueOnce(mockStory)
        .mockResolvedValueOnce(updatedStory);
      mockStoryApi.updateStory.mockResolvedValueOnce(updatedStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 編集モードに切り替え
      fireEvent.click(screen.getByRole("button", { name: /編集/ }));

      // タイトルを変更
      const titleInput = screen.getByLabelText(/タイトル/);
      fireEvent.change(titleInput, { target: { value: "更新されたタイトル" } });

      // 説明を変更
      const descInput = screen.getByLabelText(/説明/);
      fireEvent.change(descInput, { target: { value: "更新された説明文" } });

      // 保存
      fireEvent.click(screen.getByRole("button", { name: /保存/ }));

      await waitFor(() => {
        expect(mockStoryApi.updateStory).toHaveBeenCalledWith(
          1,
          expect.objectContaining({
            title: "更新されたタイトル",
            description: "更新された説明文",
          }),
        );
      });

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("ストーリーを更新しました");
      });
    });

    test("displays error when save fails", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);
      mockStoryApi.updateStory.mockRejectedValueOnce(
        new Error("Update failed"),
      );

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 編集モードに切り替え
      fireEvent.click(screen.getByRole("button", { name: /編集/ }));

      // タイトルを変更
      const titleInput = screen.getByLabelText(/タイトル/);
      fireEvent.change(titleInput, { target: { value: "更新されたタイトル" } });

      // 保存
      fireEvent.click(screen.getByRole("button", { name: /保存/ }));

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "ストーリーの更新に失敗しました",
        );
      });
    });
  });

  // 承認操作テスト
  describe("Approve operation", () => {
    test("approves story when approve button is clicked and confirmed", async () => {
      const approvedStory = {
        ...mockStory,
        status: "approved" as StoryStatus,
        story_metadata: {
          approval: {
            approved_at: "2025-01-02T00:00:00Z",
            approver: "admin",
          },
        },
        updated_at: "2025-01-02T00:00:00Z",
      };

      mockStoryApi.getStory
        .mockResolvedValueOnce(mockStory)
        .mockResolvedValueOnce(approvedStory);
      mockStoryApi.approveStory.mockResolvedValueOnce(approvedStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 承認ボタンをクリック
      const approveButton = screen.getByRole("button", { name: /承認/ });
      fireEvent.click(approveButton);

      // 確認ダイアログが表示されることを確認
      expect(screen.getByText(/ストーリーの承認/)).toBeInTheDocument();

      // 確認ボタンをクリック
      const confirmButton = screen.getByRole("button", { name: /確認/ });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockStoryApi.approveStory).toHaveBeenCalledWith(1, {
          approver: expect.any(String),
        });
      });

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("ストーリーを承認しました");
      });
    });

    test("displays error when approve fails", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);
      mockStoryApi.approveStory.mockRejectedValueOnce(
        new Error("Approve failed"),
      );

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 承認ボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /承認/ }));

      // 確認ボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /確認/ }));

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "ストーリーの承認に失敗しました",
        );
      });
    });
  });

  // 却下操作テスト
  describe("Reject operation", () => {
    test("rejects story with reason", async () => {
      const rejectedStory = {
        ...mockStory,
        status: "rejected" as StoryStatus,
        story_metadata: {
          rejection: {
            rejected_at: "2025-01-02T00:00:00Z",
            rejector: "admin",
            reason: "要件が不明確です",
          },
        },
        updated_at: "2025-01-02T00:00:00Z",
      };

      mockStoryApi.getStory
        .mockResolvedValueOnce(mockStory)
        .mockResolvedValueOnce(rejectedStory);
      mockStoryApi.rejectStory.mockResolvedValueOnce(rejectedStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 却下ボタンをクリック
      const rejectButton = screen.getByRole("button", { name: /却下/ });
      fireEvent.click(rejectButton);

      // 却下ダイアログが表示されることを確認
      expect(screen.getByText(/ストーリーの却下/)).toBeInTheDocument();

      // 却下理由を入力
      const reasonInput = screen.getByLabelText(/却下理由/);
      fireEvent.change(reasonInput, { target: { value: "要件が不明確です" } });

      // 確認ボタンをクリック
      const confirmButton = screen.getByRole("button", { name: /確認/ });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockStoryApi.rejectStory).toHaveBeenCalledWith(1, {
          rejector: expect.any(String),
          reason: "要件が不明確です",
        });
      });

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("ストーリーを却下しました");
      });
    });

    test("shows validation error when reject reason is empty", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 却下ボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /却下/ }));

      // 理由を入力せずに確認ボタンをクリック
      const confirmButton = screen.getByRole("button", { name: /確認/ });
      fireEvent.click(confirmButton);

      // バリデーションエラーメッセージが表示されることを確認
      await waitFor(() => {
        expect(screen.getByText(/却下理由は必須です/)).toBeInTheDocument();
      });

      // APIが呼び出されていないことを確認
      expect(mockStoryApi.rejectStory).not.toHaveBeenCalled();
    });

    test("displays error when reject fails", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);
      mockStoryApi.rejectStory.mockRejectedValueOnce(
        new Error("Reject failed"),
      );

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 却下ボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /却下/ }));

      // 却下理由を入力
      const reasonInput = screen.getByLabelText(/却下理由/);
      fireEvent.change(reasonInput, { target: { value: "却下理由" } });

      // 確認ボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /確認/ }));

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "ストーリーの却下に失敗しました",
        );
      });
    });
  });

  // ステータスに基づくボタン表示テスト
  describe("Button visibility based on status", () => {
    test("shows approve/reject buttons when status is waiting_review", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      expect(screen.getByRole("button", { name: /承認/ })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /却下/ })).toBeInTheDocument();
    });

    test("hides approve/reject buttons when status is approved", async () => {
      const approvedStory = {
        ...mockStory,
        status: "approved" as StoryStatus,
      };

      mockStoryApi.getStory.mockResolvedValueOnce(approvedStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      expect(
        screen.queryByRole("button", { name: /承認/ }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /却下/ }),
      ).not.toBeInTheDocument();
    });

    test("hides approve/reject buttons when status is rejected", async () => {
      const rejectedStory = {
        ...mockStory,
        status: "rejected" as StoryStatus,
      };

      mockStoryApi.getStory.mockResolvedValueOnce(rejectedStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      expect(
        screen.queryByRole("button", { name: /承認/ }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /却下/ }),
      ).not.toBeInTheDocument();
    });
  });

  // 承認・却下情報の表示テスト
  describe("Approval/Rejection information display", () => {
    test("displays approval information when story is approved", async () => {
      const approvedStory: StoryResponse = {
        ...mockStory,
        status: "approved" as StoryStatus,
        story_metadata: {
          approval: {
            approved_at: "2025-01-02T10:30:00Z",
            approver: "admin_user",
          },
        },
      };

      mockStoryApi.getStory.mockResolvedValueOnce(approvedStory);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("承認情報")).toBeInTheDocument();
      });

      expect(screen.getByText(/承認日時:/)).toBeInTheDocument();
      expect(screen.getByText(/承認者:/)).toBeInTheDocument();
      expect(screen.getByText("admin_user")).toBeInTheDocument();
    });

    test("displays rejection information when story is rejected", async () => {
      const rejectedStory: StoryResponse = {
        ...mockStory,
        status: "rejected" as StoryStatus,
        story_metadata: {
          rejection: {
            rejected_at: "2025-01-02T10:30:00Z",
            rejector: "admin_user",
            reason: "要件が不明確です",
          },
        },
      };

      mockStoryApi.getStory.mockResolvedValueOnce(rejectedStory);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("却下情報")).toBeInTheDocument();
      });

      expect(screen.getByText(/却下日時:/)).toBeInTheDocument();
      expect(screen.getByText(/却下者:/)).toBeInTheDocument();
      expect(screen.getByText("admin_user")).toBeInTheDocument();
      expect(screen.getByText(/却下理由:/)).toBeInTheDocument();
      expect(screen.getByText("要件が不明確です")).toBeInTheDocument();
    });

    test("does not display approval/rejection info when status is waiting_review", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      expect(screen.queryByText("承認情報")).not.toBeInTheDocument();
      expect(screen.queryByText("却下情報")).not.toBeInTheDocument();
    });
  });

  // 削除操作テスト
  describe("Delete operation", () => {
    test("deletes story when delete button is clicked and confirmed", async () => {
      const mockOnBack = jest.fn();
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);
      mockStoryApi.deleteStory.mockResolvedValueOnce({ success: true });

      renderComponent(1, mockOnBack);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 削除ボタンをクリック
      const deleteButton = screen.getByRole("button", { name: /削除/ });
      fireEvent.click(deleteButton);

      // 確認ダイアログが表示されることを確認
      expect(screen.getByText(/ストーリーの削除/)).toBeInTheDocument();

      // 確認ボタンをクリック
      const confirmButton = screen.getByRole("button", { name: /確認/ });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockStoryApi.deleteStory).toHaveBeenCalledWith(1);
      });

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("ストーリーを削除しました");
      });

      // onBackが呼ばれることを確認
      await waitFor(() => {
        expect(mockOnBack).toHaveBeenCalled();
      });
    });

    test("displays error when delete fails", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);
      mockStoryApi.deleteStory.mockRejectedValueOnce(
        new Error("Delete failed"),
      );

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 削除ボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /削除/ }));

      // 確認ボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /確認/ }));

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "ストーリーの削除に失敗しました",
        );
      });
    });
  });

  // ダイアログキャンセルテスト
  describe("Dialog cancel", () => {
    test("closes approve dialog when cancel is clicked", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 承認ボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /承認/ }));
      expect(screen.getByText(/ストーリーの承認/)).toBeInTheDocument();

      // キャンセルボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /キャンセル/ }));

      // ダイアログが閉じることを確認
      await waitFor(() => {
        expect(screen.queryByText(/ストーリーの承認/)).not.toBeInTheDocument();
      });
    });

    test("closes reject dialog when cancel is clicked", async () => {
      mockStoryApi.getStory.mockResolvedValueOnce(mockStory);

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText("テストストーリータイトル"),
        ).toBeInTheDocument();
      });

      // 却下ボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /却下/ }));
      expect(screen.getByText(/ストーリーの却下/)).toBeInTheDocument();

      // キャンセルボタンをクリック
      fireEvent.click(screen.getByRole("button", { name: /キャンセル/ }));

      // ダイアログが閉じることを確認
      await waitFor(() => {
        expect(screen.queryByText(/ストーリーの却下/)).not.toBeInTheDocument();
      });
    });
  });
});

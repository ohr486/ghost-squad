import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import toast from "react-hot-toast";
import InquiryDetail from "./InquiryDetail";
import * as inquiryApi from "../services/inquiryApi";
import { InquiryResponse } from "../types/inquiry";

// AxiosモックはsetupTests.tsで設定済み
jest.mock("../services/inquiryApi");
jest.mock("react-hot-toast");

const mockInquiryApi = inquiryApi as jest.Mocked<typeof inquiryApi>;

describe("InquiryDetail", () => {
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

  const mockInquiry: InquiryResponse = {
    id: 1,
    user_id: "test_user",
    content: "テスト問い合わせ内容",
    source_system: "manual",
    timestamp: "2025-01-01T00:00:00Z",
    status: "received",
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  };

  const renderComponent = (inquiryId: number) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <InquiryDetail inquiryId={inquiryId} />
      </QueryClientProvider>,
    );
  };

  // 問い合わせ詳細の表示テスト
  describe("Display inquiry details", () => {
    test("displays inquiry details when loaded", async () => {
      mockInquiryApi.getInquiry.mockResolvedValueOnce(mockInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      expect(screen.getByText(/ユーザーID:/)).toBeInTheDocument();
      expect(screen.getByText("test_user")).toBeInTheDocument();
      expect(screen.getByText(/ステータス:/)).toBeInTheDocument();
      expect(screen.getByText("received")).toBeInTheDocument();
    });

    test("displays loading state while fetching", () => {
      mockInquiryApi.getInquiry.mockImplementationOnce(
        () => new Promise(() => {}), // Never resolves
      );

      renderComponent(1);

      expect(screen.getByText(/読み込み中/)).toBeInTheDocument();
    });

    test("displays error message when fetch fails", async () => {
      mockInquiryApi.getInquiry.mockRejectedValueOnce(
        new Error("Network error"),
      );

      renderComponent(1);

      await waitFor(() => {
        expect(
          screen.getByText(/問い合わせの取得に失敗しました/),
        ).toBeInTheDocument();
      });
    });
  });

  // 編集モードの切り替えテスト
  describe("Edit mode toggle", () => {
    test("switches to edit mode when edit button is clicked", async () => {
      mockInquiryApi.getInquiry.mockResolvedValueOnce(mockInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      const editButton = screen.getByRole("button", { name: /編集/ });
      fireEvent.click(editButton);

      expect(screen.getByRole("textbox")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /保存/ })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /キャンセル/ }),
      ).toBeInTheDocument();
    });

    test("cancels edit mode when cancel button is clicked", async () => {
      mockInquiryApi.getInquiry.mockResolvedValueOnce(mockInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      // Enter edit mode
      fireEvent.click(screen.getByRole("button", { name: /編集/ }));

      expect(screen.getByRole("textbox")).toBeInTheDocument();

      // Cancel edit
      fireEvent.click(screen.getByRole("button", { name: /キャンセル/ }));

      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      expect(screen.getByRole("button", { name: /編集/ })).toBeInTheDocument();
    });
  });

  // インライン編集と保存テスト
  describe("Inline edit and save", () => {
    test("updates inquiry content when saved", async () => {
      const updatedInquiry = {
        ...mockInquiry,
        content: "更新された内容",
        updated_at: "2025-01-02T00:00:00Z",
      };

      mockInquiryApi.getInquiry
        .mockResolvedValueOnce(mockInquiry)
        .mockResolvedValueOnce(updatedInquiry);
      mockInquiryApi.updateInquiry.mockResolvedValueOnce(updatedInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      // Enter edit mode
      fireEvent.click(screen.getByRole("button", { name: /編集/ }));

      const textarea = screen.getByRole("textbox");
      fireEvent.change(textarea, { target: { value: "更新された内容" } });

      // Save
      fireEvent.click(screen.getByRole("button", { name: /保存/ }));

      await waitFor(() => {
        expect(mockInquiryApi.updateInquiry).toHaveBeenCalledWith(1, {
          content: "更新された内容",
        });
      });

      await waitFor(() => {
        expect(screen.getByText("更新された内容")).toBeInTheDocument();
      });
    });

    test("displays error when save fails", async () => {
      mockInquiryApi.getInquiry.mockResolvedValueOnce(mockInquiry);
      mockInquiryApi.updateInquiry.mockRejectedValueOnce(
        new Error("Update failed"),
      );

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      // Enter edit mode
      fireEvent.click(screen.getByRole("button", { name: /編集/ }));

      const textarea = screen.getByRole("textbox");
      fireEvent.change(textarea, { target: { value: "更新された内容" } });

      // Save
      fireEvent.click(screen.getByRole("button", { name: /保存/ }));

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "問い合わせの更新に失敗しました",
        );
      });
    });
  });

  // 承認操作テスト
  describe("Approve operation", () => {
    test("approves inquiry when approve button is clicked", async () => {
      const approvedInquiry = {
        ...mockInquiry,
        status: "task_working" as const,
        updated_at: "2025-01-02T00:00:00Z",
      };

      mockInquiryApi.getInquiry
        .mockResolvedValueOnce(mockInquiry)
        .mockResolvedValueOnce(approvedInquiry);
      mockInquiryApi.approveInquiry.mockResolvedValueOnce(approvedInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      const approveButton = screen.getByRole("button", { name: /承認/ });
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(mockInquiryApi.approveInquiry).toHaveBeenCalledWith(1);
      });

      await waitFor(() => {
        expect(screen.getByText("task_working")).toBeInTheDocument();
      });
    });

    test("displays error when approve fails", async () => {
      mockInquiryApi.getInquiry.mockResolvedValueOnce(mockInquiry);
      mockInquiryApi.approveInquiry.mockRejectedValueOnce(
        new Error("Approve failed"),
      );

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole("button", { name: /承認/ }));

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "問い合わせの承認に失敗しました",
        );
      });
    });
  });

  // 却下操作テスト（却下理由あり/なし）
  describe("Reject operation", () => {
    test("rejects inquiry without reason", async () => {
      const rejectedInquiry = {
        ...mockInquiry,
        status: "rejected" as const,
        updated_at: "2025-01-02T00:00:00Z",
      };

      mockInquiryApi.getInquiry
        .mockResolvedValueOnce(mockInquiry)
        .mockResolvedValueOnce(rejectedInquiry);
      mockInquiryApi.rejectInquiry.mockResolvedValueOnce(rejectedInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      const rejectButton = screen.getByRole("button", { name: /却下/ });
      fireEvent.click(rejectButton);

      // Click confirm button in dialog
      const confirmButton = screen.getByRole("button", { name: /確認/ });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockInquiryApi.rejectInquiry).toHaveBeenCalledWith(1, undefined);
      });

      await waitFor(() => {
        expect(screen.getByText("rejected")).toBeInTheDocument();
      });
    });

    test("rejects inquiry with reason", async () => {
      const rejectedInquiry = {
        ...mockInquiry,
        status: "rejected" as const,
        updated_at: "2025-01-02T00:00:00Z",
      };

      mockInquiryApi.getInquiry
        .mockResolvedValueOnce(mockInquiry)
        .mockResolvedValueOnce(rejectedInquiry);
      mockInquiryApi.rejectInquiry.mockResolvedValueOnce(rejectedInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      // Open reject dialog
      const rejectButton = screen.getByRole("button", { name: /却下/ });
      fireEvent.click(rejectButton);

      // Enter reason
      const reasonInput = screen.getByLabelText(/却下理由/);
      fireEvent.change(reasonInput, {
        target: { value: "要件が不明確です" },
      });

      // Confirm reject
      const confirmButton = screen.getByRole("button", { name: /確認/ });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockInquiryApi.rejectInquiry).toHaveBeenCalledWith(
          1,
          { reason: "要件が不明確です" },
        );
      });

      await waitFor(() => {
        expect(screen.getByText("rejected")).toBeInTheDocument();
      });
    });

    test("displays error when reject fails", async () => {
      mockInquiryApi.getInquiry.mockResolvedValueOnce(mockInquiry);
      mockInquiryApi.rejectInquiry.mockRejectedValueOnce(
        new Error("Reject failed"),
      );

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      const rejectButton = screen.getByRole("button", { name: /却下/ });
      fireEvent.click(rejectButton);

      // Click confirm in reject dialog
      const confirmButton = screen.getByRole("button", { name: /確認/ });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "問い合わせの却下に失敗しました",
        );
      });
    });
  });

  // receivedステータス以外での承認・却下ボタン非表示テスト
  describe("Button visibility based on status", () => {
    test("hides approve/reject buttons when status is not RECEIVED", async () => {
      const taskWorkingInquiry = {
        ...mockInquiry,
        status: "task_working",
      };

      mockInquiryApi.getInquiry.mockResolvedValueOnce(taskWorkingInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      expect(
        screen.queryByRole("button", { name: /承認/ }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /却下/ }),
      ).not.toBeInTheDocument();
    });

    test("shows approve/reject buttons when status is RECEIVED", async () => {
      mockInquiryApi.getInquiry.mockResolvedValueOnce(mockInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      expect(screen.getByRole("button", { name: /承認/ })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /却下/ })).toBeInTheDocument();
    });

    test("hides approve/reject buttons when status is REJECTED", async () => {
      const rejectedInquiry = {
        ...mockInquiry,
        status: "rejected",
      };

      mockInquiryApi.getInquiry.mockResolvedValueOnce(rejectedInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      expect(
        screen.queryByRole("button", { name: /承認/ }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /却下/ }),
      ).not.toBeInTheDocument();
    });

    test("hides approve/reject buttons when status is COMPLETED", async () => {
      const completedInquiry = {
        ...mockInquiry,
        status: "completed",
      };

      mockInquiryApi.getInquiry.mockResolvedValueOnce(completedInquiry);

      renderComponent(1);

      await waitFor(() => {
        expect(screen.getByText("テスト問い合わせ内容")).toBeInTheDocument();
      });

      expect(
        screen.queryByRole("button", { name: /承認/ }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /却下/ }),
      ).not.toBeInTheDocument();
    });
  });
});

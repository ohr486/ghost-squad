import React from "react";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import InquiriesPage from "./InquiriesPage";

// Mock InquiryForm component
jest.mock("../components/forms", () => ({
  InquiryForm: ({
    onSuccess,
    onError,
  }: {
    onSuccess?: (inquiry: any) => void;
    onError?: (error: Error) => void;
  }) => (
    <div data-testid="inquiry-form">
      <h2>Inquiry Form</h2>
      <button
        onClick={() =>
          onSuccess?.({
            id: 1,
            user_id: "user-001",
            content: "Test inquiry",
            language: "ja",
            timestamp: new Date().toISOString(),
            status: "RECEIVED",
          })
        }
      >
        Submit Success
      </button>
      <button onClick={() => onError?.(new Error("Test error"))}>
        Submit Error
      </button>
    </div>
  ),
}));

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe("InquiriesPage", () => {
  it("renders the page title", () => {
    render(
      <TestWrapper>
        <InquiriesPage />
      </TestWrapper>,
    );
    expect(screen.getByText("問い合わせ管理")).toBeInTheDocument();
  });

  it("displays the page description", () => {
    render(
      <TestWrapper>
        <InquiriesPage />
      </TestWrapper>,
    );
    expect(
      screen.getByText(
        "自然言語での問い合わせを入力し、AIがストーリーに変換します",
      ),
    ).toBeInTheDocument();
  });

  it("shows the new inquiry button", () => {
    render(
      <TestWrapper>
        <InquiriesPage />
      </TestWrapper>,
    );
    expect(screen.getByText("新しい問い合わせ")).toBeInTheDocument();
  });

  it("displays implementation status", () => {
    render(
      <TestWrapper>
        <InquiriesPage />
      </TestWrapper>,
    );
    expect(screen.getByText("問い合わせ履歴")).toBeInTheDocument();
    expect(
      screen.getByText("問い合わせ履歴表示機能は次のタスクで実装予定です"),
    ).toBeInTheDocument();
    expect(screen.getByText("実装予定の機能:")).toBeInTheDocument();
    expect(screen.getByText(/問い合わせ履歴の一覧表示/)).toBeInTheDocument();
    expect(
      screen.getByText(/AIによるストーリー生成結果の確認/),
    ).toBeInTheDocument();
  });

  describe("Form toggle functionality", () => {
    it("does not show the inquiry form initially", () => {
      render(
        <TestWrapper>
          <InquiriesPage />
        </TestWrapper>,
      );
      expect(screen.queryByTestId("inquiry-form")).not.toBeInTheDocument();
    });

    it("shows the inquiry form when clicking the '新しい問い合わせ' button", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <InquiriesPage />
        </TestWrapper>,
      );

      const toggleButton = screen.getByRole("button", {
        name: /新しい問い合わせを作成/,
      });
      await user.click(toggleButton);

      expect(screen.getByTestId("inquiry-form")).toBeInTheDocument();
    });

    it("hides the inquiry form when clicking the '閉じる' button", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <InquiriesPage />
        </TestWrapper>,
      );

      // First, show the form
      const toggleButton = screen.getByRole("button", {
        name: /新しい問い合わせを作成/,
      });
      await user.click(toggleButton);
      expect(screen.getByTestId("inquiry-form")).toBeInTheDocument();

      // Then, hide the form
      const closeButton = screen.getByRole("button", {
        name: /フォームを閉じる/,
      });
      await user.click(closeButton);
      expect(screen.queryByTestId("inquiry-form")).not.toBeInTheDocument();
    });

    it("changes button text from '新しい問い合わせ' to '閉じる' when form is shown", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <InquiriesPage />
        </TestWrapper>,
      );

      expect(screen.getByText("新しい問い合わせ")).toBeInTheDocument();
      expect(screen.queryByText("閉じる")).not.toBeInTheDocument();

      const toggleButton = screen.getByRole("button", {
        name: /新しい問い合わせを作成/,
      });
      await user.click(toggleButton);

      expect(screen.queryByText("新しい問い合わせ")).not.toBeInTheDocument();
      expect(screen.getByText("閉じる")).toBeInTheDocument();
    });

    it("hides the form after successful inquiry submission", async () => {
      const user = userEvent.setup();
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      render(
        <TestWrapper>
          <InquiriesPage />
        </TestWrapper>,
      );

      // Show the form
      const toggleButton = screen.getByRole("button", {
        name: /新しい問い合わせを作成/,
      });
      await user.click(toggleButton);
      expect(screen.getByTestId("inquiry-form")).toBeInTheDocument();

      // Simulate successful submission
      const submitButton = screen.getByText("Submit Success");
      await user.click(submitButton);

      // Form should be hidden
      expect(screen.queryByTestId("inquiry-form")).not.toBeInTheDocument();
      expect(screen.getByText("新しい問い合わせ")).toBeInTheDocument();

      // Verify console.log was called with success message
      expect(consoleSpy).toHaveBeenCalledWith(
        "Inquiry created successfully:",
        expect.objectContaining({
          id: 1,
          content: "Test inquiry",
        }),
      );

      consoleSpy.mockRestore();
    });

    it("keeps the form visible after submission error", async () => {
      const user = userEvent.setup();
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

      render(
        <TestWrapper>
          <InquiriesPage />
        </TestWrapper>,
      );

      // Show the form
      const toggleButton = screen.getByRole("button", {
        name: /新しい問い合わせを作成/,
      });
      await user.click(toggleButton);
      expect(screen.getByTestId("inquiry-form")).toBeInTheDocument();

      // Simulate error submission
      const errorButton = screen.getByText("Submit Error");
      await user.click(errorButton);

      // Form should still be visible
      expect(screen.getByTestId("inquiry-form")).toBeInTheDocument();

      // Verify console.error was called
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Failed to create inquiry:",
        expect.any(Error),
      );

      consoleErrorSpy.mockRestore();
    });
  });
});

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import InquiryForm from "./InquiryForm";
import { InquiryService } from "../../services";
import type { InquiryResponse } from "../../types/api";

// Mock the InquiryService
jest.mock("../../services", () => ({
  InquiryService: {
    createInquiry: jest.fn(),
  },
}));

// Mock react-hot-toast
jest.mock("react-hot-toast", () => ({
  success: jest.fn(),
  error: jest.fn(),
}));

const mockInquiryService = InquiryService as jest.Mocked<typeof InquiryService>;

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe("InquiryForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders form elements correctly", () => {
    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    expect(screen.getByText("新しい問い合わせ")).toBeInTheDocument();
    expect(screen.getByLabelText("問い合わせの言語")).toBeInTheDocument();
    expect(screen.getByLabelText("問い合わせ内容")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /送信/ })).toBeInTheDocument();
  });

  it("shows validation error for empty content", async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");

    // Focus and blur the textarea to trigger validation
    await user.click(textarea);
    await user.tab();

    await waitFor(() => {
      expect(
        screen.getByText("問い合わせ内容は10文字以上で入力してください"),
      ).toBeInTheDocument();
    });
  });

  it("shows validation error for content too short", async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(textarea, "短い");

    const submitButton = screen.getByRole("button", { name: /送信/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("問い合わせ内容は10文字以上で入力してください"),
      ).toBeInTheDocument();
    });
  });

  it("shows character count", async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(textarea, "テストコンテンツです");

    expect(screen.getByText(/10 \/ 5000/)).toBeInTheDocument();
  });

  it("submits form successfully", async () => {
    const user = userEvent.setup();
    const mockResponse: InquiryResponse = {
      id: 1,
      user_id: "user-001",
      content:
        "ユーザー登録機能を追加したいです。メールアドレスとパスワードで登録できるようにして、確認メールも送信したいです。",
      language: "ja",
      timestamp: "2024-01-01T00:00:00Z",
      status: "received" as any,
      metadata: {
        source: "web",
      },
    };

    mockInquiryService.createInquiry.mockResolvedValue(mockResponse);

    const onSuccess = jest.fn();
    render(
      <TestWrapper>
        <InquiryForm onSuccess={onSuccess} />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(
      textarea,
      "ユーザー登録機能を追加したいです。メールアドレスとパスワードで登録できるようにして、確認メールも送信したいです。",
    );

    const submitButton = screen.getByRole("button", { name: /送信/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockInquiryService.createInquiry).toHaveBeenCalledWith({
        content:
          "ユーザー登録機能を追加したいです。メールアドレスとパスワードで登録できるようにして、確認メールも送信したいです。",
        language: "ja",
        user_id: "user-001",
      });
    });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(mockResponse);
    });
  });

  it("handles submission error", async () => {
    const user = userEvent.setup();
    const mockError = new Error("Network error");
    mockInquiryService.createInquiry.mockRejectedValue(mockError);

    const onError = jest.fn();
    render(
      <TestWrapper>
        <InquiryForm onError={onError} />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(
      textarea,
      "ユーザー登録機能を追加したいです。メールアドレスとパスワードで登録できるようにして、確認メールも送信したいです。",
    );

    const submitButton = screen.getByRole("button", { name: /送信/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(mockError);
    });
  });

  it("shows loading state during submission", async () => {
    const user = userEvent.setup();
    let resolvePromise: (value: InquiryResponse) => void = () => {};
    const promise = new Promise<InquiryResponse>((resolve) => {
      resolvePromise = resolve;
    });
    mockInquiryService.createInquiry.mockReturnValue(promise);

    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(
      textarea,
      "ユーザー登録機能を追加したいです。メールアドレスとパスワードで登録できるようにして、確認メールも送信したいです。",
    );

    const submitButton = screen.getByRole("button", { name: /送信/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/送信中/)).toBeInTheDocument();
    });
    expect(submitButton).toBeDisabled();

    // Resolve the promise to clean up
    resolvePromise({
      id: 1,
      user_id: "user-001",
      content:
        "ユーザー登録機能を追加したいです。メールアドレスとパスワードで登録できるようにして、確認メールも送信したいです。",
      language: "ja",
      timestamp: "2024-01-01T00:00:00Z",
      status: "received" as any,
      metadata: { source: "web" },
    });
  });

  it("supports language selection", async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const languageSelect = screen.getByLabelText("問い合わせの言語");
    await user.selectOptions(languageSelect, "en");

    expect(languageSelect).toHaveValue("en");
  });

  it("resets form after successful submission", async () => {
    const user = userEvent.setup();
    const mockResponse: InquiryResponse = {
      id: 1,
      user_id: "user-001",
      content:
        "ユーザー登録機能を追加したいです。メールアドレスとパスワードで登録できるようにして、確認メールも送信したいです。",
      language: "ja",
      timestamp: "2024-01-01T00:00:00Z",
      status: "received" as any,
      metadata: {
        source: "web",
      },
    };

    mockInquiryService.createInquiry.mockResolvedValue(mockResponse);

    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(
      textarea,
      "ユーザー登録機能を追加したいです。メールアドレスとパスワードで登録できるようにして、確認メールも送信したいです。",
    );

    const submitButton = screen.getByRole("button", { name: /送信/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(textarea).toHaveValue("");
    });
  });

  it("shows success state with appropriate button styling", async () => {
    const user = userEvent.setup();
    const mockResponse: InquiryResponse = {
      id: 1,
      user_id: "user-001",
      content: "テスト問い合わせです。",
      language: "ja",
      timestamp: "2024-01-01T00:00:00Z",
      status: "received" as any,
      metadata: { source: "web" },
    };

    mockInquiryService.createInquiry.mockResolvedValue(mockResponse);

    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(textarea, "テスト問い合わせです。");

    const submitButton = screen.getByRole("button");
    await user.click(submitButton);

    await waitFor(
      () => {
        const button = screen.getByRole("button");
        expect(button).toHaveClass("bg-green-600");
      },
      { timeout: 3000 },
    );
  });

  it("shows error state with appropriate button styling", async () => {
    const user = userEvent.setup();
    const mockError = new Error("Network error");
    mockInquiryService.createInquiry.mockRejectedValue(mockError);

    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(textarea, "テスト問い合わせです。");

    const submitButton = screen.getByRole("button");
    await user.click(submitButton);

    await waitFor(
      () => {
        const button = screen.getByRole("button");
        expect(button).toHaveClass("bg-red-600");
      },
      { timeout: 3000 },
    );
  });

  it("handles non-Error object errors", async () => {
    const user = userEvent.setup();
    mockInquiryService.createInquiry.mockRejectedValue("String error");

    const onError = jest.fn();
    render(
      <TestWrapper>
        <InquiryForm onError={onError} />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(textarea, "テスト問い合わせです。");

    const submitButton = screen.getByRole("button", { name: /送信/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(
        expect.objectContaining({
          message: "送信に失敗しました",
        }),
      );
    });
  });

  it("shows warning color for character count between 4000 and 4500", async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText(
      "問い合わせ内容",
    ) as HTMLTextAreaElement;
    const longText = "あ".repeat(4100);

    // Use paste event to avoid slow typing
    await user.click(textarea);
    await user.paste(longText);

    await waitFor(() => {
      const characterCount = screen.getByText(/4100 \/ 5000/);
      expect(characterCount).toHaveClass("text-yellow-600");
    });
  });

  it("shows error color for character count above 4500", async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText(
      "問い合わせ内容",
    ) as HTMLTextAreaElement;
    const longText = "あ".repeat(4600);

    // Use paste event to avoid slow typing
    await user.click(textarea);
    await user.paste(longText);

    await waitFor(() => {
      const characterCount = screen.getByText(/4600 \/ 5000/);
      expect(characterCount).toHaveClass("text-red-600");
    });
  });

  it("clears pending timeout on component unmount", () => {
    const { unmount } = render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    // Unmount component - should not cause errors even if timers are set
    expect(() => unmount()).not.toThrow();
  });

  it("allows multiple consecutive submissions", async () => {
    const user = userEvent.setup();
    const mockResponse: InquiryResponse = {
      id: 1,
      user_id: "user-001",
      content: "テスト問い合わせです。",
      language: "ja",
      timestamp: "2024-01-01T00:00:00Z",
      status: "received" as any,
      metadata: { source: "web" },
    };

    mockInquiryService.createInquiry.mockResolvedValue(mockResponse);

    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");

    // First submission
    await user.type(textarea, "最初の問い合わせです。");
    const submitButton = screen.getByRole("button");
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockInquiryService.createInquiry).toHaveBeenCalledTimes(1);
    });

    // Second submission
    await user.type(textarea, "二番目の問い合わせです。");
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockInquiryService.createInquiry).toHaveBeenCalledTimes(2);
    });
  });

  it("uses custom userId when provided", async () => {
    const user = userEvent.setup();
    const mockResponse: InquiryResponse = {
      id: 1,
      user_id: "custom-user-123",
      content: "テスト問い合わせです。",
      language: "ja",
      timestamp: "2024-01-01T00:00:00Z",
      status: "received" as any,
      metadata: { source: "web" },
    };

    mockInquiryService.createInquiry.mockResolvedValue(mockResponse);

    render(
      <TestWrapper>
        <InquiryForm userId="custom-user-123" />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(textarea, "テスト問い合わせです。");

    const submitButton = screen.getByRole("button", { name: /送信/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockInquiryService.createInquiry).toHaveBeenCalledWith({
        content: "テスト問い合わせです。",
        language: "ja",
        user_id: "custom-user-123",
      });
    });
  });

  it("shows success message in the UI", async () => {
    const user = userEvent.setup();
    const mockResponse: InquiryResponse = {
      id: 1,
      user_id: "user-001",
      content: "テスト問い合わせです。",
      language: "ja",
      timestamp: "2024-01-01T00:00:00Z",
      status: "received" as any,
      metadata: { source: "web" },
    };

    mockInquiryService.createInquiry.mockResolvedValue(mockResponse);

    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(textarea, "テスト問い合わせです。");

    const submitButton = screen.getByRole("button", { name: /送信/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("問い合わせが正常に送信されました"),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "AIによるストーリー生成が開始されました。しばらくお待ちください。",
      ),
    ).toBeInTheDocument();
  });

  it("shows error message in the UI", async () => {
    const user = userEvent.setup();
    mockInquiryService.createInquiry.mockRejectedValue(
      new Error("Network error"),
    );

    render(
      <TestWrapper>
        <InquiryForm />
      </TestWrapper>,
    );

    const textarea = screen.getByLabelText("問い合わせ内容");
    await user.type(textarea, "テスト問い合わせです。");

    const submitButton = screen.getByRole("button", { name: /送信/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("送信に失敗しました")).toBeInTheDocument();
    });

    expect(
      screen.getByText("ネットワーク接続を確認して、もう一度お試しください。"),
    ).toBeInTheDocument();
  });
});

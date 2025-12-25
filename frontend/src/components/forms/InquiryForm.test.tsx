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
    expect(screen.getByLabelText("言語")).toBeInTheDocument();
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

    const languageSelect = screen.getByLabelText("言語");
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
});

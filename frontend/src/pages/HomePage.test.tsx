import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import HomePage from "./HomePage";

// Import the mocked module
import apiClient from "../services/apiClient";

// Mock axios completely
jest.mock("../services/apiClient", () => ({
  __esModule: true,
  default: {
    get: jest.fn(() => Promise.resolve({ data: { status: "ok" } })),
  },
}));

// Mock react-hot-toast
jest.mock("react-hot-toast", () => ({
  __esModule: true,
  default: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        {ui}
      </BrowserRouter>
    </QueryClientProvider>,
  );
};

describe("HomePage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the main title", () => {
    renderWithProviders(<HomePage />);

    expect(screen.getByText("Ghost Squad")).toBeInTheDocument();
    expect(screen.getByText("AI駆動ストーリーボード機能")).toBeInTheDocument();
  });

  it("displays feature cards", () => {
    renderWithProviders(<HomePage />);

    expect(screen.getByText("問い合わせ管理")).toBeInTheDocument();
    expect(screen.getByText("タスク管理")).toBeInTheDocument();
    expect(screen.getByText("AI統合")).toBeInTheDocument();
  });

  it("shows API status section", () => {
    renderWithProviders(<HomePage />);

    expect(screen.getByText("システム状態:")).toBeInTheDocument();
  });

  it("displays quick action buttons", () => {
    renderWithProviders(<HomePage />);

    expect(screen.getByText("新しい問い合わせを作成")).toBeInTheDocument();
    expect(screen.getByText("タスクを確認")).toBeInTheDocument();
  });

  it("shows connected status when API call succeeds", async () => {
    mockApiClient.get.mockResolvedValueOnce({ data: { status: "ok" } });

    renderWithProviders(<HomePage />);

    await waitFor(() => {
      expect(
        screen.getByText("バックエンドAPIに正常に接続されています"),
      ).toBeInTheDocument();
    });
  });

  it("shows error status when API call fails", async () => {
    mockApiClient.get.mockRejectedValueOnce(new Error("Network error"));

    renderWithProviders(<HomePage />);

    await waitFor(() => {
      expect(
        screen.getByText("バックエンドAPIに接続できませんでした"),
      ).toBeInTheDocument();
    });
  });
});

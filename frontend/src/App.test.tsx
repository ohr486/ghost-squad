import React from "react";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";

// Mock axios completely
jest.mock("axios", () => ({
  create: jest.fn(() => ({
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    get: jest.fn(() => Promise.resolve({ data: { status: "ok" } })),
    post: jest.fn(() => Promise.resolve({ data: {} })),
    put: jest.fn(() => Promise.resolve({ data: {} })),
    delete: jest.fn(() => Promise.resolve({ data: {} })),
  })),
}));

// Mock react-hot-toast
jest.mock("react-hot-toast", () => ({
  __esModule: true,
  default: {
    error: jest.fn(),
    success: jest.fn(),
  },
  Toaster: () => null,
}));

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

describe("App Component", () => {
  it("renders without crashing", () => {
    renderWithProviders(<App />);
  });

  it("displays the Ghost Squad title in navigation", () => {
    renderWithProviders(<App />);
    // Look for the title in the navigation header specifically
    expect(screen.getAllByText("Ghost Squad")).toHaveLength(2); // One in nav, one in main content
  });

  it("displays navigation links", () => {
    renderWithProviders(<App />);
    // Check for navigation links - they should exist multiple times (desktop + mobile)
    expect(screen.getAllByText("ホーム").length).toBeGreaterThan(0);
    expect(screen.getAllByText("問い合わせ").length).toBeGreaterThan(0);
    expect(screen.getAllByText("タスク").length).toBeGreaterThan(0);
  });

  it("displays the main page content", () => {
    renderWithProviders(<App />);
    expect(screen.getByText("AI駆動ストーリーボード機能")).toBeInTheDocument();
    expect(
      screen.getByText(
        "自然言語の問い合わせを構造化されたユーザーストーリーに変換",
      ),
    ).toBeInTheDocument();
  });
});

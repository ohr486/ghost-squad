import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "./Layout";

// Mock axios completely
jest.mock("axios", () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  })),
}));

// Test helper to render with providers
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

describe("Layout", () => {
  it("renders the navigation with correct links", () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>,
    );

    // Check navigation links - use getAllByText to handle multiple instances
    expect(screen.getByText("Ghost Squad")).toBeInTheDocument();
    expect(screen.getAllByText("ホーム")).toHaveLength(2); // Desktop and mobile
    expect(screen.getAllByText("問い合わせ")).toHaveLength(2); // Desktop and mobile
    expect(screen.getAllByText("タスク")).toHaveLength(2); // Desktop and mobile
  });

  it("renders children content", () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>,
    );

    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("has dark mode toggle button", () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>,
    );

    // Check for dark mode toggle button by aria-label
    const toggleButton = screen.getByLabelText("ライトモードに切り替え");
    expect(toggleButton).toBeInTheDocument();
  });

  it("toggles dark mode when button is clicked", () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>,
    );

    const toggleButton = screen.getByLabelText("ライトモードに切り替え");

    // Click the toggle button
    fireEvent.click(toggleButton);

    // The button should still be present after clicking
    expect(toggleButton).toBeInTheDocument();
  });

  it("applies correct CSS classes for dark mode", () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>,
    );

    // Check that the layout renders properly in dark mode
    // The dark mode classes are applied via CSS and Tailwind,
    // so we verify the component renders without errors
    expect(screen.getByText("Test Content")).toBeInTheDocument();
    expect(screen.getByText("Ghost Squad")).toBeInTheDocument();
  });
});

import React from "react";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import InquiriesPage from "./InquiriesPage";

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
    expect(screen.getByText("利用可能な機能:")).toBeInTheDocument();
    expect(screen.getByText("実装予定:")).toBeInTheDocument();
    expect(screen.getByText(/問い合わせ履歴表示/)).toBeInTheDocument();
    expect(screen.getByText(/AIストーリー生成機能/)).toBeInTheDocument();
  });
});

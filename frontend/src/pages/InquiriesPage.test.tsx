import React from "react";
import { render, screen } from "@testing-library/react";
import InquiriesPage from "./InquiriesPage";

describe("InquiriesPage", () => {
  it("renders the page title", () => {
    render(<InquiriesPage />);
    expect(screen.getByText("問い合わせ管理")).toBeInTheDocument();
  });

  it("displays the page description", () => {
    render(<InquiriesPage />);
    expect(
      screen.getByText(
        "自然言語での問い合わせを入力し、AIがストーリーに変換します",
      ),
    ).toBeInTheDocument();
  });

  it("shows the new inquiry button", () => {
    render(<InquiriesPage />);
    expect(screen.getByText("新しい問い合わせ")).toBeInTheDocument();
  });

  it("displays implementation status", () => {
    render(<InquiriesPage />);
    expect(
      screen.getByText("この機能は次のタスクで実装予定です"),
    ).toBeInTheDocument();
    expect(screen.getByText("実装予定:")).toBeInTheDocument();
  });
});

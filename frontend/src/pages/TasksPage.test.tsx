import React from "react";
import { render, screen } from "@testing-library/react";
import TasksPage from "./TasksPage";

describe("TasksPage", () => {
  it("renders the page title", () => {
    render(<TasksPage />);
    expect(screen.getByText("タスク管理")).toBeInTheDocument();
  });

  it("displays the page description", () => {
    render(<TasksPage />);
    expect(
      screen.getByText(
        "生成されたストーリーをレビューし、タスクとして管理します",
      ),
    ).toBeInTheDocument();
  });

  it("shows the filter button", () => {
    render(<TasksPage />);
    expect(screen.getByText("フィルター")).toBeInTheDocument();
  });

  it("displays implementation status", () => {
    render(<TasksPage />);
    expect(
      screen.getByText("この機能は将来のタスクで実装予定です"),
    ).toBeInTheDocument();
    expect(screen.getByText("実装予定:")).toBeInTheDocument();
  });
});

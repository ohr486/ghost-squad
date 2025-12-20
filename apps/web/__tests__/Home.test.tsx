import { render, screen, waitFor } from "@testing-library/react";
import Home from "../app/page";
import "@testing-library/jest-dom";

// fetchをグローバルにモック化
global.fetch = jest.fn();

describe("Command Center (Home)", () => {
  beforeEach(() => {
    // テストごとにモックの呼び出し履歴をリセット
    (global.fetch as jest.Mock).mockClear();
  });

  it("renders the main dashboard", async () => {
    // ▼▼▼ 修正ポイント: URLを見て返し分ける ▼▼▼
    (global.fetch as jest.Mock).mockImplementation((url) => {
      // 1. 履歴一覧 (/missions) は「配列」を返す
      if (url.includes("/missions")) {
        return Promise.resolve({
          ok: true,
          json: async () => [], // 空の配列
        });
      }
      // 2. それ以外 (/mission/current など) は「オブジェクト」を返す
      return Promise.resolve({
        ok: true,
        json: async () => ({
          mission_id: "test-id",
          logs: ["SYSTEM ONLINE"],
          tasks: []
        }),
      });
    });

    render(<Home />);

    // タイトルが表示されるか確認
    await waitFor(() => {
      expect(screen.getByText(/GHOST-SQUAD/i)).toBeInTheDocument();
    });
  });

  it("loads and displays initial logs", async () => {
    const testMission = {
      id: "test-mission-1",
      instruction: "Test",
      status: "done",
      logs: ["SYSTEM TEST OK"], // ★このログが表示されるか確認したい
      tasks: [],
      created_at: new Date().toISOString()
    };

    (global.fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes("/missions")) {
        return Promise.resolve({
          ok: true,
          json: async () => [testMission],
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          mission_id: "test-id-2",
          logs: ["SYSTEM TEST OK"], // テスト用のログ
          tasks: []
        }),
      });
    });

    render(<Home />);

    // APIから取得したログが表示されるのを待つ
    await waitFor(() => {
      expect(screen.getByText("SYSTEM TEST OK")).toBeInTheDocument();
    });
  });
});

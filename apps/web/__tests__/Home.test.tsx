import { render, screen, waitFor } from '@testing-library/react'
import Home from '../app/page'
import '@testing-library/jest-dom'

// fetchのモックを定義（APIが返すデータを偽装）
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({
        mission_id: "test-mission",
        status: "idle",
        logs: ["SYSTEM TEST OK"],
        tasks: [
            { id: "t-1", title: "Test Task", status: "planning", energy: 1.0 }
        ]
    }),
  })
) as jest.Mock;

describe('Command Center (Home)', () => {
  it('renders the main dashboard', async () => {
    render(<Home />)

    // 1. ヘッダーのタイトルが表示されているか確認
    const heading = screen.getByText(/GHOST-SQUAD/i)
    expect(heading).toBeInTheDocument()

    // 2. ステータス表示があるか確認
    expect(screen.getByText(/ONLINE/i)).toBeInTheDocument()

    // 3. 入力フォームがあるか確認
    expect(screen.getByPlaceholderText(/司令官、指示を入力してください/i)).toBeInTheDocument()

    // ★修正ポイント: ここを追加
    // コンポーネントがマウントされると同時に fetch が走るため、
    // その完了（画面更新）を待ってからテストを終了しないと "act(...)" ワーニングが出る
    await waitFor(() => {
        expect(screen.getByText("SYSTEM TEST OK")).toBeInTheDocument()
    })
  })

  // 2つ目のテストは実質的に上のテストと重複確認することになりますが、
  // 「ログが出る」という機能にフォーカスしたテストとして残しておきます
  it('loads and displays initial logs', async () => {
    render(<Home />)

    // 非同期でデータが読み込まれ、ログが表示されるのを待つ
    await waitFor(() => {
        expect(screen.getByText("SYSTEM TEST OK")).toBeInTheDocument()
    })
  })
})

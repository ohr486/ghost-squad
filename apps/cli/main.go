package main

import (
	"fmt"
	"net/http"
	"os"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// --- デザイン定義 (Cyberpunk Style) ---
var (
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#00FFFF")). // Cyan
			Background(lipgloss.Color("#000000")).
			Padding(0, 1).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("#0000FF"))

	statusOk = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#00FF00")). // Green
			SetString("ONLINE")

	statusErr = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FF0000")). // Red
			SetString("OFFLINE")

	subtle = lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
)

// --- アプリケーションの状態 ---
type model struct {
	status    string
	loading   bool
	err       error
	syncRate  int
}

type statusMsg string
type errMsg error

// --- API通信 ---
func checkSystemStatus() tea.Msg {
	// Dockerネットワーク内のAPIコンテナへアクセス
	// ※ ローカル開発でCLI単体で動かす場合は localhost:8000
	url := "http://api:8000/"
	if os.Getenv("API_URL") != "" {
		url = os.Getenv("API_URL")
	}

	client := http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return errMsg(err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		return statusMsg("ALL SYSTEMS GREEN")
	}
	return errMsg(fmt.Errorf("Status Code: %d", resp.StatusCode))
}

// --- Init (初期化) ---
func (m model) Init() tea.Cmd {
	// 起動と同時にステータスチェックを開始
	return tea.Batch(
		tea.Tick(time.Millisecond*500, func(t time.Time) tea.Msg {
			return checkSystemStatus()
		}),
	)
}

// --- Update (イベントループ) ---
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	
	// キー入力
	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c", "esc":
			return m, tea.Quit
		case "r":
			m.loading = true
			return m, func() tea.Msg { return checkSystemStatus() }
		}

	// 通信結果
	case statusMsg:
		m.status = string(msg)
		m.loading = false
		m.syncRate = 100
		return m, nil

	case errMsg:
		m.err = msg
		m.status = "CONNECTION LOST"
		m.loading = false
		return m, nil
	}

	return m, nil
}

// --- View (描画) ---
func (m model) View() string {
	// ヘッダー
	header := titleStyle.Render("GHOST-TERMINAL v0.1")

	// ステータス表示
	var statusView string
	if m.err != nil {
		statusView = fmt.Sprintf("STATUS: %s (%v)", statusErr.Render(), m.err)
	} else if m.loading {
		statusView = "STATUS: SCANNING..."
	} else {
		statusView = fmt.Sprintf("STATUS: %s | SYNC: %d%%", statusOk.Render(), m.syncRate)
	}

	// フッター
	footer := subtle.Render("\n[q]: Quit  [r]: Re-connect")

	return fmt.Sprintf("\n%s\n\n%s\n%s\n", header, statusView, footer)
}

func main() {
	p := tea.NewProgram(model{loading: true})
	if _, err := p.Run(); err != nil {
		fmt.Printf("Alas, there's been an error: %v", err)
		os.Exit(1)
	}
}

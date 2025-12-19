package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/charmbracelet/bubbles/textinput"
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

	statusOk = lipgloss.NewStyle().Foreground(lipgloss.Color("#00FF00")).SetString("ONLINE")
	statusErr = lipgloss.NewStyle().Foreground(lipgloss.Color("#FF0000")).SetString("OFFLINE")
	subtle    = lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
	accent    = lipgloss.NewStyle().Foreground(lipgloss.Color("#FF00FF")) // Magenta
)

// --- アプリケーションの状態 ---
type model struct {
	status    string
	loading   bool
	err       error
	syncRate  int
	
	// 入力モード用
	typing    bool
	textInput textinput.Model
	lastMsg   string // 送信結果の表示用
}

// --- メッセージ型 ---
type statusMsg string
type errMsg error
type missionSentMsg string // 送信完了メッセージ

// --- API通信: ステータス確認 ---
func checkSystemStatus() tea.Msg {
	url := getApiUrl()
	client := http.Client{Timeout: 1 * time.Second}
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

// --- API通信: ミッション開始 (POST) ---
func startMission(instruction string) tea.Cmd {
	return func() tea.Msg {
		url := getApiUrl() + "mission/start"
		
		// JSON作成
		payload := map[string]string{"instruction": instruction}
		jsonData, _ := json.Marshal(payload)

		// リクエスト送信
		resp, err := http.Post(url, "application/json", bytes.NewBuffer(jsonData))
		if err != nil {
			return errMsg(err)
		}
		defer resp.Body.Close()

		if resp.StatusCode == 200 {
			return missionSentMsg(fmt.Sprintf("Orders received: '%s'", instruction))
		}
		return errMsg(fmt.Errorf("Failed to send order: %d", resp.StatusCode))
	}
}

func getApiUrl() string {
	if os.Getenv("API_URL") != "" {
		return os.Getenv("API_URL")
	}
	return "http://api:8000/"
}

// --- Init ---
func initialModel() model {
	ti := textinput.New()
	ti.Placeholder = "Type your orders here..."
	ti.Focus()
	ti.CharLimit = 156
	ti.Width = 40
	// カーソルのスタイル
	ti.Cursor.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("#00FFFF"))

	return model{
		loading:   true,
		textInput: ti,
		typing:    false,
	}
}

func (m model) Init() tea.Cmd {
	return tea.Batch(
		tea.Tick(time.Millisecond*500, func(t time.Time) tea.Msg { return checkSystemStatus() }),
		textinput.Blink,
	)
}

// --- Update ---
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	
	// キー入力
	case tea.KeyMsg:
		// 入力モード中
		if m.typing {
			switch msg.String() {
			case "enter":
				// 送信実行
				order := m.textInput.Value()
				m.typing = false
				m.textInput.Reset()
				m.lastMsg = ">>> TRANSMITTING DATA..."
				return m, startMission(order)
			case "esc":
				// キャンセル
				m.typing = false
				m.textInput.Reset()
				return m, nil
			}
			// 入力文字を更新
			m.textInput, cmd = m.textInput.Update(msg)
			return m, cmd
		}

		// 閲覧モード中
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "i":
			m.typing = true
			return m, textinput.Blink
		}

	// 各種メッセージ処理
	case statusMsg:
		m.status = string(msg)
		m.loading = false
		m.syncRate = 100
	case missionSentMsg:
		m.lastMsg = fmt.Sprintf(">>> ACKNOWLEDGED: %s", string(msg))
	case errMsg:
		m.err = msg
		m.status = "CONNECTION LOST"
		m.loading = false
	}

	return m, nil
}

// --- View ---
func (m model) View() string {
	header := titleStyle.Render("GHOST-TERMINAL v0.2")

	// ステータスエリア
	var statusView string
	if m.err != nil {
		statusView = fmt.Sprintf("STATUS: %s (%v)", statusErr.Render(), m.err)
	} else {
		statusView = fmt.Sprintf("STATUS: %s | SYNC: %d%%", statusOk.Render(), m.syncRate)
	}

	// メインエリア（入力 or ログ）
	var mainView string
	if m.typing {
		mainView = fmt.Sprintf(
			"COMMAND OVERRIDE:\n%s\n\n%s",
			m.textInput.View(),
			subtle.Render("(esc to cancel, enter to execute)"),
		)
	} else {
		// 最新のログを表示
		logColor := lipgloss.Color("#00FF00") // Green
		if m.lastMsg == "" {
			mainView = subtle.Render("Waiting for input...")
		} else {
			mainView = lipgloss.NewStyle().Foreground(logColor).Render(m.lastMsg)
		}
	}

	// フッター
	footer := subtle.Render("\n[i]: Input Command  [q]: Quit")

	return fmt.Sprintf("\n%s\n\n%s\n\n%s\n%s\n", header, statusView, mainView, footer)
}

func main() {
	p := tea.NewProgram(initialModel())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error: %v", err)
		os.Exit(1)
	}
}

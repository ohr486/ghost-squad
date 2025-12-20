from agents.graph import node_planner, node_reporter, node_worker


def test_planner_safe_mode(mocker):
    """
    LLMがエラーを吐いたときに、システムが落ちずに
    'Safe Mode（バックアッププラン）' で動作することを確認するテスト
    """
    # agents.graph モジュール内の 'llm' オブジェクトの 'invoke' メソッドをモック化
    # 呼び出されたら必ず例外(Exception)を投げるように設定
    mock_llm = mocker.patch("agents.graph.llm")
    mock_llm.invoke.side_effect = Exception("API Quota Exceeded")

    # テストデータ
    initial_state = {
        "task_input": "Make a coffee",
        "logs": ["Init"],
        "energy_used": 0.0,
        "current_plan": [],
    }

    # 実行
    result = node_planner(initial_state)

    # 検証
    # 1. クラッシュせずに辞書が返ってくること
    assert isinstance(result, dict)

    # 2. バックアップ用のタスク (t-err-1) が生成されていること
    plan = result["current_plan"]
    assert len(plan) == 3
    assert plan[0]["id"] == "t-err-1"
    assert plan[0]["title"] == "APIクレジット残高の確認"

    # 3. ログにエラー検知の記録があること
    last_log = result["logs"][-1]
    assert "通信障害発生" in last_log


def test_worker_node(mocker):
    """
    Workerノードのテスト。time.sleep をモックして待ち時間をゼロにする。
    """
    # time.sleep を無効化（何もしない関数に置き換え）
    mocker.patch("time.sleep")

    state = {"logs": [], "energy_used": 0.0}

    result = node_worker(state)

    assert result["status"] == "working"
    assert "並列化を開始" in result["logs"][0]
    # エナジーが消費されているか
    assert result["energy_used"] == 0.05


def test_reporter_node():
    """
    Reporterノードのテスト
    """
    state = {"logs": [], "energy_used": 10.0}

    result = node_reporter(state)

    assert result["status"] == "done"
    assert "Mission Complete" in result["logs"][0]

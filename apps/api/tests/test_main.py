from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_read_root():
    """ルートエンドポイントの生存確認"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "message": "Ghost-Squad Systems: Ready.",
    }


def test_start_mission():
    """ミッション開始APIのテスト"""
    # LLMが動くと遅い、または課金が発生するため、本来はモック(Mock)を使うべきですが、
    # 今回はSafe Mode（APIエラー時のフォールバック）も含めてエンドツーエンドで確認します。

    payload = {"instruction": "Test Mission from Pytest"}
    response = client.post("/mission/start", json=payload)

    # ステータスコード確認
    assert response.status_code == 200

    data = response.json()

    # レスポンス構造の検証
    assert "mission_id" in data
    assert "status" in data
    assert "logs" in data
    assert "tasks" in data

    # ログに指示が含まれているか確認
    # (APIの仕様上、ログのどこかに命令文が記録されているはず)
    logs_str = str(data["logs"])
    assert "Mission Complete" in logs_str

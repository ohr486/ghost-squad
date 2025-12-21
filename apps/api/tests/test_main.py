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

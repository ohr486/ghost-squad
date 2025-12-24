"""
Tests for inquiry API endpoints
"""
import pytest
from fastapi.testclient import TestClient

from database import get_db
from main import app
from models.enums.inquiry_status import InquiryStatus


def override_get_db(test_session):
    """Override the get_db dependency for testing"""

    def _get_test_db():
        try:
            yield test_session
        finally:
            pass

    return _get_test_db


@pytest.fixture
def client(test_session):
    """Create a test client with database dependency override"""
    app.dependency_overrides[get_db] = override_get_db(test_session)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestInquiryAPI:
    """Test cases for inquiry API endpoints"""

    def test_create_inquiry_success(self, client, clean_database):
        """Test successful inquiry creation"""
        inquiry_data = {
            "content": "新しい機能を追加したいです",
            "language": "ja",
            "user_id": "test_user_123",
        }

        response = client.post("/api/inquiries/", json=inquiry_data)

        assert response.status_code == 201
        data = response.json()

        assert data["content"] == inquiry_data["content"]
        assert data["language"] == inquiry_data["language"]
        assert data["user_id"] == inquiry_data["user_id"]
        assert data["status"] == InquiryStatus.RECEIVED.value
        assert "id" in data
        assert "timestamp" in data
        assert "metadata" in data

    def test_create_inquiry_validation_error(self, client, clean_database):
        """Test inquiry creation with validation errors"""
        # Test empty content
        inquiry_data = {"content": "", "language": "ja", "user_id": "test_user_123"}

        response = client.post("/api/inquiries/", json=inquiry_data)
        assert response.status_code == 422

        # Test invalid language
        inquiry_data = {
            "content": "Valid content",
            "language": "invalid",
            "user_id": "test_user_123",
        }

        response = client.post("/api/inquiries/", json=inquiry_data)
        assert response.status_code == 422

        # Test missing user_id
        inquiry_data = {"content": "Valid content", "language": "ja"}

        response = client.post("/api/inquiries/", json=inquiry_data)
        assert response.status_code == 422

    def test_get_inquiries_empty(self, client, clean_database):
        """Test getting inquiries when database is empty"""
        response = client.get("/api/inquiries/")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_inquiries_with_data(self, client, clean_database):
        """Test getting inquiries with existing data"""
        # Create test inquiries
        inquiry1_data = {
            "content": "First inquiry",
            "language": "ja",
            "user_id": "user1",
        }
        inquiry2_data = {
            "content": "Second inquiry",
            "language": "en",
            "user_id": "user2",
        }

        # Create inquiries
        response1 = client.post("/api/inquiries/", json=inquiry1_data)
        response2 = client.post("/api/inquiries/", json=inquiry2_data)

        assert response1.status_code == 201
        assert response2.status_code == 201

        # Get all inquiries
        response = client.get("/api/inquiries/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verify data
        contents = [item["content"] for item in data]
        assert "First inquiry" in contents
        assert "Second inquiry" in contents

    def test_get_inquiries_with_user_filter(self, client, clean_database):
        """Test getting inquiries filtered by user"""
        # Create test inquiries for different users
        inquiry1_data = {
            "content": "User1 inquiry",
            "language": "ja",
            "user_id": "user1",
        }
        inquiry2_data = {
            "content": "User2 inquiry",
            "language": "ja",
            "user_id": "user2",
        }

        client.post("/api/inquiries/", json=inquiry1_data)
        client.post("/api/inquiries/", json=inquiry2_data)

        # Get inquiries for user1 only
        response = client.get("/api/inquiries/?user_id=user1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == "user1"
        assert data[0]["content"] == "User1 inquiry"

    def test_get_inquiries_pagination(self, client, clean_database):
        """Test inquiry pagination"""
        # Create multiple inquiries
        for i in range(5):
            inquiry_data = {
                "content": f"Inquiry {i}",
                "language": "ja",
                "user_id": f"user{i}",
            }
            client.post("/api/inquiries/", json=inquiry_data)

        # Test limit
        response = client.get("/api/inquiries/?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Test offset
        response = client.get("/api/inquiries/?offset=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_inquiry_by_id_success(self, client, clean_database):
        """Test getting a specific inquiry by ID"""
        # Create an inquiry
        inquiry_data = {
            "content": "Test inquiry for ID lookup",
            "language": "ja",
            "user_id": "test_user",
        }

        create_response = client.post("/api/inquiries/", json=inquiry_data)
        assert create_response.status_code == 201
        created_inquiry = create_response.json()
        inquiry_id = created_inquiry["id"]

        # Get the inquiry by ID
        response = client.get(f"/api/inquiries/{inquiry_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == inquiry_id
        assert data["content"] == inquiry_data["content"]
        assert data["language"] == inquiry_data["language"]
        assert data["user_id"] == inquiry_data["user_id"]

    def test_get_inquiry_by_id_not_found(self, client, clean_database):
        """Test getting a non-existent inquiry by ID"""
        response = client.get("/api/inquiries/999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_inquiry_by_id_invalid_id(self, client, clean_database):
        """Test getting inquiry with invalid ID format"""
        response = client.get("/api/inquiries/invalid_id")

        assert response.status_code == 422  # Validation error for invalid integer

    def test_get_inquiries_pagination_validation(self, client, clean_database):
        """Test pagination parameter validation"""

        # Test negative limit
        response = client.get("/api/inquiries/?limit=-1")
        assert response.status_code == 422
        data = response.json()
        assert "greater than or equal to 1" in str(data["detail"])

        # Test limit too large
        response = client.get("/api/inquiries/?limit=2000")
        assert response.status_code == 422
        data = response.json()
        assert "less than or equal to 1000" in str(data["detail"])

        # Test negative offset
        response = client.get("/api/inquiries/?offset=-5")
        assert response.status_code == 422
        data = response.json()
        assert "greater than or equal to 0" in str(data["detail"])

        # Test valid boundary values
        response = client.get("/api/inquiries/?limit=1&offset=0")
        assert response.status_code == 200

        response = client.get("/api/inquiries/?limit=1000&offset=0")
        assert response.status_code == 200

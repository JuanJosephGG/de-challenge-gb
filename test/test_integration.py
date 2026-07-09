from fastapi.testclient import TestClient
from main import app
from src.connections.database import get_db

# 1. Initialize the TestClient with our FastAPI app
client = TestClient(app)

# 2. Create a mock for the database session
def override_get_db():
    # In a real enterprise test suite, this would yield a temporary SQLite in-memory DB.
    # For this demonstration, we yield a dummy string to bypass the real DB connection.
    yield "mocked_db_session"

# Override the actual get_db dependency with our mock
app.dependency_overrides[get_db] = override_get_db

def test_health_check_endpoint():
    """Tests if the API boots up correctly and responds to the root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "API is running securely"}

def test_historical_upload_rejects_non_csv():
    """Integration test: validates that the file upload endpoint rejects wrong formats."""
    # Simulate uploading a .txt file instead of a .csv
    files = {'file': ('test.txt', b"dummy content", 'text/plain')}
    
    response = client.post("/api/v1/historical/departments", files=files)
    
    # We expect an HTTP 400 Bad Request directly from the API router logic
    assert response.status_code == 400
    assert response.json()["detail"] == "The file must be a CSV."
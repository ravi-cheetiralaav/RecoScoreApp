"""Integration tests for the API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite:///./test_recoscore.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "disclaimer" in data


class TestIngestionEndpoint:
    def test_trigger_ingestion(self, client):
        response = client.post("/ingestion/trigger", json={"limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert "fetched" in data
        assert "new" in data
        assert "processed" in data
        assert data["fetched"] >= 0


class TestRecommendationsEndpoint:
    def test_list_recommendations(self, client):
        # First ingest some data
        client.post("/ingestion/trigger", json={"limit": 5})

        response = client.get("/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_filter_by_action(self, client):
        response = client.get("/recommendations?action=buy")
        assert response.status_code == 200

    def test_invalid_rec_id(self, client):
        response = client.get("/recommendations/99999")
        assert response.status_code == 404


class TestReportsEndpoint:
    def test_summary(self, client):
        response = client.get("/reports/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_recommendations" in data
        assert "hit_rate" in data
        assert "disclaimer" in data

    def test_full_report(self, client):
        response = client.get("/reports/full")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "top_recommendations" in data
        assert "worst_recommendations" in data

    def test_hit_rate_by_month(self, client):
        response = client.get("/reports/hit-rate-by-month")
        assert response.status_code == 200
        assert "data" in response.json()

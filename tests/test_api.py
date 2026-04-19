import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_booking_page():
    response = client.get("/booking")
    assert response.status_code == 200

def test_portfolio_page():
    response = client.get("/portfolio")
    assert response.status_code == 200

def test_admin_login_page():
    response = client.get("/api/admin/login")
    assert response.status_code == 200

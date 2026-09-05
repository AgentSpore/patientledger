import pytest
from fastapi.testclient import TestClient
from patientledger.main import app

@pytest.fixture
def client():
    return TestClient(app)

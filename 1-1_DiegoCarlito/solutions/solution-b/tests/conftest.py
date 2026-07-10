import pytest
from fastapi.testclient import TestClient
from src.app import app

VALID_CUSTOMER_PAYLOAD = {
    "gender": "Female",
    "SeniorCitizen": 0,
    "Partner": "No",
    "Dependents": "No",
    "tenure": 2,
    "PhoneService": "Yes",
    "MultipleLines": "No",
    "InternetService": "Fiber optic",
    "OnlineSecurity": "No",
    "OnlineBackup": "No",
    "DeviceProtection": "No",
    "TechSupport": "No",
    "StreamingTV": "No",
    "StreamingMovies": "No",
    "Contract": "Month-to-month",
    "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": 95.5,
    "TotalCharges": "191.0",
}


@pytest.fixture
def client():
    """Sobe o app disparando o evento de startup (carrega o agente com o model.joblib real)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_payload() -> dict:
    return dict(VALID_CUSTOMER_PAYLOAD)


class FakeGeminiResponse:
    """Simula o objeto de resposta do SDK do Gemini (só o atributo `.text` importa aqui)."""

    def __init__(self, text: str):
        self.text = text

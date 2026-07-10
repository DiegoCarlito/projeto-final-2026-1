from typing import Literal
from pydantic import BaseModel, Field

# Guardrail de saída: chaves e limites que toda resposta do agente precisa respeitar
REQUIRED_OUTPUT_KEYS = {"churn_probability", "risk_factors", "recommended_action"}
MIN_RISK_FACTORS = 1
MIN_PROBABILITY = 0.0
MAX_PROBABILITY = 1.0


class CustomerPayload(BaseModel):
    """Guardrail de entrada: contrato estrito do perfil do cliente.

    Diferente das solutions A e B (que aceitam qualquer string nos campos
    categóricos), aqui os campos usam `Literal` com os valores reais do dataset
    Telco Customer Churn — um valor fora dessas categorias é "fora de escopo" e
    é rejeitado pelo FastAPI/Pydantic antes de qualquer chamada ao modelo.
    """

    gender: Literal["Female", "Male"]
    SeniorCitizen: Literal[0, 1]
    Partner: Literal["No", "Yes"]
    Dependents: Literal["No", "Yes"]
    tenure: int = Field(ge=0, le=100)
    PhoneService: Literal["No", "Yes"]
    MultipleLines: Literal["No", "No phone service", "Yes"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: Literal["No", "No internet service", "Yes"]
    OnlineBackup: Literal["No", "No internet service", "Yes"]
    DeviceProtection: Literal["No", "No internet service", "Yes"]
    TechSupport: Literal["No", "No internet service", "Yes"]
    StreamingTV: Literal["No", "No internet service", "Yes"]
    StreamingMovies: Literal["No", "No internet service", "Yes"]
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: Literal["No", "Yes"]
    PaymentMethod: Literal[
        "Bank transfer (automatic)",
        "Credit card (automatic)",
        "Electronic check",
        "Mailed check",
    ]
    MonthlyCharges: float = Field(ge=0)
    TotalCharges: str  # Pode vir em string devido à formatação do dataset


def is_valid_llm_output(data: dict) -> bool:
    """Guardrail de saída: reprova qualquer resposta do LLM que não tenha o formato
    exigido (chaves faltando, tipos errados, probabilidade fora de [0, 1] ou lista de
    fatores vazia) — sinal de alucinação ou de JSON malformado. Quem chama esta função
    decide o que fazer com a reprovação (nesta solução, aciona o fallback).
    """
    if not REQUIRED_OUTPUT_KEYS.issubset(data.keys()):
        return False

    probability = data["churn_probability"]
    if not isinstance(probability, (int, float)) or isinstance(probability, bool):
        return False
    if not (MIN_PROBABILITY <= probability <= MAX_PROBABILITY):
        return False

    risk_factors = data["risk_factors"]
    if not isinstance(risk_factors, list) or len(risk_factors) < MIN_RISK_FACTORS:
        return False
    if not all(isinstance(factor, str) and factor.strip() for factor in risk_factors):
        return False

    recommended_action = data["recommended_action"]
    if not isinstance(recommended_action, str) or not recommended_action.strip():
        return False

    return True

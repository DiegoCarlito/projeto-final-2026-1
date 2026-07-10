from conftest import FakeGeminiResponse
from src.agent_c import ChurnAgentC
from src.fallback import (
    generate_fallback_response,
    GENERIC_FALLBACK_ACTION,
    GRAY_ZONE_FALLBACK_ACTION,
    HIGH_RISK_FALLBACK_ACTION,
)
from src.guardrails import is_valid_llm_output

PREDICT_ENDPOINT = "/api/v1/predict"

VALID_LLM_OUTPUT = {
    "churn_probability": 0.7,
    "risk_factors": ["Contrato mensal.", "Fatura alta."],
    "recommended_action": "Oferecer desconto.",
}


# --- Guardrail de entrada (payload HTTP) -----------------------------------------


def test_missing_required_field_is_rejected_by_guardrail(client, valid_payload):
    incomplete_payload = dict(valid_payload)
    del incomplete_payload["Contract"]

    response = client.post(PREDICT_ENDPOINT, json=incomplete_payload)

    assert response.status_code == 422


def test_invalid_field_type_is_rejected_by_guardrail(client, valid_payload):
    invalid_payload = dict(valid_payload)
    invalid_payload["tenure"] = "não é um número"

    response = client.post(PREDICT_ENDPOINT, json=invalid_payload)

    assert response.status_code == 422


def test_out_of_scope_category_is_rejected_by_guardrail(client, valid_payload):
    """Diferença da Solution C em relação à A/B: valores categóricos fora do dataset
    (Literal no guardrails.py) são rejeitados, não silenciosamente ignorados.
    """
    out_of_scope_payload = dict(valid_payload)
    out_of_scope_payload["Contract"] = "Weekly"

    response = client.post(PREDICT_ENDPOINT, json=out_of_scope_payload)

    assert response.status_code == 422


# --- Fluxo feliz e fallback via API -----------------------------------------------


def test_valid_payload_with_llm_success_returns_expected_shape(client, valid_payload, monkeypatch):
    import json

    fake_json = json.dumps(VALID_LLM_OUTPUT)
    monkeypatch.setattr(
        "src.app.agent.llm.generate_content",
        lambda prompt, **kwargs: FakeGeminiResponse(fake_json),
    )

    response = client.post(PREDICT_ENDPOINT, json=valid_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["system_status"]["llm_executed"] is True
    assert body["system_status"]["confidence_zone"] == "standard"


def test_llm_failure_triggers_fallback_without_leaking_raw_error(client, valid_payload, monkeypatch):
    def raise_api_error(prompt, **kwargs):
        raise RuntimeError("Simulação de indisponibilidade da API do Gemini")

    monkeypatch.setattr("src.app.agent.llm.generate_content", raise_api_error)

    response = client.post(PREDICT_ENDPOINT, json=valid_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["system_status"]["llm_executed"] is False
    assert "Simulação de indisponibilidade" not in response.text
    assert "Traceback" not in response.text


def test_malformed_llm_output_is_rejected_by_output_guardrail_and_falls_back(client, valid_payload, monkeypatch):
    """Guardrail de saída: um JSON com a probabilidade fora de [0, 1] (sinal de
    alucinação/formato quebrado) não pode ser aceito como resposta válida.
    """
    malformed_json = '{"churn_probability": 4.2, "risk_factors": ["x"], "recommended_action": "y"}'
    monkeypatch.setattr(
        "src.app.agent.llm.generate_content",
        lambda prompt, **kwargs: FakeGeminiResponse(malformed_json),
    )

    response = client.post(PREDICT_ENDPOINT, json=valid_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["system_status"]["llm_executed"] is False


def test_gray_zone_customer_gets_marked_in_system_status(client, gray_zone_payload, monkeypatch):
    import json

    fake_json = json.dumps(VALID_LLM_OUTPUT)
    monkeypatch.setattr(
        "src.app.agent.llm.generate_content",
        lambda prompt, **kwargs: FakeGeminiResponse(fake_json),
    )

    response = client.post(PREDICT_ENDPOINT, json=gray_zone_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["system_status"]["confidence_zone"] == "gray_zone"


# --- Guardrail de saída (função pura) ---------------------------------------------


def test_is_valid_llm_output_accepts_well_formed_response():
    assert is_valid_llm_output(VALID_LLM_OUTPUT) is True


def test_is_valid_llm_output_rejects_missing_key():
    incomplete = {"churn_probability": 0.5, "risk_factors": ["x"]}
    assert is_valid_llm_output(incomplete) is False


def test_is_valid_llm_output_rejects_probability_out_of_range():
    invalid = {**VALID_LLM_OUTPUT, "churn_probability": 1.5}
    assert is_valid_llm_output(invalid) is False


def test_is_valid_llm_output_rejects_empty_risk_factors():
    invalid = {**VALID_LLM_OUTPUT, "risk_factors": []}
    assert is_valid_llm_output(invalid) is False


# --- Fallback determinístico por zona (função pura) -------------------------------


def test_fallback_response_uses_gray_zone_action():
    result = generate_fallback_response(0.5, [{"feature": "tenure", "shap_value": 0.1}], "gray_zone")
    assert result["recommended_action"] == GRAY_ZONE_FALLBACK_ACTION
    assert result["system_status"] == {"llm_executed": False, "confidence_zone": "gray_zone"}


def test_fallback_response_uses_high_risk_action():
    result = generate_fallback_response(0.97, [{"feature": "tenure", "shap_value": 0.3}], "high_risk_escalation")
    assert result["recommended_action"] == HIGH_RISK_FALLBACK_ACTION


def test_fallback_response_uses_generic_action_for_standard_zone():
    result = generate_fallback_response(0.6, [{"feature": "tenure", "shap_value": 0.2}], "standard")
    assert result["recommended_action"] == GENERIC_FALLBACK_ACTION


# --- Classificação de zona de confiança e escalonamento (lógica interna do agente) --


def test_high_probability_alone_does_not_trigger_escalation():
    """Probabilidade extrema sozinha não basta — precisa também de fatura alta
    (agent.md §10). Evita escalonamento desnecessário para clientes de baixo valor.
    """
    agent = ChurnAgentC()
    zone = agent._determine_confidence_zone(0.97, {"MonthlyCharges": 50.0})
    assert zone == "standard"


def test_high_probability_and_high_charges_trigger_escalation():
    agent = ChurnAgentC()
    zone = agent._determine_confidence_zone(0.97, {"MonthlyCharges": 150.0})
    assert zone == "high_risk_escalation"


def test_gray_zone_boundaries_are_inclusive():
    agent = ChurnAgentC()
    assert agent._determine_confidence_zone(0.45, {"MonthlyCharges": 50.0}) == "gray_zone"
    assert agent._determine_confidence_zone(0.55, {"MonthlyCharges": 50.0}) == "gray_zone"
    assert agent._determine_confidence_zone(0.44, {"MonthlyCharges": 50.0}) == "standard"


def test_escalation_zone_overrides_llm_recommended_action():
    """A regra determinística de escalonamento humano prevalece sobre qualquer
    sugestão do LLM, mesmo quando o LLM responde com sucesso.
    """
    agent = ChurnAgentC()
    llm_result = {
        "churn_probability": 0.97,
        "risk_factors": ["x"],
        "recommended_action": "Oferecer 10% de desconto",
    }

    final = agent._finalize_success_response(llm_result, "high_risk_escalation")

    assert final["recommended_action"] == "Escalar imediatamente para um gerente de Customer Success."
    assert final["system_status"] == {"llm_executed": True, "confidence_zone": "high_risk_escalation"}

from conftest import FakeGeminiResponse
from src.model_wrapper import RandomForestModelWrapper
from src.shap_tool import ShapExplainer

PREDICT_ENDPOINT = "/api/v1/predict"


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


def test_valid_payload_with_llm_success_returns_expected_shape(client, valid_payload, monkeypatch):
    fake_json = (
        '{"churn_probability": 0.85, '
        '"risk_factors": ["Tempo de permanência curto.", "Contrato mensal."], '
        '"recommended_action": "Oferecer contrato anual com desconto."}'
    )
    monkeypatch.setattr(
        "src.app.agent.llm.generate_content",
        lambda prompt: FakeGeminiResponse(fake_json),
    )

    response = client.post(PREDICT_ENDPOINT, json=valid_payload)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"churn_probability", "risk_factors", "recommended_action"}
    assert body["churn_probability"] == 0.85


def test_llm_failure_triggers_fallback_without_leaking_raw_error(client, valid_payload, monkeypatch):
    def raise_api_error(prompt):
        raise RuntimeError("Simulação de indisponibilidade da API do Gemini")

    monkeypatch.setattr("src.app.agent.llm.generate_content", raise_api_error)

    response = client.post(PREDICT_ENDPOINT, json=valid_payload)

    assert response.status_code == 200
    body = response.json()
    assert "Fallback" in body["recommended_action"]
    assert "Simulação de indisponibilidade" not in response.text
    assert "Traceback" not in response.text


def test_shap_explainer_returns_top_factors_sorted_by_impact(valid_payload):
    """Cobertura direta da ferramenta de explicabilidade (sem passar pela API/LLM):
    confirma que os valores SHAP retornados estão ordenados do maior para o menor
    impacto no risco de churn — é essa ordenação que o agente repassa ao LLM.
    """
    model_wrapper = RandomForestModelWrapper()
    shap_explainer = ShapExplainer(model_wrapper)

    top_factors = shap_explainer.get_top_risk_factors(valid_payload, top_n=3)

    assert len(top_factors) == 3
    assert all({"feature", "shap_value"} <= factor.keys() for factor in top_factors)
    shap_values = [factor["shap_value"] for factor in top_factors]
    assert shap_values == sorted(shap_values, reverse=True)

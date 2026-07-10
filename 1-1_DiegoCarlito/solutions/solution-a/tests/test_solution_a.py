from conftest import FakeGeminiResponse

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
        '{"churn_probability": 0.42, '
        '"risk_factors": ["Contrato mensal aumenta o risco."], '
        '"recommended_action": "Oferecer desconto no plano anual."}'
    )
    monkeypatch.setattr(
        "src.app.agent.llm.generate_content",
        lambda prompt: FakeGeminiResponse(fake_json),
    )

    response = client.post(PREDICT_ENDPOINT, json=valid_payload)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"churn_probability", "risk_factors", "recommended_action"}
    assert body["churn_probability"] == 0.42
    assert isinstance(body["risk_factors"], list)


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

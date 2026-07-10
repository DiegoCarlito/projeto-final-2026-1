# Evidência — Validação prática da Solution A (09/07/2026)

> Execução local completa: treino do modelo, subida do servidor FastAPI e chamada real ao endpoint (incluindo chamada real à API do Gemini 2.5 Flash, sem fallback).

## 1. Treino do modelo

```
$ python src/train.py
Iniciando treino do modelo baseline (Solution A)...
Treino concluído. Acurácia no teste: 0.7875 | ROC-AUC: 0.8319
              precision    recall  f1-score   support

    No Churn       0.83      0.89      0.86      1033
       Churn       0.62      0.52      0.56       374

    accuracy                           0.79      1407
   macro avg       0.73      0.70      0.71      1407
weighted avg       0.78      0.79      0.78      1407

Modelo salvo em src/model.joblib
```

Recall de apenas 0.52 na classe Churn (contra 0.78 na Solution B, que usa `class_weight="balanced"`) — esperado para o baseline sem correção de desbalanceamento; registrado aqui como característica conhecida da Solution A, não como bug.

## 2. Servidor local

```
$ uvicorn src.app:app --port 8001
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8001
```

## 3. Requisição válida — `POST /api/v1/predict`

**Payload de entrada:**

```json
{
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
  "TotalCharges": "191.0"
}
```

**Resposta (HTTP 200, gerada pelo modelo tabular + Gemini 2.5 Flash real, não fallback):**

```json
{
  "churn_probability": 0.6349,
  "risk_factors": [
    "O serviço de internet por fibra óptica.",
    "A adesão ao faturamento sem papel (Paperless Billing).",
    "Os encargos totais, que, embora baixos devido à curta permanência, crescerão rapidamente com os altos encargos mensais (R$ 95,50)."
  ],
  "recommended_action": "Contatar o cliente proativamente para oferecer um plano com melhor custo-benefício, adicionando serviços de valor (e.g., segurança, suporte técnico) e incentivando um contrato de longo prazo para estabilizar a relação e reduzir a percepção de alto custo."
}
```

Log do servidor: `INFO: 127.0.0.1 - "POST /api/v1/predict HTTP/1.1" 200 OK`

## 4. Guardrail de entrada inválida — payload incompleto/tipos errados

**Payload de entrada:**

```json
{ "gender": "Female", "tenure": "abc" }
```

**Resposta:** `HTTP 422 Unprocessable Entity`, com o Pydantic listando cada campo obrigatório faltante e o erro de tipagem em `tenure` (`"Input should be a valid integer"`). Confirma o critério de aceitação do `mission-brief.md` §7: "O sistema deve possuir guardrails para rejeitar payloads com tipos de dados inválidos ou colunas faltantes" — a rejeição acontece na camada Pydantic, antes de qualquer chamada ao modelo ou ao LLM.

## 5. Conclusão

Pipeline de ponta a ponta validado: `payload → modelo tabular (Regressão Logística) → Gemini 2.5 Flash → JSON estruturado`. Guardrail de entrada confirmado. Fallback (LLM indisponível) já implementado em `agent_a.py::_generate_fallback`, mas não foi re-exercitado nesta sessão pois a API key estava configurada; validação do caminho de fallback fica pendente para a bateria de testes automatizados (Etapa 5 do runbook).

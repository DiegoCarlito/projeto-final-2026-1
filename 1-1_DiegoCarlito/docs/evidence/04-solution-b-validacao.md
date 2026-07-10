# Evidência — Implementação e validação da Solution B (09/07/2026)

> Execução local completa: treino do Random Forest, subida do servidor FastAPI e chamada real ao endpoint com explicabilidade SHAP local + Gemini 2.5 Flash (sem fallback).

## 1. Treino do modelo

```
$ python src/train.py
Iniciando treino do modelo Random Forest (Solution B)...
Treino concluído. Acurácia no teste: 0.7477 | ROC-AUC: 0.8388
              precision    recall  f1-score   support

    No Churn       0.90      0.74      0.81      1033
       Churn       0.52      0.78      0.62       374

    accuracy                           0.75      1407
   macro avg       0.71      0.76      0.72      1407
weighted avg       0.80      0.75      0.76      1407

Modelo salvo em src/model.joblib
```

`class_weight="balanced"` foi usado para compensar o desbalanceamento de classes; o recall de 0.78 na classe Churn mostra que o modelo prioriza não deixar clientes em risco passarem despercebidos, ao custo de mais falsos positivos — trade-off aceitável para este domínio (mission-brief.md §8).

## 2. Servidor local

```
$ uvicorn src.app:app --port 8002
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8002
```

Nenhum erro na inicialização do `shap.TreeExplainer`, confirmando que o SHAP é compatível com o pipeline (`ColumnTransformer` + `RandomForestClassifier`).

## 3. Requisição válida — `POST /api/v1/predict`

**Payload de entrada:** o mesmo cliente usado na validação da Solution A (fibra óptica, contrato mensal, tenure=2, sem serviços adicionais).

**Resposta (HTTP 200, gerada pelo modelo + SHAP local + Gemini 2.5 Flash real, não fallback):**

```json
{
  "churn_probability": 0.85,
  "risk_factors": [
    "Tempo de permanência muito curto com a empresa (apenas 2 meses).",
    "O tipo de serviço de internet (fibra óptica), que pode estar associado a altas expectativas ou problemas iniciais.",
    "A ausência de um contrato de longo prazo (o cliente possui um contrato mensal), o que facilita o cancelamento a qualquer momento."
  ],
  "recommended_action": "Contatar o cliente imediatamente para entender sua experiência inicial com o serviço de fibra óptica e o relacionamento geral com a empresa. Oferecer um benefício exclusivo (ex: desconto no valor mensal, upgrade de velocidade, ou um brinde) para incentivar a migração para um plano com contrato de maior duração (anual ou bienal), focando em estabilizar o cliente a longo prazo e resolver quaisquer insatisfações precoces."
}
```

Comparado à Solution A (mesmo cliente, probabilidade 0.63 com coeficientes globais), a Solution B captura interações não-lineares e devolve uma probabilidade mais alta (0.85) ancorada nos valores SHAP locais deste cliente específico — não em pesos globais do modelo inteiro.

## 4. Guardrail de entrada inválida

**Payload:** `{ "gender": "Female", "tenure": "abc" }` → **Resposta:** `HTTP 422`, mesma validação Pydantic da Solution A (campos obrigatórios listados, erro de tipagem em `tenure`).

## 5. Conclusão

Pipeline `payload → Random Forest → ShapExplainer (SHAP local) → Gemini 2.5 Flash → JSON estruturado` validado de ponta a ponta. A explicação agora é ancorada em contribuições matemáticas exatas por cliente (`shap_tool.py`), não em coeficientes globais fixos como na Solution A — reduz o risco de o LLM generalizar demais ou alucinar causas. Fallback (`agent_b.py::_generate_fallback`) implementado seguindo o mesmo padrão da Solution A, mas não re-exercitado nesta sessão (API key configurada); testes automatizados do fallback e dos guardrails ficam para a Etapa 5 do runbook.

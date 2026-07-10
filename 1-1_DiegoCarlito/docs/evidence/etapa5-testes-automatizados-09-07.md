# Evidência — Etapa 5: testes automatizados (09/07/2026)

> 27 testes automatizados (pytest) cobrindo as três soluções: guardrail de entrada,
> sucesso com LLM (mockado, para determinismo), fallback (LLM falha, timeout ou saída
> malformada), e — só na Solution C — guardrail de saída, zona cinzenta e escalonamento
> de alto risco. Nenhum teste depende de rede: o LLM é sempre mockado via
> `monkeypatch`/`FakeGeminiResponse`, garantindo que a suíte rode determinística e
> rapidamente em qualquer ambiente (inclusive CI).

## Como rodar

```bash
cd solutions/solution-a && python -m pytest tests/ -v   # requer model.joblib (rode src/train.py antes)
cd solutions/solution-b && python -m pytest tests/ -v
cd solutions/solution-c && python -m pytest tests/ -v
```

## Resultado

```
=== solution-a ===
4 passed, 4 warnings in 0.61s

=== solution-b ===
5 passed, 4 warnings in 0.40s

=== solution-c ===
18 passed, 4 warnings in 0.74s
```

**Total: 27 passed, 0 failed.**

## Cobertura por solução

### Solution A (4 testes)
- Guardrail de entrada: campo obrigatório faltando → 422; tipo inválido → 422.
- Fluxo feliz: LLM mockado retornando JSON válido → 200 com as 3 chaves esperadas.
- Fallback: LLM lança exceção → 200 com `recommended_action` de fallback, sem vazar a
  mensagem de erro original nem stack trace no corpo da resposta.

### Solution B (5 testes)
- Os mesmos 4 casos da Solution A.
- `test_shap_explainer_returns_top_factors_sorted_by_impact`: cobertura direta da
  ferramenta SHAP (sem passar pela API), usando o `model.joblib` real treinado nesta
  sessão — confirma que os fatores retornados vêm ordenados do maior para o menor
  impacto no score de churn.

### Solution C (18 testes)
- Guardrail de entrada: campo faltando, tipo inválido e **categoria fora de escopo**
  (`Contract: "Weekly"`) → 422 nos três casos — a Solution C é a única que rejeita
  esse terceiro caso (A/B aceitam qualquer string e o `OneHotEncoder` ignora em
  silêncio).
- Fluxo feliz e fallback por falha do LLM (mesmo padrão de A/B), verificando também
  `system_status.llm_executed`.
- Guardrail de saída: uma resposta do LLM com `churn_probability` fora de `[0, 1]` é
  reprovada e aciona o fallback automaticamente.
- Zona cinzenta: cliente real do dataset (`GRAY_ZONE_CUSTOMER_PAYLOAD`, probabilidade
  ≈0.46) é classificado como `"gray_zone"` no `system_status`.
- `is_valid_llm_output` (função pura): aceita resposta bem formada, rejeita chave
  faltando, probabilidade fora de intervalo e lista de fatores vazia.
- `generate_fallback_response` (função pura): confirma o texto de ação correto para
  cada uma das três zonas (`gray_zone`, `high_risk_escalation`, `standard`).
- `_determine_confidence_zone` (lógica interna do agente): confirma que probabilidade
  alta sozinha **não** basta para escalonar (precisa também de fatura alta, conforme
  `agent.md` §10); que os limites da zona cinzenta (0.45 e 0.55) são inclusivos.
- `_finalize_success_response`: confirma que o escalonamento de alto risco **sobrepõe**
  a `recommended_action` sugerida pelo próprio LLM.

## O que ficou fora desta rodada

- Teste de timeout real (o `DeadlineExceeded` documentado em
  `docs/evidence/solution-c-validacao-09-07.md` foi genuíno, não simulado em teste
  automatizado) — simular um timeout de rede de forma determinística exigiria mockar a
  camada de transporte gRPC do SDK do Gemini, não coberto nesta rodada por custo/benefício
  baixo frente ao já validado manualmente.
- Testes de carga/latência sob concorrência (fora do escopo da Etapa 5 do runbook).

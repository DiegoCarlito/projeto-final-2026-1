# Evidência — Implementação e validação da Solution C (09/07/2026)

> Pipeline multi-etapa com guardrails de entrada/saída, zona cinzenta e fallback. Validado
> localmente com chamadas reais ao Gemini 2.5 Flash — incluindo uma falha real da API,
> não simulada, que exercitou o mecanismo de degradação graciosa de verdade.

## 1. Treino do modelo

Mesmo modelo da Solution B (Random Forest, `class_weight="balanced"`), retreinado neste diretório:

```
$ python src/train.py
Iniciando treino do modelo Random Forest (Solution C)...
Treino concluído. Acurácia no teste: 0.7477 | ROC-AUC: 0.8388
...
Modelo salvo em src/model.joblib
```

## 2. Ajuste do timeout do LLM (achado real desta sessão)

O README original sugeria um timeout "agressivo" de exemplo (2.0s). Testado na prática, esse
valor estourava quase sempre — uma chamada simples ao Gemini 2.5 Flash já leva ~1.5s, e o
prompt completo (dados do cliente + fatores SHAP + geração de JSON) frequentemente passa disso.
Ajustado para **8.0s** (`agent_c.py::LLM_TIMEOUT_SECONDS`), valor mais realista para o caminho de
sucesso sem deixar de ser um limite de proteção. README atualizado para refletir o valor real.

## 3. Cenário de sucesso — zona cinzenta (LLM ativo)

**Cliente:** tenure=10, DSL, sem serviços adicionais, contrato mensal, MonthlyCharges=29.75 →
`churn_probability = 0.4606` (dentro de [0.45, 0.55]).

**Resposta (HTTP 200, Gemini 2.5 Flash real):**

```json
{
  "churn_probability": 0.4606,
  "risk_factors": [
    "Ter um contrato mensal, o que geralmente está associado a uma maior probabilidade de cancelamento.",
    "Pouco tempo de fidelidade com a empresa (10 meses).",
    "Total de valores pagos relativamente baixos, indicando um relacionamento ainda inicial."
  ],
  "recommended_action": "Contato preventivo de relacionamento para explorar a satisfação e as necessidades do cliente, deixando claro que não há fortes indícios históricos de cancelamento imediato.",
  "system_status": { "llm_executed": true, "confidence_zone": "gray_zone" }
}
```

A instrução extra injetada no prompt para zona cinzenta (`GRAY_ZONE_PROMPT_INSTRUCTION`) funcionou:
o LLM devolveu uma ação exploratória leve, não uma oferta agressiva — conforme `agent.md` §7 e §9.

## 4. Cenário de fallback real (não simulado) — falha genuína da API

**Cliente:** o mesmo usado na validação de A e B (fibra óptica, tenure=2, contrato mensal,
MonthlyCharges=95.5) → `churn_probability = 0.85` (`confidence_zone = "standard"`).

**Log do servidor:**

```
Erro no Agente LLM (DeadlineExceeded): 504 The request timed out. Please try again.. Acionando fallback.
```

**Resposta (HTTP 200, nunca um erro cru ao usuário):**

```json
{
  "churn_probability": 0.85,
  "risk_factors": [
    "Indicador crítico detectado na variável: tenure (peso +0.0872)",
    "Indicador crítico detectado na variável: InternetService_Fiber optic (peso +0.0446)"
  ],
  "recommended_action": "Analisar perfil do cliente no painel para ação manual de retenção (Resposta de Fallback).",
  "system_status": { "llm_executed": false, "confidence_zone": "standard" }
}
```

Esse `DeadlineExceeded` veio do lado do Google (504 real, não do timeout do cliente — a chamada
durou ~5.5s, abaixo dos 8.0s configurados), reproduzido em duas chamadas separadas. É exatamente
o risco "Latência alta / Falha na API do LLM" do `mission-brief.md` §8 acontecendo de verdade
neste ambiente — e a mitigação (fallback) funcionou nas duas vezes, sem stack trace exposto.

## 5. Guardrail de entrada — categoria fora de escopo

**Payload:** mesmo cliente do item 4, mas `"Contract": "Weekly"` (valor que não existe no
dataset). **Resposta:** `HTTP 422`, `"Input should be 'Month-to-month', 'One year' or 'Two year'"`.

Diferença em relação às Solutions A e B: lá, um valor categórico inválido passaria despercebido
pelo Pydantic (`str` solto) e seria silenciosamente zerado pelo `OneHotEncoder(handle_unknown="ignore")`
— não é um erro, mas também não é um guardrail. Aqui, com `Literal` no `guardrails.py`, o valor
fora de escopo é rejeitado antes de qualquer chamada ao modelo.

## 6. Guardrail de entrada — campos faltando/tipo errado

**Payload:** `{"gender": "Female", "tenure": "abc"}` → `HTTP 422`, mesma validação de A/B
(campos obrigatórios listados + erro de tipagem em `tenure`).

## 7. Zona cinzenta e escalonamento de alto risco — verificação direta da lógica de decisão

O dataset real não contém nenhum cliente com probabilidade > 95% (máximo observado: ~0.926 com
este modelo), então a regra de escalonamento (`agent.md` §10) foi verificada chamando
`ChurnAgentC._determine_confidence_zone` e `_finalize_success_response` diretamente com valores
sintéticos de probabilidade/`MonthlyCharges`, em vez de via HTTP:

```
prob=0.97, MonthlyCharges=150 -> high_risk_escalation
prob=0.97, MonthlyCharges=50  -> standard   (probabilidade alta sozinha não basta)
prob=0.50, MonthlyCharges=80  -> gray_zone
recommended_action final -> "Escalar imediatamente para um gerente de Customer Success."
TODOS OS CASOS DE ESCALONAMENTO PASSARAM
```

Confirma que a regra de escalonamento humano é determinística e prevalece sobre qualquer
sugestão do LLM, mesmo quando o LLM responde com sucesso.

## 8. Conclusão

Pipeline multi-etapa validado: guardrail de entrada (Pydantic + `Literal`) → modelo → zona de
confiança → SHAP → LLM com timeout → guardrail de saída → fallback determinístico por zona.
Diferente das evidências de A e B, aqui o fallback não foi apenas testado — foi acionado por uma
falha real e não planejada da API do Gemini, validando o mecanismo de degradação graciosa nas
condições que ele foi desenhado para enfrentar. Testes automatizados (simulação controlada de
timeout/queda do LLM, cobertura completa de guardrails) ficam para a Etapa 5 do runbook.

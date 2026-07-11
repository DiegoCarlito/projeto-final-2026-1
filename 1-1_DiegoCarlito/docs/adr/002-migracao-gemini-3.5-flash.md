# ADR-002: Migração do LLM de produção de gemini-2.5-flash para gemini-3.5-flash (Solution C)

> **Data:** 11/07/2026
> **Status:** aceita

---

## Contexto

Em produção (deploy público no Render, `docs/evidence/11-deploy-render.md`), chamadas ao
`gemini-2.5-flash` passaram a devolver `404 NotFound`:

```
This model models/gemini-2.5-flash is no longer available to new users. Please update your
code to use a newer model for the latest features and improvements.
```

Confirmado (busca externa em 11/07/2026, threads no fórum oficial Google AI Developers) que
isso **não é uma restrição de conta nova**, apesar do texto do erro: a partir de 09/07/2026 o
Google começou a devolver 404 para `gemini-2.5-flash` **e também `gemini-2.5-flash-lite`** de
forma ampla, antes da data de desligamento oficialmente anunciada (16/10/2026). Trocar de
conta/chave da API não resolve — o modelo está indisponível para chamadas novas, não só para
contas recém-criadas.

Isso bloqueou a Solution C (única solução em produção, ver ADR-001) de gerar qualquer
explicação real via LLM — toda chamada cai em fallback determinístico, mesmo com o guardrail
funcionando exatamente como projetado.

---

## Alternativas consideradas

### Alternativa A: manter gemini-2.5-flash e trocar de conta/chave
- **Descrição:** gerar uma nova chave de API em outra conta Google, assumindo que fosse uma
  restrição por "conta nova".
- **Descartada:** os relatos do fórum oficial indicam que a indisponibilidade é do lado do
  modelo em si (rollout/bug antes do desligamento anunciado), não da conta — testado
  localmente e confirmado que mesmo a chave já em uso (não nova) também falha com 404 no
  momento da investigação.

### Alternativa B: aceitar o modo fallback permanente e documentar como limitação conhecida
- **Descrição:** não trocar nada, seguir demonstrando o produto só em modo de contingência.
- **Descartada:** a explicação gerada por LLM é um critério de aceitação do produto
  (`agent.md`, `docs/mission-brief.md`) — aceitar fallback permanente esconderia a capacidade
  central do agente sem necessidade, já que existe um substituto disponível e funcional.

### Alternativa C: migrar para gemini-3.5-flash
- **Descrição:** `gemini-3.5-flash` (GA desde 19/mai/2026) está disponível, sem data de
  desligamento anunciada, e é acessível com a mesma chave de API já em uso — sem trocar de
  provedor nem de SDK (`google-generativeai`, já usado por toda a stack).
- **Escolhida.**

---

## Decisão

Migrar `MODEL_NAME` em `solutions/solution-c/src/agent_c.py` de `"gemini-2.5-flash"` para
`"gemini-3.5-flash"`. Duas consequências técnicas descobertas e corrigidas durante a migração
(validadas com chamadas reais, não simuladas):

1. **Timeout do LLM (`LLM_TIMEOUT_SECONDS`):** medido empiricamente contra o `gemini-3.5-flash`
   com o prompt completo (dados do cliente + fatores SHAP + geração de JSON) — variação de
   ~11.7s a ~15.6s em 3 chamadas reais, contra ~1.5s-2.0s do `gemini-2.5-flash`. O valor
   antigo (8.0s) estourava sistematicamente. Ajustado para **20.0s**.
2. **Ambiguidade de escala no prompt:** `PROMPT_TEMPLATE` mostra a probabilidade ao modelo
   como percentual (`{probability:.2%}`, ex. `"46.06%"`) mas só instruía a devolver
   `"churn_probability"` como "float numérico", sem fixar a escala. O `gemini-2.5-flash`
   inferia a escala decimal (0–1) corretamente; o `gemini-3.5-flash` ecoou o valor no mesmo
   formato percentual mostrado (`46.06` em vez de `0.4606`), reprovado corretamente pelo
   guardrail de saída (`is_valid_llm_output`, que exige `0 <= churn_probability <= 1`) — o
   guardrail funcionou como projetado, mas o LLM nunca teria sucesso sem a correção. Regra 2
   do `PROMPT_TEMPLATE` foi reescrita para fixar explicitamente a escala decimal 0–1.

Após as duas correções, validado localmente com 3 chamadas reais consecutivas ao
`gemini-3.5-flash`: `llm_executed: true` nas 3, latência 11.7s–15.6s, JSON válido nas 3.

`solutions/solution-a` e `solutions/solution-b` **não** foram alteradas — permanecem
congeladas em `gemini-2.5-flash` como registro histórico do processo iterativo (decisão já
tomada em ADR-001: não mantidas em paridade de features com a C daqui para frente). Isso é
consistente mesmo sabendo que uma nova chamada a essas soluções também falharia hoje — elas
não são mais executadas em produção.

---

## Consequências

- `solutions/solution-c/src/agent_c.py`: `MODEL_NAME = "gemini-3.5-flash"`,
  `LLM_TIMEOUT_SECONDS = 20.0`, regra 2 do `PROMPT_TEMPLATE` fixando a escala decimal.
- A imagem publicada em `ghcr.io/diegocarlito/churn-solution-c` precisa de rebuild + push
  manual para que essa correção chegue ao deploy público no Render (mesma limitação já
  registrada em `docs/evidence/11-deploy-render.md` — sem CI/CD configurado).
- Latência de resposta ao usuário no painel aumenta (de ~2s-8s para até ~16s no caminho de
  sucesso do LLM) — aceitável para esta entrega acadêmica, mas relevante se este produto
  fosse evoluir além do curso.
- Se o Google reverter a indisponibilidade do `gemini-2.5-flash` antes de 16/10/2026, não há
  necessidade de reverter esta migração — `gemini-3.5-flash` é estritamente mais recente e
  sem desligamento anunciado.

---

## Referências

- `docs/adr/001-escolha-da-solucao.md` (Solution C como base de produção; A/B congeladas)
- `solutions/solution-c/src/agent_c.py`
- `agent.md` §7 (política de erro/fallback), §10 (escalonamento humano)
- Logs de produção do Render, 11/07/2026 (falha reportada pelo usuário, sem stack trace —
  motivou também a correção de logging em `app.py`, tratada separadamente)

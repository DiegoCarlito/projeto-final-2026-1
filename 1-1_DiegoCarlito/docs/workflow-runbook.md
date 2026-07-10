# Workflow Runbook

> **Projeto:** Previsão de Churn
> **Aluno(a):** Diego Carlito Rodrigues de Souza

---

## Processo obrigatório de execução

Siga as etapas abaixo na ordem indicada. Cada etapa deve gerar pelo menos um commit com mensagem descritiva e racionalidade.

### Etapa 1: Ler o Mission Brief
- [x] Ler e compreender o mission brief
- [x] Identificar entradas, saídas e restrições
- [x] Anotar dúvidas ou ambiguidades

### Etapa 2: Propor três soluções possíveis
- [x] **Descrever solution-a (baseline simples):** Pipeline composto por um modelo tabular interpretável (Regressão Logística). O agente utiliza o LLM apenas como um formatador de texto (prompt direto), passando a probabilidade e as features mais importantes baseadas nos coeficientes globais do modelo.
- [x] **Descrever solution-b (explicabilidade como ferramenta):** Agente que utiliza um modelo baseado em árvores (ex: Random Forest) e consulta uma ferramenta externa geradora de valores SHAP. A explicação do LLM é ancorada matematicamente no impacto local de cada variável para o cliente específico, evitando alucinações.
- [x] **Descrever solution-c (fluxo multi-etapa com guardrails):** Evolução da solution-b com foco em confiabilidade (Reliable). Inclui validação rigorosa de entrada (guardrails via Pydantic), política de fallback com respostas pré-determinadas caso o LLM falhe ou demore, e tratamento condicional para clientes na "zona cinzenta" (probabilidade entre 45% e 55%).

### Etapa 3: Registrar cada solução em pasta separada
- [x] Criar `solutions/solution-a/`
- [x] Criar `solutions/solution-b/`
- [x] Criar `solutions/solution-c/`

### Etapa 4: Implementar protótipos mínimos
- [x] Implementar protótipo da solution-a
- [x] Implementar protótipo da solution-b
- [x] Implementar protótipo da solution-c

### Etapa 5: Executar testes
- [x] Criar testes em `tests/`
- [x] Executar testes para cada solução
- [x] Registrar resultados em `docs/evidence/`

### Etapa 6: Comparar as soluções

| Critério | Solution A | Solution B | Solution C |
|----------|-----------|-----------|-----------|
| Custo | Mesmo custo de infra que B/C (Gemini 2.5 Flash free tier + modelo local). Menor custo de *desenvolvimento*: 4 arquivos, 4 testes. | Igual a A em infra. Custo de dev um pouco maior (SHAP tool + treino de Random Forest). | Igual a A/B em infra. Maior custo de dev (7 arquivos, 18 testes), mas parte já paga nesta sessão. |
| Complexidade | Baixa. Regressão Logística + prompt direto, sem ferramentas extras. | Média. Modelo não-linear + `ShapExplainer` como ferramenta consultada pelo agente. | Alta. Pipeline multi-etapa: classificação de zona de confiança, guardrail de saída, timeout, fallback determinístico por zona. |
| Qualidade da explicação | Baixa/média. Coeficientes **globais** do modelo — o LLM recebe "os fatores que mais pesam no modelo inteiro", não necessariamente os que pesam para *aquele* cliente. Risco de explicação genérica. | Alta. Valores SHAP **locais** — contribuição real e auditável de cada variável para o score daquele cliente específico (evidência: `docs/evidence/solution-b-validacao-09-07.md`). | Alta (herda o SHAP da B) + comunicação adaptada à incerteza: zona cinzenta gera explicação e ação diferentes de um caso de alta confiança. |
| Riscos | Recall de apenas 0.52 na classe Churn (deixa passar quase metade dos casos reais) — ver `docs/evidence/solution-a-validacao-09-07.md`. Sem guardrail de saída: um JSON malformado do LLM quebraria a resposta. Guardrail de entrada aceita qualquer string em campos categóricos (`OneHotEncoder` ignora em silêncio). | Recall de 0.78 (`class_weight="balanced"`). Mesma ausência de guardrail de saída e de entrada estrita que A — um LLM instável ainda pode gerar JSON malformado sem ser pego. | Mitiga os riscos de A/B: guardrail de saída rejeita JSON malformado/alucinado; guardrail de entrada rejeita categoria fora de escopo; timeout + fallback tratam indisponibilidade do LLM. Risco residual: mais superfície de código para manter; thresholds de zona cinzenta/escalonamento (`agent_c.py`) ainda não validados formalmente com o negócio. |
| Manutenibilidade | Alta a curto prazo (pouco código), mas frágil: qualquer mudança de comportamento do LLM (ex: retornar markdown) quebra sem aviso, e não há teste cobrindo isso além do fallback genérico. | Boa. Separação clara `model_wrapper` / `shap_tool` / `agent`, mas mesma fragilidade de A quanto a saída malformada. | Melhor a médio/longo prazo: 18 testes cobrindo os casos de borda (guardrails, zona cinzenta, escalonamento), módulos com responsabilidade única (`guardrails.py`, `fallback.py`). Custo: mais arquivos para entender antes de mexer. |
| Adequação ao problema | Atende ao mínimo (previsão + explicação + ação), mas não cobre os requisitos obrigatórios de **Reliable** do curso (guardrails de entrada/saída, fallback, degradação graciosa) além do básico. | Resolve bem a exigência de explicabilidade não-alucinada (mission-brief.md §7), mas ainda não cobre guardrails de saída nem zona cinzenta/escalonamento (agent.md §7, §9, §10). | É a única que atende à régua "Reliable" por completo: guardrail de entrada e saída, fallback testado com uma falha **real** de API (não simulada — ver `docs/evidence/solution-c-validacao-09-07.md`), zona cinzenta e escalonamento humano do `agent.md`. |

### Etapa 7: Escolher uma solução final
- [x] Solução escolhida: **Solution C**
- [x] Justificativa: é a única das três que atende à régua de saída obrigatória do curso na dimensão **Reliable** (guardrails de entrada e saída, fallback/degradação graciosa, sem erro técnico cru ao usuário) — não apenas em teoria: o fallback foi acionado por uma falha real da API do Gemini durante a validação desta sessão e respondeu corretamente as duas vezes. Herda o modelo com melhor recall (0.78 vs. 0.52 da A) e a explicação ancorada em SHAP local da B, então não perde nenhuma capacidade das soluções anteriores — só adiciona confiabilidade. O custo de complexidade adicional é compensado pela cobertura de testes (18 testes, a maior das três) que reduz o risco de regressão ao evoluir o código. Detalhamento completo em `docs/adr/001-escolha-da-solucao.md`.

### Etapa 8: Registrar a decisão em ADR
- [x] Criar `docs/adr/001-escolha-da-solucao.md`

### Etapa 9: Gerar o Merge-Readiness Pack
- [x] Preencher `docs/merge-readiness-pack.md`

### Etapa 10: Empacotar, integrar ao produto e escrever o relatório
- [x] Docker sobe com um comando (`GEMINI_API_KEY=... docker compose up --build`, testado com e sem chave)
- [x] API integrada a um produto/painel (`solutions/solution-c/static/index.html`, testado com Playwright)
- [ ] `report.md` completo — escrito por completo, exceto dois pontos que só o aluno pode preencher: link de deploy público e vídeo de demonstração
- [x] Verificar que cada etapa tem pelo menos um commit com racionalidade — auditoria completa em `docs/ai-workflow/session-log.md` (Sessão 3): todos os 10 itens da tabela têm commit correspondente; commits #1–#4 (04–05/07, anteriores a esta sessão) não têm racionalidade no corpo — aceito como registro histórico, sem reescrita de commits já publicados

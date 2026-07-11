# Merge-Readiness Pack

> **Projeto:** Previsão de Churn
> **Aluno(a):** Diego Carlito Rodrigues de Souza
> **Data:** 09/07/2026 (última revisão: 11/07/2026 — migração para gemini-3.5-flash, ver ADR-002)

---

## 1. Resumo da solução escolhida

**Solution C** — pipeline multi-etapa de previsão de churn: Random Forest (`class_weight="balanced"`)
para a probabilidade, `ShapExplainer` (SHAP local) para os fatores de risco reais daquele
cliente, e um agente orquestrador (`agent_c.py`) que classifica a zona de confiança do
cliente (padrão / zona cinzenta 0.45–0.55 / escalonamento de alto risco), chama o Gemini
3.5 Flash com timeout para traduzir os fatores SHAP em linguagem de negócio, valida a saída
do LLM (guardrail) e cai em um fallback determinístico específico por zona sempre que
qualquer etapa falha. Entrada validada por um schema Pydantic estrito (`guardrails.py`)
que rejeita não só tipos errados, mas também valores categóricos fora do escopo conhecido
do dataset Telco Customer Churn. Escolhida em `docs/adr/001-escolha-da-solucao.md` por ser
a única das três soluções que atende à régua "Reliable" do curso por completo.

---

## 2. Comparação entre as três alternativas

| Critério | Solution A | Solution B | Solution C |
|----------|-----------|-----------|-----------|
| **Abordagem** | Regressão Logística + LLM como formatador de coeficientes globais | Random Forest + SHAP local como ferramenta consultada pelo agente | Random Forest + SHAP local + guardrails de entrada/saída + zona cinzenta + fallback determinístico |
| **Custo** | Mesma infra (Gemini 2.5 Flash free tier); menor custo de desenvolvimento (4 arquivos, 4 testes) | Igual em infra; custo de dev um pouco maior (SHAP tool) | Igual em infra; maior custo de dev (7 arquivos, 18 testes), já pago nesta sessão |
| **Complexidade** | Baixa | Média | Alta |
| **Qualidade da explicação** | Baixa/média — coeficientes globais, risco de generalizar demais | Alta — SHAP local, ancorada no cliente específico | Alta (herda o SHAP da B) + comunicação adaptada à incerteza (zona cinzenta) |
| **Riscos** | Recall 0.52 na classe Churn; sem guardrail de saída; entrada aceita categoria fora de escopo | Recall 0.78; mesma ausência de guardrail de saída/entrada estrita que A | Riscos de A/B mitigados por guardrails; risco residual: threshold de "fatura alta" para escalonamento ainda não validado com o negócio |
| **Manutenibilidade** | Alta a curto prazo, frágil a mudanças de comportamento do LLM | Boa separação de responsabilidades, mesma fragilidade de saída que A | Melhor a médio prazo: 18 testes cobrindo casos de borda, módulos de responsabilidade única |
| **Adequação ao problema** | Atende ao mínimo, não cobre guardrails/fallback completos | Resolve explicabilidade não-alucinada, ainda sem guardrail de saída/zona cinzenta | Única que atende à régua "Reliable" por completo |

**Solução escolhida:** C

**Justificativa:** ver `docs/adr/001-escolha-da-solucao.md`. Em resumo: é a única alternativa
que implementa guardrails de entrada e saída, fallback testado contra uma falha **real**
(não simulada) da API do Gemini, tratamento explícito de incerteza (zona cinzenta) e
escalonamento humano — sem abrir mão do recall (0.78) e da explicação SHAP local herdados
da Solution B.

---

## 3. Testes executados

27 testes automatizados (pytest), 0 falhas. Detalhamento completo em
`docs/evidence/05-testes-automatizados.md`.

| Teste | Descrição | Resultado |
|-------|-----------|-----------|
| `solution-a/tests/test_solution_a.py` (4 testes) | Guardrail de entrada (campo faltando, tipo inválido), sucesso com LLM mockado, fallback sem vazar erro cru | Passou |
| `solution-b/tests/test_solution_b.py` (5 testes) | Os mesmos 4 casos de A + cobertura direta do `ShapExplainer` (fatores ordenados por impacto) | Passou |
| `solution-c/tests/test_solution_c.py` (18 testes) | Guardrail de entrada (incl. categoria fora de escopo), guardrail de saída (JSON malformado → fallback), zona cinzenta, escalonamento de alto risco (probabilidade sozinha não basta; escalonamento sobrepõe o LLM), fallback por zona | Passou |
| Validação manual ponta a ponta (as 3 soluções) | Treino real, servidor local, chamada real ao Gemini 2.5 Flash, guardrail de entrada via HTTP | Passou — `docs/evidence/04-solution-a-validacao.md`, `04-solution-b-validacao.md`, `04-solution-c-validacao.md` |

---

## 4. Evidências de funcionamento

Em `docs/evidence/`:

- `04-solution-a-validacao.md` — treino, servidor local, request/response real (LLM real, não fallback), guardrail de entrada.
- `04-solution-b-validacao.md` — idem, com explicação SHAP local real e comparação com A.
- `04-solution-c-validacao.md` — idem, incluindo um `DeadlineExceeded` **real** (504 do lado do Google) que acionou o fallback corretamente duas vezes, zona cinzenta validada com cliente real do dataset, e verificação direta da lógica de escalonamento (o dataset não atinge probabilidade > 95% com o modelo treinado).
- `05-testes-automatizados.md` — saída completa dos 27 testes automatizados.

---

## 5. Limitações conhecidas

- O threshold `HIGH_RISK_MONTHLY_CHARGES_THRESHOLD = 100.0` (`solutions/solution-c/src/agent_c.py`) é um valor placeholder para "fatura alta" (agent.md §10), ainda não validado formalmente com o negócio.
- Nenhum cliente do dataset Telco Customer Churn atinge probabilidade de churn > 95% com o modelo Random Forest treinado nesta sessão (máximo observado: ~0.926) — a regra de escalonamento de alto risco foi validada diretamente na lógica de decisão (testes unitários), não via uma requisição HTTP real com esse desfecho.
- O timeout do LLM (`LLM_TIMEOUT_SECONDS = 20.0`, ajustado na migração para `gemini-3.5-flash` — ver ADR-002) foi calibrado empiricamente contra a latência observada; latência da API do Gemini pode variar por região/carga/versão do modelo e merece revisão periódica.
- Testes automatizados mockam o LLM para determinismo; não há um teste automatizado que simule um timeout real de rede (a evidência de timeout real veio de uma falha genuína durante testes manuais, não de um teste de regressão repetível).
- O painel web (`solutions/solution-c/static/index.html`) é intencionalmente simples (HTML/JS estático, sem framework) — atende ao requisito de produto/interface, mas não é uma UI de produção completa (sem autenticação, sem histórico de consultas).
- `report.md` completo, incluindo link de deploy público e vídeo de demonstração (Etapa 10 do runbook concluída).

---

## 6. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Falsos positivos (sugerir desconto para cliente que não ia cancelar) | Média | Médio | `class_weight="balanced"` ajustado para recall; ação recomendada varia por zona de confiança em vez de ser sempre agressiva |
| Latência alta / falha na API do LLM | Alta (observada de verdade nesta sessão) | Alto | Timeout de 8s + fallback determinístico por zona, validado com uma falha real |
| Alucinação na explicação de risco | Média | Alto | Explicação ancorada em valores SHAP reais (não em texto livre do LLM); guardrail de saída rejeita JSON fora do formato/intervalo esperado |
| Threshold de escalonamento não validado com o negócio | Alta (é um placeholder) | Médio | Registrado explicitamente no ADR e aqui; não usar em produção real sem validação |

---

## 7. Decisões arquiteturais

- **ADR-001** (`docs/adr/001-escolha-da-solucao.md`): Solution C escolhida como solução final, por ser a única que atende à régua "Reliable" do curso por completo.

---

## 8. Instruções de execução

### Via Docker (recomendado — um comando, sobe API + painel)

```bash
# dataset não é versionado (licença Kaggle) — baixar antes, ver data/DATA_CARD.md
kaggle datasets download -d blastchar/telco-customer-churn -p data/ --unzip

GEMINI_API_KEY=sua_chave_aqui docker compose up --build
# painel: http://localhost:8000/  ·  docs interativos: http://localhost:8000/docs
```

Testado nesta sessão: build limpo, subida com chave real (LLM executando de verdade) e
subida sem chave (fallback ativado automaticamente, sem crash) — ver
`docs/evidence/10-docker-painel.md`.

### Local, sem Docker (desenvolvimento)

```bash
cd solutions/solution-c
python3 -m venv .venv && source .venv/bin/activate   # ou reutilize o .venv da raiz
pip install -r requirements.txt

cp .env.example .env   # preencha GEMINI_API_KEY (gerada em https://aistudio.google.com/)

python src/train.py                # gera src/model.joblib, não versionado
python -m pytest tests/ -v         # não depende de rede — LLM é mockado
uvicorn src.app:app --port 8000
```

---

## 9. Checklist de revisão

- [x] Mission brief atendido
- [x] Três soluções implementadas
- [x] Testes executados e documentados
- [x] Evidências registradas em `docs/evidence/`
- [x] ADR registrado em `docs/adr/`
- [x] Commits com mensagens claras e racionalidade
- [x] Código funcional em `src/` (de cada solução, em `solutions/solution-*/src/`)
- [x] Agent.md preenchido
- [x] Mentorship Pack preenchido
- [x] Workflow Runbook seguido (Etapas 1–10 concluídas nesta ordem)
- [x] Sistema deployable (Docker, roda com um comando — `GEMINI_API_KEY=... docker compose up --build`)
- [x] Sistema reliable (guardrails e fallback implementados e validados, inclusive contra uma falha real de API)

---

## 10. Justificativa para merge

As três soluções obrigatórias foram implementadas, treinadas com métricas honestas
(incluindo as que não favorecem a solução escolhida, como o recall mais baixo da A), testadas
automaticamente (27 testes, 0 falhas) e comparadas de forma objetiva em critérios definidos
antes da escolha (ADR-001). A solução final (C) foi validada não só em condições ideais, mas
também sob uma falha real e não planejada da dependência externa mais frágil do sistema (a
API do LLM), e respondeu exatamente como especificado em `agent.md`: sem expor erro técnico,
com fallback determinístico. As limitações conhecidas estão documentadas, não escondidas.
O sistema sobe com um único comando via Docker (build + treino + API + painel), com ou sem
a chave do Gemini configurada. A entrega está completa: `report.md` preenchido por inteiro
(link de deploy público, vídeo de demonstração), e a migração não planejada de
`gemini-2.5-flash` para `gemini-3.5-flash` em produção (`docs/adr/002-migracao-gemini-3.5-flash.md`)
foi absorvida sem alterar a arquitetura — só ajuste de timeout e de instrução de escala no
prompt — e validada de ponta a ponta, incluindo rebuild e novo push da imagem para
`ghcr.io/diegocarlito/churn-solution-c` (`docs/evidence/11-deploy-render.md` §6).

# ADR-001: Escolha da solução final

> **Data:** 09/07/2026
> **Status:** aceita

---

## Contexto

O projeto exige três abordagens distintas para o mesmo problema (previsão de churn com
explicação acionável), implementadas e validadas de forma independente em
`solutions/solution-a`, `solutions/solution-b` e `solutions/solution-c`, antes de escolher
qual delas segue para a integração final (API + produto + `report.md`).

A régua de saída do curso (`docs/ai-workflow/project-context.md` §3) exige que o sistema
final seja **Deployable** e, principalmente, **Reliable**: guardrails na entrada e na saída,
fallback/degradação graciosa quando o LLM falha ou demora, nunca expor erro técnico cru ao
usuário, e latência sob controle. Essa exigência pesa diretamente nesta decisão — não é só
"qual solução prevê melhor", é "qual solução está pronta para produção sem supervisão".

As três soluções foram implementadas, treinadas e validadas com chamadas reais à API do
Gemini 2.5 Flash (não simuladas) nesta sessão (09/07/2026), com evidências em
`docs/evidence/`, e cobertas por 27 testes automatizados (`docs/evidence/05-testes-automatizados.md`).

---

## Alternativas consideradas

### Alternativa A: solution-a
- **Descrição:** baseline. Regressão Logística (`class_weight` padrão) + LLM usado apenas
  como formatador de texto a partir dos coeficientes **globais** do modelo.
- **Prós:** menor superfície de código (4 arquivos, 4 testes), mais rápida de entender e
  de treinar, latência de inferência do modelo tabular desprezível.
- **Contras:** recall de apenas **0.52** na classe Churn (acurácia 0.7875, ROC-AUC 0.8319 —
  `docs/evidence/04-solution-a-validacao.md`) — deixa passar quase metade dos clientes
  que de fato cancelam. Explicação baseada em coeficientes globais, não no cliente
  específico — risco de o LLM generalizar demais. Sem guardrail de saída: uma resposta
  malformada do LLM não é detectada antes de chegar ao usuário. Guardrail de entrada aceita
  qualquer string nos campos categóricos.

### Alternativa B: solution-b
- **Descrição:** Random Forest (`class_weight="balanced"`) + `ShapExplainer`, uma
  ferramenta que o agente consulta para obter a contribuição matemática real (SHAP) de
  cada variável no score **daquele cliente específico**, antes de acionar o LLM.
- **Prós:** recall de **0.78** na classe Churn (ROC-AUC 0.8388 —
  `docs/evidence/04-solution-b-validacao.md`), bem acima de A. Explicação ancorada em
  evidência matemática local, reduzindo alucinação. Boa separação de responsabilidades
  (`model_wrapper.py` / `shap_tool.py` / `agent_b.py`).
- **Contras:** mesma ausência de guardrail de saída e de guardrail de entrada estrito que
  A — herda o mesmo ponto cego se o LLM devolver algo malformado ou se um valor
  categórico fora de escopo for enviado.

### Alternativa C: solution-c
- **Descrição:** herda o modelo e o `ShapExplainer` da B e encapsula tudo sob um pipeline
  multi-etapa: guardrail de entrada com `Literal` nos campos categóricos, classificação de
  zona de confiança (zona cinzenta 0.45–0.55, escalonamento de alto risco >95% + fatura
  alta), chamada ao LLM com timeout, guardrail de saída (`is_valid_llm_output`) e fallback
  determinístico específico por zona.
- **Prós:** é a única que implementa a régua "Reliable" por completo. Validada com uma
  falha **real** (não simulada) da API do Gemini durante esta sessão — `DeadlineExceeded`
  genuíno, tratado sem expor erro técnico ao usuário
  (`docs/evidence/04-solution-c-validacao.md`). Maior cobertura de testes das três (18,
  incluindo guardrail de saída, zona cinzenta e escalonamento). Não perde nenhuma
  capacidade de A/B — mesma qualidade de modelo e de explicação da B.
- **Contras:** maior superfície de código (7 arquivos) e mais conceitos para quem for dar
  manutenção entender de uma vez. O threshold de "fatura alta" para escalonamento
  (`HIGH_RISK_MONTHLY_CHARGES_THRESHOLD = 100.0` em `agent_c.py`) é um valor placeholder,
  ainda não validado formalmente com o negócio — risco residual registrado, não escondido.

---

## Decisão

**Solution C foi escolhida** para seguir para a integração final (API + produto).

Ela é a única alternativa que atende integralmente à régua de saída obrigatória do curso na
dimensão *Reliable*: guardrails de entrada e de saída, fallback testado contra uma falha real
de API (não um cenário simulado), tratamento explícito de incerteza (zona cinzenta) e
escalonamento humano (`agent.md` §10). Como herda o modelo (Random Forest, recall 0.78) e o
`ShapExplainer` da Solution B, a escolha não sacrifica capacidade preditiva nem qualidade de
explicação em troca de confiabilidade — soma as duas. O custo de complexidade adicional é
mitigado pela cobertura de testes (18 testes automatizados, a maior das três), que reduz o
risco de regressão silenciosa ao evoluir o código daqui para frente.

---

## Consequências

- `solutions/solution-c` passa a ser a base da API final exposta ao produto/painel
  (próximas etapas do runbook: merge-readiness pack e empacotamento).
- O threshold `HIGH_RISK_MONTHLY_CHARGES_THRESHOLD` precisa de validação de negócio antes
  de qualquer uso além deste projeto acadêmico — registrado como limitação conhecida,
  a repetir no `docs/merge-readiness-pack.md` e no `report.md`.
- Solutions A e B permanecem no repositório como registro do processo iterativo (exigido
  pelo curso: "o que NÃO funcionou também conta") — não serão apagadas nem mantidas em
  paridade de features com a C daqui para frente.
- Qualquer mudança futura nos thresholds de zona cinzenta/escalonamento ou no timeout do
  LLM (`agent_c.py`) deve vir acompanhada de atualização dos testes em
  `solutions/solution-c/tests/test_solution_c.py`, que hoje fixam esses valores como
  comportamento esperado.

---

## Referências

- `docs/evidence/04-solution-a-validacao.md`
- `docs/evidence/04-solution-b-validacao.md`
- `docs/evidence/04-solution-c-validacao.md`
- `docs/evidence/05-testes-automatizados.md`
- `docs/mission-brief.md` §7 (critérios de aceitação) e §8 (riscos)
- `agent.md` §7 (política de erro) e §10 (escalonamento humano)
- `docs/ai-workflow/project-context.md` §3 (régua de saída do curso)

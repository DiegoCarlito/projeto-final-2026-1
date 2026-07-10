# Contexto do Projeto

## 1. O que é este projeto

Projeto Final de uma disciplina de sistemas com agentes de IA. Ciclo completo exigido: **agente → API → produto**, no ar, até a entrega.

- **Trilha escolhida:** 1.1 — Previsão de Churn
- **Prazo de entrega:** 13/07/2026
- **Modalidade:** individual
- **Ferramentas:** Claude Code — única ferramenta de IA de desenvolvimento do projeto (especificação, arquitetura, geração de código, testes, execução e revisão). GitHub Copilot e o uso de chat do Gemini para desenvolvimento foram descontinuados. Não confundir com o Gemini 2.5 Flash: esse é usado via API pelo *produto* em runtime, não como ferramenta de desenvolvimento (ver seção 6).

## 2. O problema (Trilha 1.1)

Prever quais clientes têm alta probabilidade de cancelar o serviço (churn), para apoiar ações de retenção.

- Classificação binária, com classes desbalanceadas
- A métrica não pode ser só acurácia (precisão/recall/F1/AUC precisam entrar)
- A previsão precisa ser **interpretável**: mostrar por que aquele cliente está em risco, não só a probabilidade

**Dado:** Telco Customer Churn (IBM), ~7.043 clientes, 21 colunas, coluna alvo "Churn".
Link: https://www.kaggle.com/datasets/blastchar/telco-customer-churn

**Produto esperado:** Agente de IA que recebe o perfil do cliente, raciocina sobre os fatores de risco e devolve a probabilidade de churn com explicação, exposto como API e integrado a um painel ou interface conversacional de retenção.

## 3. Régua de saída do curso (não é opcional, vale nota)

O sistema final precisa ser:

### Deployable
- Empacotado (Docker), sobe com um comando
- Uma pessoa de fora consegue usar sem explicação
- Reproduzível: clone → comando → sistema no ar

### Reliable
- **Guardrails** na entrada (dado inválido, fora de escopo) e na saída (resposta sem sentido, alucinação, formato quebrado)
- **Fallback / degradação graciosa**: o que acontece se o LLM cair ou demorar demais
- Nunca mostrar erro técnico cru pro usuário
- Latência medida e sob controle

### O caminho de trabalho esperado
1. Enquadrar o problema (métrica de negócio + métrica técnica, stakeholders)
2. Preparar dados/contexto (origem, licença, vieses conhecidos)
3. Construir e iterar o agente a partir de um baseline simples, documentando decisões (o que NÃO funcionou também conta)
4. Avaliar de verdade (qualidade da resposta, latência, custo por chamada, taxa de fallback, casos extremos: entrada vazia, fora de escopo, jailbreak)
5. Colocar em produção (API + produto)
6. Monitorar (traces, custo, latência, taxa de fallback)

## 4. Framework de processo que vou seguir (Spec-Driven Development / Engenharia de Software Agêntica)

Este é o processo auditável que quero aplicar, com os artefatos abaixo. **Sua função é me ajudar a preencher e revisar cada um destes documentos antes de qualquer código ser escrito.**

- `agent.md` — como o agente (o sistema de churn) deve se comportar: papel, tom, ferramentas, restrições, formato de saída, critérios de parada, política de erro, como registrar decisões, como lidar com incerteza, quando escalar para humano.
- `docs/mission-brief.md` — contrato entre humano e agente: objetivo, problema, usuários-alvo, contexto de uso, entradas/saídas, limites, critérios de aceitação, riscos, evidências necessárias.
- `docs/mentorship-pack.md` — como "eu" (o desenvolvedor, apoiado por Copilot) devo trabalhar: julgamento, padrões de arquitetura, padrões de código, estilo de documentação, qualidade mínima aceitável, exemplos de boas/más decisões.
- `docs/workflow-runbook.md` — processo obrigatório de execução, etapa a etapa, cada etapa gerando pelo menos um commit com racionalidade registrada.
- `solutions/solution-a`, `solution-b`, `solution-c` — três abordagens diferentes para o mesmo problema (ver seção 8).
- `docs/adr/001-escolha-da-solucao.md` — decisão registrada: qual solução venceu e por quê.
- `docs/merge-readiness-pack.md` — evidências finais de que está pronto: comparação das 3 soluções, testes, evidências, limitações, riscos, decisões arquiteturais, instruções de execução, checklist.
- `report.md` — relatório final público exigido pelo curso (formato descrito na seção 9).

## 5. Arquitetura de arquivos/pastas do repositório

```
1-1_DiegoCarlito/
├── CLAUDE.md
├── agent.md
├── README.md
├── report.md
├── docs/
│   ├── mission-brief.md
│   ├── mentorship-pack.md
│   ├── workflow-runbook.md
│   ├── merge-readiness-pack.md
│   ├── adr/
│   │   └── 001-escolha-da-solucao.md
│   ├── evidence/
│   └── ai-workflow/
│       ├── project-context.md
│       └── session-log.md
├── solutions/
│   ├── solution-a/
│   ├── solution-b/
│   └── solution-c/
├── src/
│   ├── model/       # treino e artefato do modelo
│   ├── agent/        # wrapper de raciocínio/explicação
│   └── api/          # FastAPI
├── tests/
├── data/
│   └── DATA_CARD.md
├── docker/
│   └── Dockerfile
└── .vscode/
    └── extensions.json
```

Sempre que eu pedir para gerar um arquivo, use exatamente este caminho — não invente uma estrutura alternativa nem sugira renomear pastas sem eu pedir.

## 6. Stack técnica

- **Linguagem:** Python 3.11+
- **Modelo:** scikit-learn (regressão logística / RandomForest) ou XGBoost — escolher um e manter nas três soluções, salvo justificativa registrada em ADR
- **Explicabilidade:** SHAP (ou `feature_importances_` do modelo, se SHAP for pesado demais para o prazo)
- **LLM do produto (respostas do agente):** Gemini 2.5 Flash via API `google-generativeai` — fixo para as três soluções. É o modelo que o agente chama em runtime para gerar a explicação final ao usuário; não é a ferramenta de desenvolvimento (essa é o Claude Code, ver `CLAUDE.md` na raiz). Não trocar sem decisão registrada em ADR.
- **API:** FastAPI + Uvicorn
- **Validação de entrada:** Pydantic
- **Testes:** pytest
- **Formatter/linter:** black + ruff
- **Empacotamento:** Docker

Não introduza uma biblioteca ou framework fora desta lista sem antes perguntar e justificar — mesmo que pareça mais adequado para uma solução específica. Se genuinamente for necessário (ex: uma solução exige algo que as outras não precisam), registre isso como decisão explícita, não como escolha silenciosa.

## 7. Sequência de commits esperada

Cada commit deve conter, no corpo da mensagem, a racionalidade da decisão (o que foi decidido e por quê):

| # | Commit | Quando fazer |
|---|--------|--------------|
| 1 | Cria mission brief inicial | Ao terminar `docs/mission-brief.md` |
| 2 | Adiciona agent.md com regras de comportamento | Ao terminar `agent.md` |
| 3 | Cria mentorship pack e workflow runbook | Ao terminar os dois documentos |
| 4 | Implementa solution-a | Protótipo mínimo rodando (modelo + explicação simples) |
| 5 | Implementa solution-b | Protótipo com SHAP/explicabilidade como ferramenta |
| 6 | Implementa solution-c | Pipeline com guardrails + fallback funcionando |
| 7 | Adiciona testes e evidências | Testes passando + prints/logs em `docs/evidence/` |
| 8 | Registra ADR com comparação das soluções | Após comparar as 3 e decidir qual vai pra frente |
| 9 | Adiciona merge-readiness pack | Ao preencher o checklist final |
| 10 | Consolida solução final (API + Docker + report) | Sistema no ar, `report.md` completo |

Não precisa ser um commit só por item — pode quebrar em vários menores dentro da mesma etapa, mas cada etapa da lista acima precisa ter pelo menos um commit correspondente antes de avançar para a próxima.

## 8. As três soluções obrigatórias, adaptadas ao problema de churn

| Solução | Abordagem | Ideia para este projeto |
|---|---|---|
| **solution-a** | Simples, baseada em prompt/modelo direto | Modelo tabular simples (regressão logística ou árvore) + LLM só formata a explicação a partir das features mais importantes |
| **solution-b** | RAG / ferramenta externa / base de conhecimento | Modelo com SHAP (ou feature importance) como "ferramenta" que o agente consulta antes de responder — explicação baseada em valores reais de contribuição, não só no texto gerado |
| **solution-c** | Fluxo multi-etapa, validação ou agente com ferramentas | Pipeline com validação de entrada (guardrail), chamada ao modelo, chamada ao explicador, verificação de confiança (fallback se a probabilidade estiver na "zona cinzenta"), e só então resposta final |

Comparar as três em: custo, complexidade, qualidade da explicação, riscos, manutenibilidade, adequação ao problema — isso vira o ADR e parte do Merge-Readiness Pack.

## 9. Estrutura do relatório final (report.md)

Cabeçalho (link da app, link do repo) → Definição do problema (dor, stakeholders, métrica de negócio e técnica) → Como o sistema é montado (diagrama de arquitetura, exploração de agente/modelo, deployment, CI/CD) → Descrição do agente (modelo/ferramentas, dados/contexto, guardrails, iterações de prompt) → Avaliação do sistema (performance, UX) → Demonstração (vídeo) → Reflexão (o que funcionou/não funcionou, próximos passos) → Impactos e ética (viés entre grupos, privacidade) → Referências.

## 10. Seu papel (Claude Code)

As instruções de persona e de operação ficam no `CLAUDE.md` da raiz do repositório — carregado automaticamente pelo Claude Code em toda sessão, sem precisar colar nada. Este documento é a referência de contexto que o `CLAUDE.md` aponta para decisões de arquitetura, stack e estrutura. Sempre que eu pedir para revisar um artefato parcialmente preenchido, avalie contra os requisitos acima antes de aprovar. Sempre que eu pedir para "avançar de etapa", confirme que a etapa anterior está completa primeiro.
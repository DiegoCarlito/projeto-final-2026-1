# Previsão de Churn — Trilha 1.1

Agente de IA que recebe o perfil de um cliente de telecom, calcula a probabilidade de
cancelamento (churn), explica os fatores de risco reais daquele cliente e sugere uma ação
de retenção — exposto como API (FastAPI) com um painel web simples para a equipe de
Customer Success.

Projeto acadêmico (disciplina de sistemas com agentes de IA), desenvolvido seguindo
Spec-Driven Development. Veja `docs/ai-workflow/project-context.md` para o processo
completo e `docs/adr/001-escolha-da-solucao.md` para a decisão de arquitetura.

## Subir o sistema (um comando)

Pré-requisitos: Docker e Docker Compose. O dataset **não é versionado** por restrição de
licença do Kaggle — baixe antes de construir a imagem (ver `data/DATA_CARD.md`):

```bash
# 1. Baixar o dataset (uma vez só)
kaggle datasets download -d blastchar/telco-customer-churn -p data/ --unzip
mv data/WA_Fn-UseC_-Telco-Customer-Churn.csv data/telco_churn.csv   # se o nome vier diferente

# 2. Subir tudo (build + treino do modelo + API + painel)
GEMINI_API_KEY=sua_chave_aqui docker compose up --build
```

Painel: **http://localhost:8000/** · Documentação interativa da API: **http://localhost:8000/docs**

Sem `GEMINI_API_KEY`, o sistema ainda sobe e funciona — o agente responde em modo de
fallback (degradação graciosa), só sem a explicação gerada pelo Gemini 2.5 Flash. A chave é
gratuita em https://aistudio.google.com/.

## O que é cada coisa

- **`solutions/solution-c/`** — solução final escolhida (ver ADR-001), a que roda no Docker acima.
- **`solutions/solution-a/`** e **`solutions/solution-b/`** — as outras duas abordagens obrigatórias do curso, mantidas como registro do processo iterativo (não são a versão em produção).
- **`agent.md`** — como o agente deve se comportar (persona, ferramentas, guardrails, fallback).
- **`docs/mission-brief.md`** — contrato entre humano e agente.
- **`docs/adr/001-escolha-da-solucao.md`** — por que a Solution C foi escolhida.
- **`docs/merge-readiness-pack.md`** — evidências finais, testes, limitações conhecidas.
- **`docs/evidence/`** — logs reais de execução das três soluções e dos testes automatizados.
- **`report.md`** — relatório final do curso.

## Desenvolvimento local (sem Docker)

Ver "Instruções de execução" em `docs/merge-readiness-pack.md`.

## Stack

Python 3.12 · scikit-learn (Random Forest) · SHAP · FastAPI · Pydantic · pytest · Gemini
2.5 Flash · Docker. Detalhada em `docs/ai-workflow/project-context.md` §6.

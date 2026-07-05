# Framework de Soluções: Previsão de Churn e Retenção Automatizada

Este diretório contém a implementação modular do ecossistema de inteligência para retenção de clientes (Trilha 1.1), estruturado em três soluções incrementais que evoluem em complexidade, capacidade preditiva e resiliência operacional.

## Estrutura das Soluções

O ecossistema foi desenhado em uma arquitetura **Híbrida (Estatística/Determinística + Agentes de IA)** para garantir precisão matemática auditável, previsibilidade de custos de infraestrutura e uma camada de comunicação humanizada orientada a negócios.

### [Solution A: Baseline Tático](./solution-a/README.md)
- **Foco:** Predição estatística linear rápida e formatação de relatórios padronizados.
- **Tecnologia:** Regressão Logística (Scikit-Learn) + Gemini 2.5 Flash (Prompt Direto para formatação).

### [Solution B: Explicabilidade Avançada](./solution-b/README.md)
- **Foco:** Captura de relações não-lineares complexas e explicabilidade matemática local.
- **Tecnologia:** Random Forest/XGBoost + Ferramenta SHAP (Shapley Values) + Agente de IA orquestrador.

### [Solution C: Pipeline de Produção Confiável](./solution-c/README.md)
- **Foco:** Estabilidade em produção, segurança de dados, tratamento de incertezas e tolerância a falhas.
- **Tecnologia:** FastAPI + Guardrails de Entrada/Saída (Pydantic) + Mecanismo de Fallback local + Modelo SHAP.

## Fluxo Evolutivo e de Integração

1. A **Solution A** estabelece o marco zero do projeto (*baseline*), provando que o pipeline de dados funciona de ponta a ponta e que o LLM consegue traduzir os coeficientes globais do modelo em texto legível.
2. A **Solution B** desacopla a explicação de regras fixas globais, permitindo ao agente interagir com a ferramenta de cálculo SHAP para auditar matematicamente o score individual de *cada* cliente antes de formular a resposta.
3. A **Solution C** encapsula toda a inteligência preditiva e explicativa desenvolvida na etapa anterior sob barreiras de contenção operacionais (Guardrails), monitorando o status das dependências externas para acionar o protocolo de degradação graciosa (*Fallback*) se o LLM falhar.

## Estrutura Unificada de Pastas


```

solutions/
├── README.md
├── solution-a/             # Baseline: Regressão Logística + Prompt Direto
│   ├── README.md
│   ├── src/ (train.py, model_wrapper.py, agent_a.py, app.py)
│   └── tests/
├── solution-b/             # Avançado: Random Forest + Ferramenta SHAP
│   ├── README.md
│   ├── src/ (train.py, shap_tool.py, agent_b.py, app.py)
│   └── tests/
└── solution-c/             # Produção: Pipeline Resiliente com Guardrails & Fallback
├── README.md
├── src/ (train.py, shap_tool.py, guardrails.py, fallback.py, agent_c.py, app.py)
└── tests/

```

## Evidências e Testes

Cada subpasta de solução contém uma suíte de testes dedicada na pasta `tests/`. As evidências de execução com sucesso (logs de predição bem-sucedidos, ativações de guardrail e acionamentos simulados de fallback) são coletadas de forma auditável e documentadas no repositório geral em `docs/evidence/`.
# Diretrizes do projeto — Agente de Previsão de Churn

## Stack
- Python 3.11+
- Modelo: scikit-learn (regressão logística e/ou RandomForest) ou XGBoost
- API: FastAPI + Uvicorn
- Explicabilidade: SHAP (ou feature_importances_ do modelo, se SHAP for pesado demais)
- Testes: pytest
- Empacotamento: Docker

## Estrutura do projeto
- `src/model/` — treinamento, avaliação e serialização do modelo (joblib/pickle)
- `src/agent/` — camada de raciocínio: recebe a saída do modelo + explicabilidade e gera a resposta final (probabilidade + fatores de risco + ação sugerida)
- `src/api/` — endpoints FastAPI que expõem o agente
- `tests/` — testes unitários e de integração espelhando a estrutura de `src/`
- `data/` — nunca versionar CSVs aqui, só `DATA_CARD.md` (ver `.gitignore`)

## Seu papel neste projeto
O código-base principal (modelo, agente, API, testes) é gerado no Gemini Pro seguindo Clean Code e colado aqui. Seu papel é **completar, integrar e debugar** — não reescrever com um estilo diferente. Ao sugerir completions, siga o padrão já presente no arquivo em vez de introduzir convenções novas.

## Convenções de código
- Type hints obrigatórios em todas as funções públicas
- Nomes de função em português ou inglês, mas consistentes dentro do mesmo módulo (preferir inglês para código, português para docs/comentários de negócio)
- Formatter: black; linter: ruff
- Um teste por função de lógica de decisão relevante (não é preciso 100% de cobertura, mas o caminho de decisão do agente precisa estar coberto)
- **Clean Code, sempre:** funções pequenas e de responsabilidade única, nomes que revelam intenção, zero números/strings mágicos (usar constantes/config), tratamento de erro explícito (nunca `except: pass`), lógica de negócio separada de I/O
- Ao completar uma função existente, mantenha a mesma separação de camadas e nomenclatura já usada no arquivo

## Regras de negócio do agente (não mudar sem atualizar `agent.md`)
- A saída do agente sempre inclui: probabilidade de churn, os 3 principais fatores que contribuíram, e uma ação sugerida (ex: "baixo risco — nenhuma ação", "alto risco — acionar retenção")
- Nunca retornar só o número da probabilidade sem explicação — isso quebra o requisito de interpretabilidade do projeto
- Entradas inválidas (campos faltando, tipos errados) devem ser validadas antes de chegar ao modelo — usar Pydantic models na API para isso
- Se a confiança da previsão estiver numa faixa intermediária (ex: entre 0.4 e 0.6), sinalizar como "incerto" em vez de forçar uma classificação binária — ver política de fallback em `agent.md`

## O que evitar
- Não usar apenas acurácia como métrica de avaliação (classes desbalanceadas) — priorizar precisão/recall/F1/AUC
- Não hardcodar caminhos de arquivo — usar variáveis de ambiente ou config
- Não expor stack trace/erro técnico cru na resposta da API — sempre traduzir para uma mensagem de fallback amigável
# Previsão de Churn — Solution B: Explicabilidade Avançada (Random Forest + Ferramenta SHAP)

Este diretório contém a implementação da **Solution B**, que eleva o nível técnico do sistema ao substituir o modelo linear por um algoritmo não-linear baseado em árvores e introduzir uma ferramenta externa de explicabilidade matemática local (**SHAP — Shapley Additive exPlanations**). Aqui, o agente ganha a capacidade de consultar ferramentas antes de formular o seu raciocínio.

## Abordagem Arquitetural

Esta abordagem resolve a rigidez do baseline (Solution A) ao utilizar um modelo preditivo com maior capacidade de generalização e garantir que a explicação do LLM seja ancorada puramente em contribuições matemáticas exatas para *aquele* cliente específico, eliminando o risco de alucinações textuais sobre as causas do risco.

- **Foco:** Alta performance preditiva combinada com explicabilidade matemática local e auditável.
- **Modelo Tabular:** Random Forest (Scikit-Learn) ou XGBoost — captura relações não-lineares complexas e interações entre variáveis que a Regressão Logística ignora.
- **Camada de IA (Agente com Ferramentas):** O Agente de IA recebe os dados, mas não envia as informações diretamente ao LLM. Ele atua como um orquestrador que invoca ativamente uma ferramenta de cálculo de SHAP para extrair o impacto exato (positivo ou negativo) de cada variável no score final do cliente. O LLM atua na síntese de negócios a partir de evidências matemáticas estritas.

## Estrutura de Componentes

O código desta solução expande a modularidade para acomodar a ferramenta de explicabilidade local:


```

solutions/solution-b/
├── README.md
├── src/
│   ├── train.py          # Script de treino do modelo baseado em árvores (Random Forest)
│   ├── shap_tool.py      # Ferramenta externa que calcula os valores SHAP locais para o cliente
│   ├── agent_b.py        # Agente que orquestra a execução (chama predição -> consulta SHAP -> envia ao LLM)
│   └── app.py            # API FastAPI expondo o endpoint com suporte a ferramentas
└── tests/
└── test_solution_b.py # Testes de integração do fluxo do agente e validação da ferramenta SHAP

```

## Fluxo de Execução

1. A API (`app.py`) recebe as características do cliente via requisição POST.
2. O `agent_b.py` intercepta a entrada e aciona o modelo de Random Forest para extrair a probabilidade exata de churn.
3. O agente invoca a ferramenta interna `shap_tool.py`, passando a instância do cliente.
4. A `shap_tool.py` calcula os valores Shapley, isola as 3 variáveis que mais empurraram o score do cliente em direção ao Churn e devolve estes dados estruturados com os seus respetivos pesos estatísticos.
5. O agente monta o prompt injetando: as variáveis do cliente, a probabilidade calculada e os top 3 fatores extraídos matematicamente pelo SHAP.
6. O LLM traduz estes pesos exatos em uma narrativa comercial fluida e sugere a ação de retenção contextualizada.

## Formato do Payload (API)

### Entrada Esperada (`POST /api/v1/predict`)
*(Mesma estrutura de dados padronizada do dataset Telco Customer Churn)*

### Saída Gerada (Ancorada em Evidências SHAP)
```json
{
  "churn_probability": 0.7425,
  "risk_factors": [
    "O tempo de permanência de apenas 1 mês (tenure) foi o fator de maior peso matemático para o risco (+0.25 no score).",
    "A cobrança mensal elevada de 29.85 (MonthlyCharges) impactou negativamente a fidelização (+0.18 no score).",
    "A ausência do serviço de segurança online (OnlineSecurity=No) aumentou a vulnerabilidade do cliente (+0.12 no score)."
  ],
  "recommended_action": "Disparar uma campanha de onboarding prioritária para clientes novos, oferecendo ativação gratuita do módulo de Segurança Online por 6 meses e migração subsidiada para o plano semestral."
}

```

## Como Executar (Ambiente Local)

### 1. Instalar as dependências da Solution B (inclui a biblioteca shap)

```bash
pip install -r requirements.txt

```

### 2. Treinar o modelo Random Forest

```bash
python src/train.py

```

### 3. Iniciar a API FastAPI com suporte a explicabilidade local

```bash
uvicorn src.app:app --reload --port 8001

```
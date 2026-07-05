# Previsão de Churn — Solution A: Baseline Tático (Modelo Tabular + LLM Formatador)

Este diretório contém a implementação da **Solution A**, que serve como o baseline mínimo viável (MVP) do sistema de retenção de clientes. Ela adota uma abordagem híbrida simples, onde a inteligência preditiva é estritamente estatística e a IA atua puramente como uma camada de tradução e formatação textual.

## Abordagem Arquitetural

A solução foi desenhada para priorizar baixo custo de processamento de LLM, alta velocidade de resposta e interpretabilidade direta através de um modelo linear clássico.

- **Foco:** Predição estatística rápida e geração de relatórios de risco padronizados.
- **Modelo Tabular:** Regressão Logística (Scikit-Learn) — escolhida por ser inerentemente interpretável através de seus coeficientes globais.
- **Camada de IA:** LLM (Gemini Pro via API) atuando estritamente com **Prompt Direto**. O LLM não deduz o risco; ele recebe a probabilidade calculada e a lista de variáveis de maior peso matemático para formatar uma resposta humanizada e sugerir a ação de retenção.

## Estrutura de Componentes

O código desta solução está dividido seguindo o princípio de separação de responsabilidades (Clean Code):


```

solutions/solution-a/
├── README.md
├── src/
│   ├── train.py          # Script reprodutível de tratamento e treino do modelo estatístico
│   ├── model_wrapper.py  # Classe responsável por carregar o modelo e extrair a importância das colunas
│   ├── agent_a.py        # Orquestrador do agente (chama o modelo -> monta o prompt -> chama o LLM)
│   └── app.py            # API FastAPI expondo o endpoint de predição
└── tests/
└── test_solution_a.py # Testes unitários do fluxo crítico (sem mocks pesados)

```

## Fluxo de Execução

1. A API (`app.py`) recebe um payload contendo as características estruturadas do cliente.
2. O `model_wrapper.py` executa o `.predict_proba()` usando a Regressão Logística treinada.
3. O wrapper intercepta os coeficientes globais do modelo e identifica quais das características daquele cliente possuem o maior peso estatístico para a decisão de Churn.
4. O `agent_a.py` injeta estes dados estruturados em um prompt rígido de *In-Context Learning*.
5. O LLM recebe o prompt estruturado e devolve um payload formatado em JSON contendo a probabilidade exata, a explicação traduzida e a ação sugerida.

## Formato do Payload (API)

### Entrada Esperada (`POST /api/v1/predict`)
```json
{
  "gender": "Female",
  "SeniorCitizen": 0,
  "Partner": "Yes",
  "Dependents": "No",
  "tenure": 1,
  "PhoneService": "No",
  "MultipleLines": "No phone service",
  "InternetService": "DSL",
  "OnlineSecurity": "No",
  "OnlineBackup": "Yes",
  "DeviceProtection": "No",
  "TechSupport": "No",
  "StreamingTV": "No",
  "StreamingMovies": "No",
  "Contract": "Month-to-month",
  "PaperlessBilling": "Yes",
  "PaymentMethod": "Electronic check",
  "MonthlyCharges": 29.85,
  "TotalCharges": 29.85
}

```

### Saída Gerada

```json
{
  "churn_probability": 0.6842,
  "risk_factors": [
    "O contrato mês a mês (Month-to-month) reduz a barreira de saída do cliente.",
    "A falta de suporte técnico (TechSupport) contratado eleva o risco de abandono.",
    "O método de pagamento por boleto eletrônico (Electronic check) possui historicamente maior taxa de cancelamento."
  ],
  "recommended_action": "Oferecer transição imediata para o contrato anual com desconto de 15% na mensalidade e inclusão de suporte técnico gratuito por 3 meses."
}

```

## Como Executar (Ambiente Local)

### 1. Instalar as dependências da Solution A

```bash
pip install -r requirements.txt

```

### 2. Treinar o modelo baseline

```bash
python src/train.py

```

### 3. Iniciar a API FastAPI

```bash
uvicorn src.app:app --reload --port 8000

```
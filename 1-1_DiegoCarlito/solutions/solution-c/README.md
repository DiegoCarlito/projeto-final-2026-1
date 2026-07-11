# Previsão de Churn — Solution C: Pipeline de Produção Confiável (Multi-Etapa, Guardrails e Fallback)

Este diretório contém a implementação da **Solution C**, a versão mais robusta e resiliente do sistema (alinhada com a régua de saída *Reliable* do curso). Esta solução envolve um pipeline de execução multi-etapa que encapsula o modelo não-linear e a ferramenta SHAP da Solution B sob camadas estritas de segurança, validação de dados e políticas automáticas de contingência (*degradação graciosa*).

## Abordagem Arquitetural

O foco desta abordagem não é apenas a precisão matemática, mas a estabilidade operacional no mundo real, garantindo que o sistema seja tolerante a falhas de rede, indisponibilidade de APIs externas de LLM e tentativas de inputs maliciosos.

- **Foco:** Confiabilidade pontual, segurança (Guardrails), tratamento de incerteza operacional e resiliência (Fallback).
- **Modelo Tabular:** Random Forest ou XGBoost (Herdado da Solution B).
- **Mecanismo de Confiabilidade:** - **Guardrail de Entrada:** Validação de esquema, tipos e limites através do **Pydantic**. Entrada fora do escopo ou incompleta é rejeitada imediatamente na camada HTTP antes de consumir processamento.
  - **Guardrail de Saída:** Filtros pós-geração do LLM para garantir que a resposta retorne estritamente em formato JSON estruturado e sem alucinações técnicas brutas.
  - **Tratamento de Incerteza (Zona Cinzenta):** Clientes com score de churn marginal (entre 45% e 55%) acionam um fluxo alternativo de recomendação focado em análise preventiva leve, sinalizando a incerteza estatística.
  - **Degradação Graciosa (Fallback):** Se a API do LLM estiver fora do ar ou ultrapassar o timeout limite de latência estabelecido, o sistema intercepta a falha de forma transparente, consome um dicionário estático local e preenche a resposta com base nas diretrizes matemáticas do SHAP, nunca mostrando um erro bruto ou stack trace ao utilizador.

## Estrutura de Componentes

O código desta solução adiciona módulos específicos para governar o fluxo e tratar as exceções:


```

solutions/solution-c/
├── README.md
├── src/
│   ├── train.py          # Script de treino (geração do modelo não-linear)
│   ├── shap_tool.py      # Ferramenta de explicabilidade matemática local
│   ├── guardrails.py     # Esquemas Pydantic e lógica de validação de Entrada/Saída
│   ├── fallback.py       # Mecanismo de contingência (geração estática de segurança se LLM cair)
│   ├── agent_c.py        # Agente multi-etapas que valida, prevê, avalia a zona cinzenta e orquestra a resiliência
│   └── app.py            # API FastAPI com timeouts estritos, tratamento de erros global e logs detalhados
└── tests/
└── test_solution_c.py # Testes intensivos: validação de payloads inválidos, simulação de queda do LLM e tempo limite

```

## Fluxo de Execução Multi-Etapa

1. A API (`app.py`) recebe as características do cliente e o **Guardrail de Entrada** (`guardrails.py`) valida os limites e tipos de dados via Pydantic.
2. O modelo tabular processa a probabilidade.
3. O sistema avalia se a probabilidade está na **Zona Cinzenta (45% - 55%)**. Se sim, anexa uma flag de incerteza.
4. A ferramenta SHAP calcula as variáveis determinantes.
5. O agente tenta invocar o LLM para humanizar o relatório com um timeout (20.0s — valor medido empiricamente contra a latência real do Gemini 3.5 Flash, ver `docs/evidence/` e `docs/adr/002-migracao-gemini-3.5-flash.md`).
6. **Cenário de Sucesso (LLM Online):** O LLM responde, o **Guardrail de Saída** valida a estrutura do JSON e o entrega ao utilizador.
7. **Cenário de Contingência (LLM Offline/Timeout):** O módulo `fallback.py` captura a exceção, consome a saída bruta do SHAP e monta as justificações através de mapeamentos de texto locais pré-determinados, entregando a resposta no formato esperado sem que o utilizador note a falha de terceiros.

## Formato do Payload (API)

### Entrada Esperada (`POST /api/v1/predict`)
*(Mesma estrutura padronizada para manter a compatibilidade entre as soluções)*

### Saída Gerada com Sucesso (LLM Ativo)
```json
{
  "churn_probability": 0.5210,
  "risk_factors": [
    "O contrato mês a mês empurra o risco positivamente (+0.22 no score).",
    "Fatura mensal elevada atua como fator desestabilizador (+0.14 no score)."
  ],
  "recommended_action": "Contacto preventivo de relacionamento: Enviar sondagem de satisfação sem oferta agressiva devido à probabilidade marginal.",
  "system_status": {
    "llm_executed": true,
    "confidence_zone": "marginal"
  }
}

```

### Saída de Contingência (LLM Indisponível - Fallback Ativado)

```json
{
  "churn_probability": 0.7425,
  "risk_factors": [
    "Indicador crítico detetado na variável: tenure (tempo de contrato curto).",
    "Indicador crítico detetado na variável: MonthlyCharges (custo mensal elevado)."
  ],
  "recommended_action": "Aplicar protocolo padrão de retenção: Oferecer migração para o plano anual com suporte técnico estendido.",
  "system_status": {
    "llm_executed": false,
    "confidence_zone": "high_risk_fallback"
  }
}

```

## Como Executar (Ambiente Local)

### 1. Instalar as dependências da Solution C

```bash
pip install -r requirements.txt

```

### 2. Executar a bateria completa de testes de resiliência

```bash
pytest tests/test_solution_c.py -v

```

### 3. Iniciar a API em modo seguro de produção

```bash
uvicorn src.app:app --reload --port 8002

```
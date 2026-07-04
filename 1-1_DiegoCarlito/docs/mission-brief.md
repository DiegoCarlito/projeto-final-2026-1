# Mission Brief

> **Aluno(a):** Diego Carlito Rodrigues de Souza
> **Trilha:** 1.1 — Previsão de Churn

---

## 1. Objetivo do agente

Analisar o perfil e o histórico de um cliente, calcular a probabilidade dele cancelar o serviço (churn), explicar os fatores de risco determinantes e sugerir uma ação de retenção acionável.

---

## 2. Problema que ele resolve

A perda de clientes (churn) impacta diretamente a receita da empresa de telecomunicações. Modelos tradicionais apenas dizem *quem* vai cancelar, mas a equipe de negócios precisa saber *por que* o cliente está em risco para oferecer a intervenção correta (ex: desconto, suporte técnico, upgrade de plano). O agente preenche essa lacuna unindo previsão estatística com explicabilidade textual.

---

## 3. Usuários-alvo

Equipe de retenção de clientes e analistas de atendimento (Customer Success).

---

## 4. Contexto de uso

O agente será exposto como uma API. Ele será consultado de forma assíncrona (batch diário) ou em tempo real quando um analista de retenção abrir o perfil de um cliente em risco no painel de atendimento para decidir qual oferta fazer.

---

## 5. Entradas e saídas esperadas

| Item | Descrição |
|------|-----------|
| **Entrada** | Dados demográficos, informações da conta e serviços contratados de um cliente. |
| **Formato da entrada** | Objeto JSON com as features do dataset Telco Customer Churn. |
| **Saída** | Probabilidade de churn, fatores de risco e sugestão de ação. |
| **Formato da saída** | Objeto JSON contendo: `churn_probability` (float), `risk_factors` (lista de strings), `recommended_action` (string). |

---

## 6. Limites do agente

### O que o agente faz:
- Calcula a probabilidade de churn com base em um modelo tabular (ex: Regressão Logística, Random Forest ou XGBoost).
- Traduz a importância das variáveis (ex: via SHAP ou coeficientes) em texto compreensível.
- Sugere uma ação de retenção baseada no fator de risco primário.

### O que o agente NÃO deve fazer:
- Não executa ações automaticamente (ex: não aplica descontos direto na conta, não envia e-mails).
- Não retreina o modelo dinamicamente.
- Não lida com clientes fora da base de dados fornecida.

---

## 7. Critérios de aceitação

- [ ] O sistema deve receber um payload JSON na API e retornar um JSON com probabilidade, explicação e ação recomendada.
- [ ] A explicação deve ser baseada nos dados reais do cliente, sem alucinações.
- [ ] O sistema deve possuir guardrails para rejeitar payloads com tipos de dados inválidos ou colunas faltantes.
- [ ] O sistema deve ter um fallback configurado (se o LLM falhar, a API retorna apenas a probabilidade e uma explicação genérica predefinida).

---

## 8. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Falsos positivos (sugerir desconto para cliente que não ia cancelar) | Média | Médio | Limiar de decisão bem ajustado (trade-off precisão/recall) focado em evitar perda de margem desnecessária. |
| Latência alta / Falha na API do LLM | Alta | Alto | Implementar degradação graciosa (fallback); modelo estatístico roda local/rápido, a explicação textual cai se o LLM falhar. |
| Alucinação na explicação de risco | Média | Alto | Usar features tabulares reais como input estrito para o LLM via in-context learning. O LLM apenas formata, não deduz. |

---

## 9. Evidências necessárias

- [ ] Logs de requisições mostrando o payload de entrada, saída do modelo tabular e saída formatada pelo LLM.
- [ ] Bateria de testes unitários validando o fallback e os guardrails de entrada.
- [ ] Imagem Docker da API rodando com sucesso.
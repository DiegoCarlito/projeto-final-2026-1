# Data Card — Telco Customer Churn

## Origem
- **Fonte:** Kaggle — Telco Customer Churn (IBM)
- **Link:** https://www.kaggle.com/datasets/blastchar/telco-customer-churn
- **Origem original:** adaptado dos IBM Cognos Analytics base samples (dados fictícios de uma empresa de telecom fictícia)

## Licença
- Declarada no Kaggle como "Data files © Original Authors" — **não é uma licença aberta padrão** (não é CC0, CC BY, MIT, etc.).
- Como o texto da licença é vago e não define explicitamente os termos de redistribuição, o dataset **não é versionado no repositório**. Apenas este Data Card é público; o arquivo original deve ser baixado individualmente por quem for rodar o projeto.
- Uso neste projeto: educacional, para fins de disciplina acadêmica, sem fins comerciais e sem redistribuição do arquivo bruto.

## Descrição
- ~7.043 clientes, 21 colunas
- Dados fictícios (empresa e clientes fictícios, não é dado real de pessoas)
- Coluna alvo: `Churn` (Yes/No)
- Principais grupos de colunas: dados demográficos (gênero, idosos, dependentes), conta (tempo de contrato, forma de pagamento, cobrança), serviços contratados (internet, streaming, suporte técnico)

## Como obter
```bash
# via Kaggle CLI (requer conta e API key configurada)
kaggle datasets download -d blastchar/telco-customer-churn -p data/ --unzip
```
Ou baixar manualmente pelo link acima e salvar em `data/telco_churn.csv` (arquivo ignorado pelo git).

## Vieses e limitações conhecidos
- Dados sintéticos/fictícios: podem não refletir padrões reais de comportamento de clientes com a mesma fidelidade de um dataset de produção.
- Classes desbalanceadas: a proporção de clientes que cancelam é minoria — não usar apenas acurácia como métrica.
- Snapshot único (um trimestre): não captura sazonalidade nem mudanças de comportamento ao longo do tempo.
- Sem dados de localização/geografia real (é uma empresa fictícia na Califórnia, genérica).

## Uso neste projeto
Treinamento de modelo de classificação binária (churn/não-churn) e geração de explicações sobre os fatores de risco por cliente, consumido pelo agente descrito em `agent.md`.
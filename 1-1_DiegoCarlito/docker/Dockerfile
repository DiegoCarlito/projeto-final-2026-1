# Imagem da solução final (Solution C) — API de previsão de churn + painel estático.
#
# O dataset (data/telco_churn.csv) não é versionado no git por restrição de licença do
# Kaggle (ver data/DATA_CARD.md) — precisa existir localmente ANTES do build, baixado
# manualmente ou via `kaggle datasets download`. O contexto de build é a raiz do
# repositório (ver docker-compose.yml / instruções em docs/merge-readiness-pack.md).
# shap==0.52.0 (fixado em requirements.txt) exige Python 3.12+; a mesma versão usada no
# desenvolvimento/validação local desta sessão.
FROM python:3.12-slim

WORKDIR /app

# Instala as dependências primeiro para aproveitar o cache de camadas do Docker.
COPY solutions/solution-c/requirements.txt solutions/solution-c/requirements.txt
RUN pip install --no-cache-dir -r solutions/solution-c/requirements.txt

# Copia o dataset e o código da Solution C, espelhando o mesmo caminho relativo usado
# em desenvolvimento local (solutions/solution-c/src/train.py::DATA_PATH depende disso).
COPY data/telco_churn.csv data/telco_churn.csv
COPY solutions/solution-c/ solutions/solution-c/

WORKDIR /app/solutions/solution-c

# Treina o modelo durante o build — gera src/model.joblib dentro da imagem, sem depender
# de volume montado em runtime nem de rebaixar/redistribuir o CSV bruto do dataset.
RUN python src/train.py

EXPOSE 8000

# GEMINI_API_KEY é passada em runtime (docker run -e / docker-compose), nunca embutida
# na imagem. Sem ela, o agente ainda sobe e responde em modo de fallback (agent.md §7).
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]

import logging
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from .agent_c import ChurnAgentC
from .guardrails import CustomerPayload

STATIC_FILES_DIR = "static"

logger = logging.getLogger("solution_c")

app = FastAPI(title="Previsão de Churn - Solution C", version="1.0.0")

agent = None


@app.on_event("startup")
def load_agent():
    global agent
    try:
        agent = ChurnAgentC()
    except Exception as e:
        print(f"Aviso Crítico na Inicialização: {e}")


@app.post("/api/v1/predict")
async def predict_churn(payload: CustomerPayload):
    if not agent:
        raise HTTPException(status_code=503, detail="Modelo preditivo não carregado ou indisponível.")

    try:
        data_dict = payload.model_dump()
        result = agent.analyze(data_dict)
        return result
    except Exception:
        # Não vazar stack trace cru para o cliente, mas registrar nos logs do servidor
        # para permitir diagnóstico — antes disso a causa real ficava invisível.
        logger.error("Falha ao processar /api/v1/predict:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Erro interno no processamento do perfil de risco.")


# Montado por último: serve o painel estático (index.html) em "/", sem interferir nas
# rotas de API já registradas acima.
app.mount("/", StaticFiles(directory=STATIC_FILES_DIR, html=True), name="painel")

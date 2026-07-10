from fastapi import FastAPI, HTTPException
from .agent_c import ChurnAgentC
from .guardrails import CustomerPayload

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
    except Exception as e:
        # Não vazar stack trace cru, registrar e devolver erro amigável
        raise HTTPException(status_code=500, detail="Erro interno no processamento do perfil de risco.")

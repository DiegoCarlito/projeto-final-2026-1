from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .agent_a import ChurnAgentA

app = FastAPI(title="Previsão de Churn - Solution A", version="1.0.0")

# O esquema é flexível na Solution A (aceita dict direto ou kwargs), 
# mas usamos um tipo mínimo para a documentação do Swagger.
class CustomerPayload(BaseModel):
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str
    tenure: int
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float
    TotalCharges: str # Pode vir em string devido à formatação do dataset

agent = None

@app.on_event("startup")
def load_agent():
    global agent
    try:
        agent = ChurnAgentA()
    except Exception as e:
        print(f"Aviso Crítico na Inicialização: {e}")

@app.post("/api/v1/predict")
async def predict_churn(payload: CustomerPayload):
    if not agent:
        raise HTTPException(status_code=503, detail="Modelo preditivo não carregado ou indisponível.")
    
    try:
        # Converter payload para dicionário e acionar o Agente
        data_dict = payload.model_dump()
        result = agent.analyze(data_dict)
        return result
    except Exception as e:
        # Não vazar stack trace cru, registrar e devolver erro amigável
        raise HTTPException(status_code=500, detail="Erro interno no processamento do perfil de risco.")

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .model_wrapper import BaselineModelWrapper

load_dotenv()

# Configurar chave da API via variável de ambiente
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("GEMINI_API_KEY não encontrada.")

# Constantes do Agente
MODEL_NAME = "gemini-2.5-flash"
PROMPT_TEMPLATE = """
Você é um Analista Assistente de Retenção de Clientes.
Sua tarefa é ler os dados do cliente, a probabilidade estatística de cancelamento (churn) e os fatores matemáticos de risco identificados pelo modelo base, e gerar um relatório JSON formatado para a equipe de atendimento.

DADOS DO CLIENTE:
{customer_data}

PROBABILIDADE CALCULADA DE CHURN: {probability:.2%}

PRINCIPAIS VARIÁVEIS DE RISCO ESTATÍSTICO (Coeficientes Positivos):
{top_factors}

Regras estritas de saída:
1. Responda APENAS com um objeto JSON válido, sem markdown, sem blocos ```json.
2. O JSON deve ter exatamente estas chaves: "churn_probability" (float numérico), "risk_factors" (lista de 2 a 3 strings explicando os riscos com base nas variáveis informadas), "recommended_action" (string com a ação de retenção sugerida).
3. Seja objetivo e não use jargões de machine learning na explicação.
"""

class ChurnAgentA:
    def __init__(self):
        self.model_wrapper = BaselineModelWrapper()
        
        if not GEMINI_API_KEY:
            # Degradação Graciosa Básica se a API Key não existir
            self.llm = None
        else:
            self.llm = genai.GenerativeModel(MODEL_NAME)

    def analyze(self, customer_data: dict) -> dict:
        try:
            # 1. Chamar o modelo tabular
            probability, top_factors = self.model_wrapper.predict_with_factors(customer_data)
            
            # 2. Fallback caso não haja LLM configurado
            if not self.llm:
                return self._generate_fallback(probability, top_factors)
                
            # 3. Formatar o Prompt para o Gemini 2.5 Flash
            prompt = PROMPT_TEMPLATE.format(
                customer_data=json.dumps(customer_data, indent=2),
                probability=probability,
                top_factors=", ".join(top_factors)
            )
            
            # 4. Chamar LLM
            response = self.llm.generate_content(prompt)
            
            # 5. Fazer parse do JSON retornado
            result_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(result_text)
            
        except Exception as e:
            # Em caso de qualquer erro na API do Google ou no parse, aplicar Fallback
            print(f"Erro no Agente LLM: {str(e)}. Acionando fallback.")
            # Se o erro for antes de calcular a probabilidade, o app.py deve tratar com HTTP 500
            if 'probability' in locals():
                 return self._generate_fallback(probability, top_factors)
            raise e

    def _generate_fallback(self, probability: float, top_factors: list) -> dict:
        """Gera resposta padronizada sem necessitar do LLM."""
        return {
            "churn_probability": round(probability, 4),
            "risk_factors": [f"Variável crítica identificada globalmente: {factor}" for factor in top_factors[:2]],
            "recommended_action": "Analisar perfil do cliente no painel para ação manual de retenção (Resposta de Fallback)."
        }

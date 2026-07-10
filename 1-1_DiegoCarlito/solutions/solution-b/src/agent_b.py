import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .model_wrapper import RandomForestModelWrapper
from .shap_tool import ShapExplainer

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
Sua tarefa é ler os dados do cliente, a probabilidade estatística de cancelamento (churn) e os
fatores de risco extraídos matematicamente via SHAP (a contribuição real de cada variável para
o score deste cliente específico), e gerar um relatório JSON formatado para a equipe de
atendimento.

DADOS DO CLIENTE:
{customer_data}

PROBABILIDADE CALCULADA DE CHURN: {probability:.2%}

FATORES DE RISCO (valores SHAP locais — contribuição exata de cada variável para o score
deste cliente, do maior para o menor impacto):
{shap_factors}

Regras estritas de saída:
1. Responda APENAS com um objeto JSON válido, sem markdown, sem blocos ```json.
2. O JSON deve ter exatamente estas chaves: "churn_probability" (float numérico),
   "risk_factors" (lista de 2 a 3 strings traduzindo os fatores SHAP acima em linguagem de
   negócio, sem citar "SHAP" ou jargão técnico), "recommended_action" (string com a ação de
   retenção sugerida).
3. Baseie-se exclusivamente nos fatores SHAP fornecidos — não invente outras causas.
"""


class ChurnAgentB:
    def __init__(self):
        self.model_wrapper = RandomForestModelWrapper()
        self.shap_explainer = ShapExplainer(self.model_wrapper)

        if not GEMINI_API_KEY:
            # Degradação Graciosa Básica se a API Key não existir
            self.llm = None
        else:
            self.llm = genai.GenerativeModel(MODEL_NAME)

    def analyze(self, customer_data: dict) -> dict:
        try:
            # 1. Chamar o modelo tabular (Random Forest)
            probability = self.model_wrapper.predict_probability(customer_data)

            # 2. Consultar a ferramenta de explicabilidade (SHAP local)
            top_factors = self.shap_explainer.get_top_risk_factors(customer_data)

            # 3. Fallback caso não haja LLM configurado
            if not self.llm:
                return self._generate_fallback(probability, top_factors)

            # 4. Formatar o Prompt para o Gemini 2.5 Flash com evidências SHAP
            prompt = PROMPT_TEMPLATE.format(
                customer_data=json.dumps(customer_data, indent=2),
                probability=probability,
                shap_factors=self._format_shap_factors(top_factors),
            )

            # 5. Chamar LLM
            response = self.llm.generate_content(prompt)

            # 6. Fazer parse do JSON retornado
            result_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(result_text)

        except Exception as e:
            # Em caso de qualquer erro na API do Google, no parse ou no cálculo SHAP, aplicar Fallback
            print(f"Erro no Agente LLM: {str(e)}. Acionando fallback.")
            if "probability" in locals() and "top_factors" in locals():
                return self._generate_fallback(probability, top_factors)
            raise e

    def _format_shap_factors(self, top_factors: list[dict]) -> str:
        """Formata os fatores SHAP como uma lista legível para o prompt."""
        return "\n".join(
            f"- {factor['feature']}: impacto de {factor['shap_value']:+.4f} no score de churn"
            for factor in top_factors
        )

    def _generate_fallback(self, probability: float, top_factors: list[dict]) -> dict:
        """Gera resposta padronizada sem necessitar do LLM, citando as variáveis SHAP brutas."""
        return {
            "churn_probability": round(probability, 4),
            "risk_factors": [
                f"Variável com maior impacto matemático no risco: {factor['feature']} "
                f"(peso {factor['shap_value']:+.4f})"
                for factor in top_factors[:2]
            ],
            "recommended_action": "Analisar perfil do cliente no painel para ação manual de retenção (Resposta de Fallback).",
        }

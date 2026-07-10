import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .model_wrapper import RandomForestModelWrapper
from .shap_tool import ShapExplainer
from .guardrails import is_valid_llm_output
from .fallback import generate_fallback_response

load_dotenv()

# Configurar chave da API via variável de ambiente
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("GEMINI_API_KEY não encontrada.")

# Constantes do Agente
MODEL_NAME = "gemini-2.5-flash"
# Medido empiricamente: uma chamada simples ao Gemini 2.5 Flash já leva ~1.5s; com o
# prompt completo (dados do cliente + fatores SHAP + geração de JSON) 2.0s (sugestão
# inicial do README) estourava quase sempre. 8.0s é "agressivo" o suficiente para não
# deixar o usuário esperando indefinidamente, mas realista para o caminho de sucesso.
LLM_TIMEOUT_SECONDS = 8.0

# Zona cinzenta: probabilidade marginal, sem indícios estatísticos fortes o suficiente
# para justificar uma oferta agressiva de retenção (agent.md §7 e §9).
GRAY_ZONE_LOWER_BOUND = 0.45
GRAY_ZONE_UPPER_BOUND = 0.55

# Escalonamento humano obrigatório (agent.md §10). O valor de MonthlyCharges é um proxy
# para "alto valor de fatura" ainda não validado formalmente com o negócio — registrar
# a validação definitiva em ADR antes de ir para produção.
HIGH_RISK_PROBABILITY_THRESHOLD = 0.95
HIGH_RISK_MONTHLY_CHARGES_THRESHOLD = 100.0

HIGH_RISK_ESCALATION_ACTION = "Escalar imediatamente para um gerente de Customer Success."

GRAY_ZONE_PROMPT_INSTRUCTION = (
    "ATENÇÃO: esta probabilidade está na zona cinzenta (marginal). Em vez de uma oferta "
    "agressiva, a ação recomendada deve ser uma intervenção exploratória leve (ex: contato "
    "preventivo de relacionamento), deixando claro que não há fortes indícios históricos de "
    "cancelamento imediato."
)

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

{extra_instruction}

Regras estritas de saída:
1. Responda APENAS com um objeto JSON válido, sem markdown, sem blocos ```json.
2. O JSON deve ter exatamente estas chaves: "churn_probability" (float numérico),
   "risk_factors" (lista de 2 a 3 strings traduzindo os fatores SHAP acima em linguagem de
   negócio, sem citar "SHAP" ou jargão técnico), "recommended_action" (string com a ação de
   retenção sugerida).
3. Baseie-se exclusivamente nos fatores SHAP fornecidos — não invente outras causas.
"""


class ChurnAgentC:
    """Agente multi-etapa: valida entrada (guardrail, na camada FastAPI/Pydantic) →
    prevê → classifica a zona de confiança → consulta SHAP → chama o LLM com timeout →
    valida a saída (guardrail) → cai em fallback determinístico se qualquer etapa falhar.
    """

    def __init__(self):
        self.model_wrapper = RandomForestModelWrapper()
        self.shap_explainer = ShapExplainer(self.model_wrapper)

        if not GEMINI_API_KEY:
            # Degradação Graciosa Básica se a API Key não existir
            self.llm = None
        else:
            self.llm = genai.GenerativeModel(MODEL_NAME)

    def analyze(self, customer_data: dict) -> dict:
        probability = self.model_wrapper.predict_probability(customer_data)
        confidence_zone = self._determine_confidence_zone(probability, customer_data)
        top_factors = self.shap_explainer.get_top_risk_factors(customer_data)

        if not self.llm:
            return generate_fallback_response(probability, top_factors, confidence_zone)

        llm_result = self._try_generate_with_llm(customer_data, probability, top_factors, confidence_zone)
        if llm_result is None:
            return generate_fallback_response(probability, top_factors, confidence_zone)

        return self._finalize_success_response(llm_result, confidence_zone)

    def _determine_confidence_zone(self, probability: float, customer_data: dict) -> str:
        """Classifica o cliente numa das três zonas que mudam o comportamento do agente."""
        monthly_charges = customer_data.get("MonthlyCharges", 0)

        if probability > HIGH_RISK_PROBABILITY_THRESHOLD and monthly_charges > HIGH_RISK_MONTHLY_CHARGES_THRESHOLD:
            return "high_risk_escalation"
        if GRAY_ZONE_LOWER_BOUND <= probability <= GRAY_ZONE_UPPER_BOUND:
            return "gray_zone"
        return "standard"

    def _try_generate_with_llm(
        self, customer_data: dict, probability: float, top_factors: list[dict], confidence_zone: str
    ) -> dict | None:
        """Chama o Gemini 2.5 Flash com timeout agressivo. Devolve `None` em qualquer falha
        (timeout, erro de API, JSON malformado ou reprovado pelo guardrail de saída) — quem
        chama decide o fallback, esta função nunca deixa uma exceção vazar.
        """
        try:
            prompt = self._build_prompt(customer_data, probability, top_factors, confidence_zone)
            response = self.llm.generate_content(prompt, request_options={"timeout": LLM_TIMEOUT_SECONDS})

            result_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
            result = json.loads(result_text)

            if not is_valid_llm_output(result):
                print("Guardrail de saída reprovou a resposta do LLM (formato inválido). Acionando fallback.")
                return None

            return result
        except Exception as e:
            print(f"Erro no Agente LLM ({type(e).__name__}): {str(e)}. Acionando fallback.")
            return None

    def _build_prompt(
        self, customer_data: dict, probability: float, top_factors: list[dict], confidence_zone: str
    ) -> str:
        extra_instruction = GRAY_ZONE_PROMPT_INSTRUCTION if confidence_zone == "gray_zone" else ""
        return PROMPT_TEMPLATE.format(
            customer_data=json.dumps(customer_data, indent=2),
            probability=probability,
            shap_factors=self._format_shap_factors(top_factors),
            extra_instruction=extra_instruction,
        )

    def _format_shap_factors(self, top_factors: list[dict]) -> str:
        return "\n".join(
            f"- {factor['feature']}: impacto de {factor['shap_value']:+.4f} no score de churn"
            for factor in top_factors
        )

    def _finalize_success_response(self, llm_result: dict, confidence_zone: str) -> dict:
        """Aplica a regra determinística de escalonamento humano (agent.md §10): prevalece
        sobre a ação sugerida pelo LLM quando o risco é extremo, independente do que o
        modelo de linguagem tenha respondido.
        """
        if confidence_zone == "high_risk_escalation":
            llm_result["recommended_action"] = HIGH_RISK_ESCALATION_ACTION

        llm_result["system_status"] = {"llm_executed": True, "confidence_zone": confidence_zone}
        return llm_result

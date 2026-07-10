import numpy as np
import shap
from .model_wrapper import RandomForestModelWrapper

TOP_N_FACTORS = 3
CHURN_CLASS_INDEX = 1


class ShapExplainer:
    """Ferramenta que o agente consulta para obter o impacto matemático real de cada
    variável no score de churn de um cliente específico (SHAP local). Idêntica à
    shap_tool.py da Solution B.
    """

    def __init__(self, model_wrapper: RandomForestModelWrapper):
        self.model_wrapper = model_wrapper
        classifier = model_wrapper.pipeline.named_steps["classifier"]
        self.explainer = shap.TreeExplainer(classifier)

    def get_top_risk_factors(self, customer_data: dict, top_n: int = TOP_N_FACTORS) -> list[dict]:
        """Calcula os valores SHAP locais do cliente e devolve as `top_n` variáveis que
        mais empurraram o score em direção ao churn, cada uma com seu peso exato.
        """
        transformed_input = self.model_wrapper.transform_customer(customer_data)
        if hasattr(transformed_input, "toarray"):
            transformed_input = transformed_input.toarray()

        shap_values = self._compute_churn_class_shap_values(transformed_input)

        feature_names = self.model_wrapper.feature_names
        ranked_indices = np.argsort(shap_values)[::-1][:top_n]

        return [
            {"feature": feature_names[i], "shap_value": round(float(shap_values[i]), 4)}
            for i in ranked_indices
        ]

    def _compute_churn_class_shap_values(self, transformed_input: np.ndarray) -> np.ndarray:
        """Isola os valores SHAP da classe 'Churn' (1) para o primeiro (único) cliente do
        batch, cobrindo os dois formatos de retorno que o TreeExplainer pode devolver
        dependendo da versão da lib shap instalada.
        """
        raw_output = self.explainer.shap_values(transformed_input, check_additivity=False)

        if isinstance(raw_output, list):
            return np.asarray(raw_output[CHURN_CLASS_INDEX][0])
        if raw_output.ndim == 3:
            return np.asarray(raw_output[0, :, CHURN_CLASS_INDEX])
        return np.asarray(raw_output[0])

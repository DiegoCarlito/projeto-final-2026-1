import os
import joblib
import pandas as pd

MODEL_PATH = "src/model.joblib"


class RandomForestModelWrapper:
    """Isola o pipeline treinado (pré-processamento + Random Forest) do resto do agente."""

    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Modelo não encontrado em {MODEL_PATH}. Rode o train.py primeiro.")

        artifact = joblib.load(MODEL_PATH)
        self.pipeline = artifact["pipeline"]
        self.feature_names = artifact["feature_names"]

    def predict_probability(self, customer_data: dict) -> float:
        """Calcula a probabilidade de churn (classe 1) para um cliente."""
        df_input = pd.DataFrame([customer_data])
        probability = self.pipeline.predict_proba(df_input)[0][1]
        return float(probability)

    def transform_customer(self, customer_data: dict):
        """Aplica apenas o pré-processamento do pipeline (sem o classificador) a um cliente.

        Usado pelo ShapExplainer, que precisa dos dados já no espaço de features
        numérico/one-hot em que a Random Forest foi treinada.
        """
        df_input = pd.DataFrame([customer_data])
        preprocessor = self.pipeline.named_steps["preprocessor"]
        return preprocessor.transform(df_input)

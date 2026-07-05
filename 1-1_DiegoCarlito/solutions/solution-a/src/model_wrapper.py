import joblib
import pandas as pd
import numpy as np
import os

MODEL_PATH = "src/model.joblib"

class BaselineModelWrapper:
    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Modelo não encontrado em {MODEL_PATH}. Rode o train.py primeiro.")
        
        artifact = joblib.load(MODEL_PATH)
        self.pipeline = artifact['pipeline']
        self.feature_names = artifact['feature_names']
        
        # Extrair coeficientes globais da Regressão Logística
        classifier = self.pipeline.named_steps['classifier']
        self.coefficients = classifier.coef_[0]

    def predict_with_factors(self, customer_data: dict) -> tuple[float, list[str]]:
        """
        Calcula a probabilidade de churn e devolve os top fatores de risco globais 
        que estão presentes nos dados deste cliente.
        """
        df_input = pd.DataFrame([customer_data])
        
        # Predição de probabilidade (classe 1 = Churn)
        probability = self.pipeline.predict_proba(df_input)[0][1]
        
        # Para a Solution A (Baseline), usamos os maiores coeficientes globais positivos 
        # como "fatores de risco base" para passar ao LLM como contexto.
        top_indices = np.argsort(self.coefficients)[-5:] # Top 5 coeficientes que levam ao churn
        top_features = [self.feature_names[i] for i in reversed(top_indices)]
        
        return float(probability), top_features

import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

# Constantes de configuração
DATA_PATH = "../../data/telco_churn.csv"
MODEL_SAVE_PATH = "src/model.joblib"
TARGET_COLUMN = "Churn"
TEST_SIZE = 0.2
RANDOM_STATE = 42

def load_and_clean_data(file_path: str) -> pd.DataFrame:
    """Carrega o CSV e aplica limpeza básica (tratamento do TotalCharges vazio)."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de dados não encontrado em: {file_path}")
    
    df = pd.read_csv(file_path)
    # TotalCharges vem como string por causa de espaços em branco; converter para numérico
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df.dropna(subset=['TotalCharges'], inplace=True)
    
    # Remover ID do cliente pois não é feature preditiva
    if 'customerID' in df.columns:
        df.drop('customerID', axis=1, inplace=True)
        
    return df

def build_pipeline(categorical_cols: list, numerical_cols: list) -> Pipeline:
    """Constrói o pipeline do scikit-learn com pré-processamento e modelo linear."""
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_cols),
            ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), categorical_cols)
        ])
    
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(max_iter=1000, random_state=RANDOM_STATE))
    ])
    
    return pipeline

def train_model():
    """Executa o fluxo completo de treino e salva o artefato."""
    print("Iniciando treino do modelo baseline (Solution A)...")
    df = load_and_clean_data(DATA_PATH)
    
    X = df.drop(TARGET_COLUMN, axis=1)
    y = df[TARGET_COLUMN].map({'Yes': 1, 'No': 0})
    
    categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
    numerical_cols = X.select_dtypes(exclude=['object']).columns.tolist()
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    
    pipeline = build_pipeline(categorical_cols, numerical_cols)
    pipeline.fit(X_train, y_train)
    
    accuracy = pipeline.score(X_test, y_test)
    print(f"Treino concluído. Acurácia no teste: {accuracy:.4f}")
    
    # Extrair nomes reais das features após o OneHotEncoding
    cat_encoder = pipeline.named_steps['preprocessor'].named_transformers_['cat']
    encoded_cat_cols = cat_encoder.get_feature_names_out(categorical_cols)
    all_feature_names = numerical_cols + list(encoded_cat_cols)
    
    # Salvar pipeline e lista de features para uso no Wrapper
    joblib.dump({'pipeline': pipeline, 'feature_names': all_feature_names}, MODEL_SAVE_PATH)
    print(f"Modelo salvo em {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_model()

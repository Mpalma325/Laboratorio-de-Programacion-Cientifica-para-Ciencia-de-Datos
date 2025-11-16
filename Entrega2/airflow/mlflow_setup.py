"""
Inicializa MLflow y define dónde y bajo qué nombre se registran 
los resultados de cada entrenamiento del pipeline predictivo.
"""

import mlflow
mlflow.set_tracking_uri("file:/opt/airflow/mlruns")
mlflow.set_experiment("predictive_pipeline_xgb")
def get_mlflow_client():
    return mlflow

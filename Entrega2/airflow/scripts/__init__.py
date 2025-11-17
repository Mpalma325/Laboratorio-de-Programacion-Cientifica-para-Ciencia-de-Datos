"""
Módulos para el pipeline de Airflow.

El archivo contiene las funciones principales utilizadas en el DAG:
 - prepare_data: preparación y limpieza de datos
 - detect_drift: detección de drift en los datos (opcional)
 - train_model: entrenamiento del modelo XGBoost con MLflow
 - explain_model: generación de interpretabilidad con SHAP
 - predict_next_week: predicción automática para la próxima semana

__init__.py permite que Python reconozca esta carpeta como
un paquete importable y así Airflow pueda ejecutar correctamente
los módulos contenidos en scripts/.
"""

__all__ = [
    "data_preparation",
    "detect_drift",
    "model_training",
    "explainability",
    "predict_next_week",
]
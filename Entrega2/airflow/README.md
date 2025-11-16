# Predictive Pipeline (XGBoost) – Airflow + MLflow + SHAP

Usa los hiperparámetros que compartiste (Optuna `study.best_params`) y los integra al pipeline de Airflow.

## Hiperparámetros
Se cargan desde `data/config/xgb_best_params.json` o env var `XGB_BEST_PARAMS` (JSON).

## Flujo
1. `prepare_data` → features + preprocesador (persistidos).
2. `detect_drift` → KS-test sobre `features.parquet` vs referencia.
3. `retrain_xgb` → entrena XGB con tus params y calcula umbral óptimo (F1).
4. `explain_model` → SHAP summary.
5. `predict_next_week` → aplica ambos pipelines y genera `score`/`pred_compra`.

## Rutas esperadas
- `/opt/airflow/data/raw/transacciones.parquet` (t)
- `/opt/airflow/data/reference/features.parquet` (referencia para drift)
- `/opt/airflow/data/new_data/transacciones.parquet` (t+1)

## Ejecución
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

export AIRFLOW_HOME=$(pwd)
airflow db init
airflow webserver &
airflow scheduler &
```


## Actualización
- `prepare_data` ahora **mergea `clientes.parquet` y `productos.parquet`** si están presentes en `data/raw/`.
- `predict_next_week` concatena histórico (t) + nuevos (t+1) para calcular **recencias y shifts correctos** y filtra la **semana t+1** automáticamente.

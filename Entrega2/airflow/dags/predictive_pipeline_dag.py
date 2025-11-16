from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

from scripts.data_preparation import prepare_data
from scripts.detect_drift import detect_drift  # debe retornar 'retrain_xgb' o 'skip_retrain'
from scripts.model_training import train_model
from scripts.explainability import explain_model
from scripts.predict_next_week import predict_next_week

def skip_retrain(**kwargs):
    print("⏩ Sin drift, sin reentrenamiento")

default_args = {
    "owner": "ml_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="predictive_pipeline_xgb",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="@weekly",   # en Airflow >=2.6 puedes usar 'schedule=' si prefieres
    catchup=False,
    max_active_runs=1,
    tags=["ml", "xgboost", "mlflow", "shap"],
) as dag:

    t1_prepare = PythonOperator(
        task_id="prepare_data",
        python_callable=prepare_data,
    )

    t2_drift = BranchPythonOperator(
        task_id="detect_drift",
        python_callable=detect_drift,  
    )

    t3_train = PythonOperator(
        task_id="retrain_xgb",
        python_callable=train_model,
    )

    t4_explain = PythonOperator(
        task_id="explain_model",
        python_callable=explain_model,
    )

    t5_predict = PythonOperator(
        task_id="predict_next_week",
        python_callable=predict_next_week,
    )

    t_skip = PythonOperator(
        task_id="skip_retrain",
        python_callable=skip_retrain,
    )

    t1_prepare >> t2_drift
    t2_drift >> [t3_train, t_skip]
    t3_train >> t4_explain >> t5_predict
    t_skip >> t5_predict

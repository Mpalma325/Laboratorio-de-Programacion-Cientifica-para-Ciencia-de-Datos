from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from hiring_functions import create_folders, split_data, preprocess_and_train

import joblib
import gradio as gr
import pandas as pd


def serve_gradio_json(**kwargs):
    dags_dir = Path(__file__).resolve().parent
    ds_nodash = kwargs.get("ds_nodash")
    if not ds_nodash:
        ds_nodash = datetime.now().strftime("%Y%m%d")
    
    model_path = dags_dir / ds_nodash / "models" / "rf_pipeline.joblib"
    
    artefacto = joblib.load(model_path)
    pipe = artefacto["model"]
    feature_columns = artefacto["feature_columns"]

    def predecir_json(json_file):
        df = pd.read_json(json_file.name)
        
        if isinstance(df, pd.Series):
            df = df.to_frame().T
        if df.ndim == 1:
            df = df.to_frame().T
        
        
        X = df[feature_columns]
        y_hat = pipe.predict(X)
        
        if hasattr(pipe.named_steps["clf"], "predict_proba"):
            p1 = pipe.predict_proba(X)[:, 1]
            out = pd.DataFrame({"prediccion": y_hat, "prob_positivo": p1})
        else:
            out = pd.DataFrame({"prediccion": y_hat})
        
        return out

    demo = gr.Interface(
        fn=predecir_json,
        inputs=gr.File(
            label="JSON con las mismas columnas de entrenamiento", 
            file_types=[".json"]
        ),
        outputs=gr.Dataframe(),
        title="Predicción de contratación archivo JSON",
        description="Cargar archivo JSON"
    )
    
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)



default_args = {
    "owner": "marcelo",
    "depends_on_past": False,
}

with DAG(
    dag_id="hiring_lineal",
    start_date=datetime(2024, 10, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["lab9", "hiring"],
) as dag:

    start = EmptyOperator(task_id="start")

    create_dirs = PythonOperator(
        task_id="create_folders",
        python_callable=create_folders,
    )

    download_raw = BashOperator(
        task_id="download_data",
        bash_command=(
            "curl -L -o /opt/airflow/dags/{{ ds_nodash }}/raw/data_1.csv "
            "https://gitlab.com/eduardomoyab/laboratorio-13/-/raw/main/files/data_1.csv"
        ),
    )

    do_split = PythonOperator(
        task_id="split_data",
        python_callable=split_data,
        op_kwargs={"target_col": "HiringDecision"},
    )

    train_model = PythonOperator(
        task_id="preprocess_and_train",
        python_callable=preprocess_and_train,
        op_kwargs={"target_col": "HiringDecision"},
    )

    serve_gradio = PythonOperator(
        task_id="serve_gradio_json",
        python_callable=serve_gradio_json,
    )

    start >> create_dirs >> download_raw >> do_split >> train_model >> serve_gradio
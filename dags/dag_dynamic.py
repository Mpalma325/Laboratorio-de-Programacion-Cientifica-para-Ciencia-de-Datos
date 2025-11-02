from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule
from hiring_dynamic_functions import create_folders, split_data, load_and_merge, train_model, evaluate_models
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


def branch_download(**kwargs):
    run_date = datetime.strptime(kwargs["ds"], "%Y-%m-%d")
    if run_date < datetime(2024, 11, 1):
        return "download_data1"
    else:
        return "download_data_both"


default_args = {"owner": "marcelo", "depends_on_past": False}

with DAG(
    dag_id="hiring_dynamic",
    start_date=datetime(2024, 10, 1),
    schedule="0 15 5 * *",
    catchup=True,
    default_args=default_args,
    tags=["lab9", "dynamic"],
    description="Pipeline dinámico para entrenamiento mensual con múltiples modelos",
) as dag:

    start = EmptyOperator(task_id="start")

    create_dirs = PythonOperator(task_id="create_folders", python_callable=create_folders)

    branching = BranchPythonOperator(task_id="branch_download", python_callable=branch_download)

    download_data1 = BashOperator(
        task_id="download_data1",
        bash_command=(
            "curl -L -o /opt/airflow/dags/{{ ds_nodash }}/raw/data_1.csv "
            "https://gitlab.com/eduardomoyab/laboratorio-13/-/raw/main/files/data_1.csv"
        ),
    )

    download_data_both = BashOperator(
        task_id="download_data_both",
        bash_command=(
            "curl -L -o /opt/airflow/dags/{{ ds_nodash }}/raw/data_1.csv "
            "https://gitlab.com/eduardomoyab/laboratorio-13/-/raw/main/files/data_1.csv && "
            "curl -L -o /opt/airflow/dags/{{ ds_nodash }}/raw/data_2.csv "
            "https://gitlab.com/eduardomoyab/laboratorio-13/-/raw/main/files/data_2.csv"
        ),
    )

    merge_data = PythonOperator(
        task_id="load_and_merge",
        python_callable=load_and_merge,
        trigger_rule=TriggerRule.ONE_SUCCESS,
    )

    do_split = PythonOperator(
        task_id="split_data",
        python_callable=split_data,
        op_kwargs={"target_col": "HiringDecision"},
    )

    train_rf = PythonOperator(
        task_id="train_rf",
        python_callable=train_model,
        op_kwargs={"model": RandomForestClassifier(n_estimators=300, random_state=42), "target_col": "HiringDecision"},
    )

    train_lr = PythonOperator(
        task_id="train_lr",
        python_callable=train_model,
        op_kwargs={
            "model": LogisticRegression(max_iter=1000, random_state=42),
            "target_col": "HiringDecision",
        },
    )

    train_dt = PythonOperator(
        task_id="train_dt",
        python_callable=train_model,
        op_kwargs={"model": DecisionTreeClassifier(random_state=42), "target_col": "HiringDecision"},
    )

    evaluate = PythonOperator(
        task_id="evaluate_models",
        python_callable=evaluate_models,
        op_kwargs={"target_col": "HiringDecision"},
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    end = EmptyOperator(task_id="end")

    (
        start
        >> create_dirs
        >> branching
        >> [download_data1, download_data_both]
        >> merge_data
        >> do_split
        >> [train_rf, train_lr, train_dt]
        >> evaluate
        >> end
    )
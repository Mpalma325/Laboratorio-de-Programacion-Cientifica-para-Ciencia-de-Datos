import joblib
import pandas as pd
import shap
import matplotlib.pyplot as plt
from pathlib import Path
from mlflow_setup import get_mlflow_client


def explain_model(**kwargs):
    ml = get_mlflow_client()
    model = joblib.load("/opt/airflow/data/models/model_xgb.pkl")
    df = pd.read_parquet("/opt/airflow/data/processed/features.parquet")
    X = df.drop(columns=["y"])
    Xs = X.sample(min(1000, len(X)), random_state=42)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(Xs)

    Path("/opt/airflow/data/artifacts").mkdir(parents=True, exist_ok=True)
    plt.figure()
    shap.summary_plot(shap_values, Xs, show=False)
    out_png = "/opt/airflow/data/artifacts/shap_summary_xgb.png"
    plt.savefig(out_png, bbox_inches="tight")
    ml.log_artifact(out_png)

import numpy as np
import joblib
import pandas as pd
import shap
import matplotlib.pyplot as plt
from pathlib import Path
from mlflow_setup import get_mlflow_client


def explain_model(**kwargs):
    ml = get_mlflow_client()
    model = joblib.load("/opt/airflow/data/models/model_xgb.pkl")
    preprocessor = joblib.load("/opt/airflow/data/models/preprocessor.pkl")
    
    df = pd.read_parquet("/opt/airflow/data/processed/features.parquet")
    
    X = preprocessor.transform(df)
    
    n_samples = min(1000, X.shape[0])
    if hasattr(X, 'toarray'):
        X_dense = X.toarray()
    else:
        X_dense = X
    
    indices = np.random.RandomState(42).choice(X.shape[0], n_samples, replace=False)
    Xs = X_dense[indices]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(Xs)

    Path("/opt/airflow/data/artifacts").mkdir(parents=True, exist_ok=True)
    plt.figure()
    shap.summary_plot(shap_values, Xs, show=False)
    out_png = "/opt/airflow/data/artifacts/shap_summary_xgb.png"
    plt.savefig(out_png, bbox_inches="tight")
    plt.close()
    ml.log_artifact(out_png)
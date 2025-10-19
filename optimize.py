#Imports
import os
import json
import time
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
import mlflow
from mlflow import log_artifact, log_artifacts, log_metric, log_param, log_params, log_dict, start_run, set_experiment, set_tracking_uri
import optuna
from optuna import Trial
from optuna.visualization.matplotlib import plot_optimization_history, plot_param_importances
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import platform
import sys

# Configuración
DATA_PATH = os.getenv("DATA_PATH", "water_potability.csv")
N_TRIALS = int(os.getenv("N_TRIALS", "30"))
RANDOM_STATE = int(os.getenv("RANDOM_STATE", "42"))

# Directorios
ARTIFACTS_DIR = Path("artifacts")
PLOTS_DIR = ARTIFACTS_DIR / "plots"
MODELS_DIR = ARTIFACTS_DIR / "models"
for d in [ARTIFACTS_DIR, PLOTS_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

set_tracking_uri("mlruns")


def version_snapshot():
    payload = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit-learn": __import__("sklearn").__version__,
        "xgboost": __import__("xgboost").__version__,
        "optuna": optuna.__version__,
        "mlflow": mlflow.__version__,
    }
    with open(ARTIFACTS_DIR / "versions.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return payload


def suggest_params(trial: Trial):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 800),
        "max_depth": trial.suggest_int("max_depth", 2, 10),
        "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "min_child_weight": trial.suggest_float("min_child_weight", 1e-2, 10.0, log=True),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 1.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "gamma": trial.suggest_float("gamma", 1e-8, 1.0, log=True),
        "scale_pos_weight": trial.suggest_float("scale_pos_weight", 0.5, 2.0),
    }
    return params


def build_model(params):
    model = XGBClassifier(
        **params,
        objective="binary:logistic",
        eval_metric="auc",
        tree_method="hist",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbosity=0
    )
    return model


def evaluate_model(model, X_valid, y_valid):
    preds = model.predict(X_valid)
    preds_proba = model.predict_proba(X_valid)[:, 1]
    
    metrics = {
        "valid_f1": f1_score(y_valid, preds),
        "valid_precision": precision_score(y_valid, preds),
        "valid_recall": recall_score(y_valid, preds),
        "valid_roc_auc": roc_auc_score(y_valid, preds_proba)
    }
    return metrics


def plot_feature_importance(model, feature_names, output_path):
    importances = model.feature_importances_
    fig, ax = plt.subplots(figsize=(10, 6))
    idx = np.argsort(importances)[::-1]
    
    ax.bar(range(len(importances)), importances[idx])
    ax.set_xticks(range(len(importances)))
    ax.set_xticklabels([feature_names[i] for i in idx], rotation=45, ha='right')
    ax.set_xlabel('Características')
    ax.set_ylabel('Importancia')
    ax.set_title('Importancia de Características - XGBoost')
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_optuna_visualizations(study, plots_dir):
    try:
        fig1 = plot_optimization_history(study)
        fig1.savefig(plots_dir / "optuna_optimization_history.png", dpi=160, bbox_inches="tight")
        plt.close(fig1)
    except Exception:
        pass
    
    try:
        fig2 = plot_param_importances(study)
        fig2.savefig(plots_dir / "optuna_param_importances.png", dpi=160, bbox_inches="tight")
        plt.close(fig2)
    except Exception:
        pass


def optimize_model():
    # Cargar datos
    df = pd.read_csv(DATA_PATH)
    X = df.drop(columns=["Potability"])
    y = df["Potability"].astype(int)
    
    # Split estratificado
    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    
    # Imputar valores faltantes
    medians = X_train.median(numeric_only=True)
    X_train = X_train.fillna(medians)
    X_valid = X_valid.fillna(medians)
    medians_dict = medians.to_dict()
    
    # Calcular scale_pos_weight base
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    base_scale_pos_weight = neg_count / pos_count
    
    # Configurar Optuna y MLflow
    ts = time.strftime("%Y%m%d-%H%M%S")
    study_name = f"Potability-XGB-{ts}"
    exp_name = f"Potability-Optimization-{ts}"
    
    set_experiment(exp_name)
    study = optuna.create_study(
        direction="maximize",
        study_name=study_name,
        sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE),
        pruner=optuna.pruners.MedianPruner(
            n_startup_trials=5,
            n_warmup_steps=10,
            interval_steps=1
        )
    )
    
    best_model_container = {"model": None, "f1": 0.0, "trial_num": -1}
    
    def objective(trial: Trial):
        params = suggest_params(trial)
        
        run_name = (
            f"Trial_{trial.number:03d}_"
            f"lr{params['learning_rate']:.4f}_"
            f"depth{params['max_depth']}_"
            f"nest{params['n_estimators']}"
        )
        
        with start_run(run_name=run_name):
            log_params(params)
            log_param("trial_number", trial.number)
            log_param("split_seed", RANDOM_STATE)
            log_param("base_scale_pos_weight", base_scale_pos_weight)
            
            start_time = time.time()
            model = build_model(params)
            model.fit(X_train, y_train)
            train_time = time.time() - start_time
            
            metrics = evaluate_model(model, X_valid, y_valid)
            
            for metric_name, metric_value in metrics.items():
                log_metric(metric_name, float(metric_value))
            log_metric("train_time_sec", train_time)
            
            f1 = metrics["valid_f1"]
            
            if f1 > best_model_container["f1"]:
                best_model_container["model"] = model
                best_model_container["f1"] = f1
                best_model_container["trial_num"] = trial.number
            
            return f1
    
    study.optimize(objective, n_trials=N_TRIALS, catch=(Exception,), show_progress_bar=False)
    
    # Guardar mejor modelo
    best_model = best_model_container["model"]
    best_params = study.best_params
    best_f1 = best_model_container["f1"]
    
    model_path = MODELS_DIR / "best_xgb.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(best_model, f)
    
    # Guardar estudio
    study_path = ARTIFACTS_DIR / "optuna_study.pkl"
    with open(study_path, "wb") as f:
        pickle.dump(study, f)
    
    # Guardar configuración
    best_config = {
        "best_trial_number": best_model_container["trial_num"],
        "best_params": best_params,
        "best_f1_score": float(best_f1),
        "n_trials_executed": len(study.trials),
        "n_trials_completed": len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]),
        "n_trials_pruned": len([t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED]),
        "median_imputation_values": medians_dict,
        "base_scale_pos_weight": float(base_scale_pos_weight),
        "random_state": RANDOM_STATE,
        "timestamp": ts
    }
    
    with open(ARTIFACTS_DIR / "best_config.json", "w", encoding="utf-8") as f:
        json.dump(best_config, f, indent=2, ensure_ascii=False)
    
    versions = version_snapshot()
    
    # Generar gráficos
    plot_optuna_visualizations(study, PLOTS_DIR)
    plot_feature_importance(best_model, X.columns.tolist(), PLOTS_DIR / "feature_importance.png")
    
    # Run resumen
    with start_run(run_name=f"SUMMARY_Best_F1={best_f1:.4f}"):
        final_metrics = evaluate_model(best_model, X_valid, y_valid)
        for metric_name, metric_value in final_metrics.items():
            log_metric(metric_name, float(metric_value))
        
        log_params(best_params)
        log_param("best_trial_number", best_model_container["trial_num"])
        log_param("n_trials_total", N_TRIALS)
        log_param("n_trials_completed", best_config["n_trials_completed"])
        log_param("n_trials_pruned", best_config["n_trials_pruned"])
        log_param("base_scale_pos_weight", base_scale_pos_weight)
        
        log_dict(versions, "versions.json")
        log_dict(best_config, "best_config.json")
        log_dict(medians_dict, "imputation_medians.json")
        log_artifacts(str(PLOTS_DIR), artifact_path="plots")
        log_artifacts(str(MODELS_DIR), artifact_path="models")
        log_artifact(str(study_path))
    
    return best_model


if __name__ == "__main__":
    optimize_model()
from pathlib import Path
from datetime import datetime
import pandas as pd
import joblib
import gradio as gr
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score


def create_folders(**kwargs):
    dags_dir = Path(__file__).resolve().parent
    ds_nodash = kwargs.get("ds_nodash")
    
    if not ds_nodash:
        ds_nodash = datetime.now().strftime("%Y%m%d")

    run_dir = dags_dir / ds_nodash
    subdirs = ["raw", "splits", "models"]
    
    run_dir.mkdir(parents=True, exist_ok=True)
    for sub in subdirs:
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    return str(run_dir)


def split_data(**kwargs):
    dags_dir = Path(__file__).resolve().parent
    ds_nodash = kwargs.get("ds_nodash") or datetime.now().strftime("%Y%m%d")
    target_col = kwargs.get("target_col", "HiringDecision")
    run_dir = dags_dir / ds_nodash
    raw, splits = run_dir / "raw", run_dir / "splits"
    splits.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(raw / "data_1.csv")
    y = df[target_col]
    X = df.drop(columns=[target_col])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pd.concat([X_train, y_train], axis=1).to_csv(splits / "train.csv", index=False)
    pd.concat([X_test, y_test], axis=1).to_csv(splits / "test.csv", index=False)


def preprocess_and_train(**kwargs):
    dags_dir = Path(__file__).resolve().parent
    ds_nodash = kwargs.get("ds_nodash") or datetime.now().strftime("%Y%m%d")
    target_col = kwargs.get("target_col", "HiringDecision")
    run_dir = dags_dir / ds_nodash
    splits_dir = run_dir / "splits"
    models_dir = run_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(splits_dir / "train.csv")
    test_df = pd.read_csv(splits_dir / "test.csv")

    X_train, y_train = train_df.drop(columns=[target_col]), train_df[target_col]
    X_test, y_test = test_df.drop(columns=[target_col]), test_df[target_col]

    cat_cols = X_train.select_dtypes(include=["object", "category"]).columns.tolist()
    num_cols = X_train.select_dtypes(exclude=["object", "category"]).columns.tolist()

    pre_num = Pipeline([("imp", SimpleImputer(strategy="median"))])
    pre_cat = Pipeline([
        ("imp", SimpleImputer(strategy="most_frequent")), 
        ("ohe", OneHotEncoder(handle_unknown="ignore"))
    ])
    pre = ColumnTransformer([
        ("num", pre_num, num_cols), 
        ("cat", pre_cat, cat_cols)
    ])

    clf = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
    pipe = Pipeline([("pre", pre), ("clf", clf)])
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, pos_label=1)

    model_path = models_dir / "rf_pipeline.joblib"
    joblib.dump({
        "model": pipe, 
        "feature_columns": X_train.columns.tolist(), 
        "target_col": target_col
    }, model_path)

    print(f"Accuracy test: {acc:.4f}")
    print(f"F1 positivo (contratado): {f1:.4f}")
    print(f"Modelo guardado en: {model_path}")

    return str(model_path)


def gradio_interface(**kwargs):
    dags_dir = Path(__file__).resolve().parent
    ds_nodash = kwargs.get("ds_nodash") or datetime.now().strftime("%Y%m%d")
    model_path = kwargs.get("model_path") or (dags_dir / ds_nodash / "models" / "rf_pipeline.joblib")

    artefacto = joblib.load(model_path)
    pipe = artefacto["model"]
    feature_columns = artefacto["feature_columns"]

    def predecir(csv_file):
        df = pd.read_csv(csv_file.name)
        faltantes = [c for c in feature_columns if c not in df.columns]
        if faltantes:
            raise ValueError(f"Faltan columnas en el CSV: {faltantes}")
        X = df[feature_columns]
        y_hat = pipe.predict(X)
        if hasattr(pipe.named_steps["clf"], "predict_proba"):
            p1 = pipe.predict_proba(X)[:, 1]
            out = pd.DataFrame({"prediccion": y_hat, "prob_positivo": p1})
        else:
            out = pd.DataFrame({"prediccion": y_hat})
        return out

    demo = gr.Interface(
        fn=predecir,
        inputs=gr.File(label="CSV con mismas columnas que train.csv"),
        outputs=gr.Dataframe(),
        title="Predicción de contratación",
        description="Sube un CSV con las mismas columnas de entrenamiento; devuelve predicción y probabilidad positiva."
    )
    demo.launch()
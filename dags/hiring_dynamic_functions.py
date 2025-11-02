from pathlib import Path
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
import joblib
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score

def create_folders(**kwargs):
    dags_dir = Path(__file__).resolve().parent
    ds_nodash = kwargs.get("ds_nodash") or datetime.now().strftime("%Y%m%d")

    run_dir = dags_dir / ds_nodash
    subdirs = ["raw", "preprocessed", "splits", "models"]

    run_dir.mkdir(parents=True, exist_ok=True)
    for sub in subdirs:
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
        
    return str(run_dir)

def load_and_merge(**kwargs):
    dags_dir = Path(__file__).resolve().parent
    ds_nodash = kwargs.get("ds_nodash") or datetime.now().strftime("%Y%m%d")
    run_dir = dags_dir / ds_nodash
    raw_dir = run_dir / "raw"
    pre_dir = run_dir / "preprocessed"
    pre_dir.mkdir(parents=True, exist_ok=True)

    data1_path = raw_dir / "data_1.csv"
    data2_path = raw_dir / "data_2.csv"

    df1 = pd.read_csv(data1_path)
    if data2_path.exists():
        df2 = pd.read_csv(data2_path)
        df = pd.concat([df1, df2], ignore_index=True)
    else:
        df = df1.copy()


    merged_path = pre_dir / "merged.csv"
    df.to_csv(merged_path, index=False)


    return str(merged_path)


def split_data(**kwargs):
    dags_dir = Path(__file__).resolve().parent
    ds_nodash = kwargs.get("ds_nodash") or datetime.now().strftime("%Y%m%d")
    target_col = kwargs.get("target_col", "HiringDecision")

    run_dir = dags_dir / ds_nodash
    pre_dir = run_dir / "preprocessed"
    splits_dir = run_dir / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    merged_path = pre_dir / "merged.csv"

    df = pd.read_csv(merged_path)

    y = df[target_col]
    X = df.drop(columns=[target_col])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    train_path = splits_dir / "train.csv"
    test_path = splits_dir / "test.csv"

    pd.concat([X_train, y_train], axis=1).to_csv(train_path, index=False)
    pd.concat([X_test, y_test], axis=1).to_csv(test_path, index=False)


    return str(splits_dir)




def train_model(model, **kwargs):
    dags_dir = Path(__file__).resolve().parent
    ds_nodash = kwargs.get("ds_nodash") or datetime.now().strftime("%Y%m%d")
    target_col = kwargs.get("target_col", "HiringDecision")

    run_dir = dags_dir / ds_nodash
    splits_dir = run_dir / "splits"
    models_dir = run_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(splits_dir / "train.csv")
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]

    cat_cols = X_train.select_dtypes(include=["object", "category"]).columns.tolist()
    num_cols = X_train.select_dtypes(exclude=["object", "category"]).columns.tolist()

    pre_num = Pipeline([("imp", SimpleImputer(strategy="median"))])
    pre_cat = Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("ohe", OneHotEncoder(handle_unknown="ignore"))])
    pre = ColumnTransformer([("num", pre_num, num_cols), ("cat", pre_cat, cat_cols)])

    pipe = Pipeline([("pre", pre), ("clf", model)])
    pipe.fit(X_train, y_train)

    model_name = model.__class__.__name__.lower()
    model_path = models_dir / f"{model_name}_{ds_nodash}.joblib"
    joblib.dump({"model": pipe, "feature_columns": X_train.columns.tolist(), "target_col": target_col, "model_name": model_name}, model_path)

    return str(model_path)

def evaluate_models(**kwargs):
    dags_dir = Path(__file__).resolve().parent
    ds_nodash = kwargs.get("ds_nodash") or datetime.now().strftime("%Y%m%d")
    target_col = kwargs.get("target_col", "HiringDecision")

    run_dir = dags_dir / ds_nodash
    splits_dir = run_dir / "splits"
    models_dir = run_dir / "models"

    test_df = pd.read_csv(splits_dir / "test.csv")
    X_test = test_df.drop(columns=[target_col])
    y_test = test_df[target_col]

    model_files = list(models_dir.glob("*.joblib"))

    best_acc = -1
    best_model = None
    best_name = None

    for model_file in model_files:
        artefacto = joblib.load(model_file)
        pipe = artefacto["model"]
        name = artefacto.get("model_name", model_file.stem)
        acc = accuracy_score(y_test, pipe.predict(X_test))


        print(f"Modelo {name}: accuracy = {acc:.4f}")

        if acc > best_acc:
            best_acc = acc
            best_model = artefacto
            best_name = name

    print(f"Mejor modelo seleccionado: {best_name}")
    print(f"Accuracy obtenido: {best_acc:.4f}")

    best_path = models_dir / "best_model.joblib"
    joblib.dump(best_model, best_path)

    return str(best_path)

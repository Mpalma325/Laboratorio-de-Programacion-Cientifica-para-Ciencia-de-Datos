import pickle
import json
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import pandas as pd

MODEL_PATH = Path("artifacts/models/best_xgb.pkl")
MEDIANS_PATH = Path("artifacts/best_config.json")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with open(MEDIANS_PATH, "r") as f:
    config = json.load(f)
    medians = config["median_imputation_values"]

FEATURE_NAMES = ["ph", "Hardness", "Solids", "Chloramines", "Sulfate", 
                 "Conductivity", "Organic_carbon", "Trihalomethanes", "Turbidity"]

app = FastAPI()


class WaterSample(BaseModel):
    ph: float
    Hardness: float
    Solids: float
    Chloramines: float
    Sulfate: float
    Conductivity: float
    Organic_carbon: float
    Trihalomethanes: float
    Turbidity: float


class PredictionResponse(BaseModel):
    potable: bool
    probability: float


@app.get("/")
def home():
    return {
        "modelo": "XGBoost Classifier optimizado con Optuna",
        "problema": "Clasificación binaria: determinar si una muestra de agua es potable o no potable",
        "entrada": {
            "features": FEATURE_NAMES
        },
        "salida": {
            "potable": "boolean",
            "probability": "float"
        }
    }


@app.post("/potabilidad/", response_model=PredictionResponse)
def predict_potability(sample: WaterSample):
    input_data = pd.DataFrame([{
        "ph": sample.ph,
        "Hardness": sample.Hardness,
        "Solids": sample.Solids,
        "Chloramines": sample.Chloramines,
        "Sulfate": sample.Sulfate,
        "Conductivity": sample.Conductivity,
        "Organic_carbon": sample.Organic_carbon,
        "Trihalomethanes": sample.Trihalomethanes,
        "Turbidity": sample.Turbidity
    }])
    
    input_data = input_data.fillna(medians)
    input_data = input_data[FEATURE_NAMES]
    
    prediction = model.predict(input_data)[0]
    probability = model.predict_proba(input_data)[0][1]
    
    return PredictionResponse(
        potable=bool(prediction == 1),
        probability=float(probability)
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

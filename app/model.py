import json
import joblib
import pandas as pd

model = joblib.load("model/model.joblib")

with open("model/features.json", "r") as f:
    FEATURES = json.load(f)


def predict(features_dict: dict) -> float:
    df = pd.DataFrame([features_dict])

    # enforce exact feature order
    df = df[FEATURES]

    pred = model.predict(df)[0]
    return float(pred)
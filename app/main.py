from fastapi import FastAPI
from app.schemas import QueryRequest, PredictionResponse
from app.llm import stage1_extract, stage2_interpret
from app.model import predict

app = FastAPI(title="AI Real Estate Agent API")

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/predict", response_model=PredictionResponse)
def run_pipeline(payload: QueryRequest):

    query = payload.query
    manual_features = payload.manual_features

    if manual_features:
        features = manual_features
        confident_fields = [k for k, v in features.items() if v is not None]
        missing_fields = [k for k, v in features.items() if v is None]
        confidence_score = round(len(confident_fields) / len(features), 2)

        ready_for_prediction = len([
            f for f in ["Gr Liv Area", "Overall Qual", "Year Built"]
            if features.get(f) is not None
        ]) >= 2

        prompt_version = "manual"

    else:
        stage1 = stage1_extract(query)

        features = stage1["features"]
        confident_fields = stage1["confident_fields"]
        missing_fields = stage1["missing_fields"]
        ready_for_prediction = stage1["ready_for_prediction"]
        confidence_score = stage1["confidence_score"]
        prompt_version = stage1["prompt_version"]

    if not ready_for_prediction:
        return {
            "extracted_features": features,
            "confident_fields": confident_fields,
            "missing_fields": missing_fields,
            "ready_for_prediction": False,
            "predicted_price": None,
            "interpretation": "",
            "message": "Not enough info. Provide at least size, quality, or year.",
            "confidence_score": confidence_score,
            "prompt_version": prompt_version,
        }

    price = predict(features)
    explanation = stage2_interpret(features, price)

    return {
        "extracted_features": features,
        "confident_fields": confident_fields,
        "missing_fields": missing_fields,
        "ready_for_prediction": True,
        "predicted_price": float(price),
        "interpretation": explanation,
        "message": "Prediction based on available data",
        "confidence_score": confidence_score,
        "prompt_version": prompt_version,
    }
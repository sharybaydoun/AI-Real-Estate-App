from fastapi import FastAPI
from app.schemas import QueryRequest, PredictionResponse

app = FastAPI(title="AI Real Estate Agent API")


@app.get("/")
def root():
    return {"message": "API is running"}


@app.post("/predict", response_model=PredictionResponse)
def run_pipeline(payload: QueryRequest):
    from app.llm import stage1_extract, stage2_interpret
    from app.model import predict
    query = payload.query

    # use v2 as default winner for now
    stage1 = stage1_extract(query, version="v2")

    if not stage1["ready_for_prediction"]:
        return {
            "extracted_features": stage1["features"],
            "confident_fields": stage1["confident_fields"],
            "missing_fields": stage1["missing_fields"],
            "ready_for_prediction": False,
            "predicted_price": None,
            "interpretation": "",
            "message": "Missing required features. Please review and fill them in the UI.",
            "prompt_version": stage1["prompt_version"],
        }

    try:
        price = predict(stage1["features"])
    except Exception as e:
        return {
            "extracted_features": stage1["features"],
            "confident_fields": stage1["confident_fields"],
            "missing_fields": [],
            "ready_for_prediction": False,
            "predicted_price": None,
            "interpretation": "",
            "message": f"Prediction error: {str(e)}",
            "prompt_version": stage1["prompt_version"],
        }

    explanation = stage2_interpret(stage1["features"], price)

    return {
        "extracted_features": stage1["features"],
        "confident_fields": stage1["confident_fields"],
        "missing_fields": [],
        "ready_for_prediction": True,
        "predicted_price": float(price),
        "interpretation": explanation,
        "message": "Success",
        "prompt_version": stage1["prompt_version"],
    }
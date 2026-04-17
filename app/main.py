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

    # ----------------------------------------
    # CASE 1: User manually filled missing fields (from UI form)
    # ----------------------------------------
    manual_features = getattr(payload, "manual_features", None)

    if manual_features:
        features = manual_features
        ready_for_prediction = True
        missing_fields = []
        confident_fields = list(features.keys())
        prompt_version = "manual"

    else:
        # ----------------------------------------
        # CASE 2: Normal LLM extraction
        # ----------------------------------------
        stage1 = stage1_extract(query, version="v2")

        features = stage1["features"]
        ready_for_prediction = stage1["ready_for_prediction"]
        missing_fields = stage1["missing_fields"]
        confident_fields = stage1["confident_fields"]
        prompt_version = stage1["prompt_version"]

    # ----------------------------------------
    # If still missing → return to UI (form will appear)
    # ----------------------------------------
    if not ready_for_prediction:
        return {
            "extracted_features": features,
            "confident_fields": confident_fields,
            "missing_fields": missing_fields,
            "ready_for_prediction": False,
            "predicted_price": None,
            "interpretation": "",
            "message": "Please complete missing fields in the form.",
            "prompt_version": prompt_version,
        }

    # ----------------------------------------
    # Run prediction
    # ----------------------------------------
    try:
        price = predict(features)
    except Exception as e:
        return {
            "extracted_features": features,
            "confident_fields": confident_fields,
            "missing_fields": [],
            "ready_for_prediction": False,
            "predicted_price": None,
            "interpretation": "",
            "message": f"Prediction error: {str(e)}",
            "prompt_version": prompt_version,
        }

    # ----------------------------------------
    # Stage 2 explanation
    # ----------------------------------------
    explanation = stage2_interpret(features, price)

    # ----------------------------------------
    # Final response
    # ----------------------------------------
    return {
        "extracted_features": features,
        "confident_fields": confident_fields,
        "missing_fields": [],
        "ready_for_prediction": True,
        "predicted_price": float(price),
        "interpretation": explanation,
        "message": "Success",
        "prompt_version": prompt_version,
    }
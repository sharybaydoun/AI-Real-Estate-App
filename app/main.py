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
    manual_features = payload.manual_features

    # ----------------------------------------
    # CASE 1 → MANUAL INPUT
    # ----------------------------------------
    if manual_features:
        features = {}

        for k, v in manual_features.items():
            if v is None or v == "":
                features[k] = None
            else:
                features[k] = v

        missing_fields = [k for k, v in features.items() if v is None]
        ready_for_prediction = len(missing_fields) == 0
        confident_fields = [k for k, v in features.items() if v is not None]
        prompt_version = "manual"

    else:
        # ----------------------------------------
        # CASE 2 → LLM
        # ----------------------------------------
        stage1 = stage1_extract(query, version="v2")

        features = stage1["features"]
        ready_for_prediction = stage1["ready_for_prediction"]
        missing_fields = stage1["missing_fields"]
        confident_fields = stage1["confident_fields"]
        prompt_version = stage1["prompt_version"]

    # ----------------------------------------
    # STILL MISSING → RETURN
    # ----------------------------------------
    if not ready_for_prediction:
        return {
            "extracted_features": features,
            "confident_fields": confident_fields,
            "missing_fields": missing_fields,
            "ready_for_prediction": False,
            "predicted_price": None,
            "interpretation": "",
            "message": "Fill missing fields",
            "prompt_version": prompt_version,
        }

    # ----------------------------------------
    # PREDICTION
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
            "message": str(e),
            "prompt_version": prompt_version,
        }

    # ----------------------------------------
    # INTERPRETATION
    # ----------------------------------------
    explanation = stage2_interpret(features, price)

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
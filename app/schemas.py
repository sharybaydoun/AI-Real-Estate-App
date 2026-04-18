from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class QueryRequest(BaseModel):
    query: str
    manual_features: Optional[Dict[str, Any]] = None

class PredictionResponse(BaseModel):
    extracted_features: Dict[str, Any]
    confident_fields: List[str]
    missing_fields: List[str]
    ready_for_prediction: bool
    predicted_price: Optional[float]
    interpretation: str
    message: str
    confidence_score: Optional[float]
    prompt_version: str
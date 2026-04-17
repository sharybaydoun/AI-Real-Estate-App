from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3)


class FeatureExtractionResponse(BaseModel):
    features: Dict[str, Any]
    confident_fields: List[str]
    missing_fields: List[str]
    ready_for_prediction: bool
    prompt_version: str


class PredictionResponse(BaseModel):
    extracted_features: Dict[str, Any]
    confident_fields: List[str]
    missing_fields: List[str]
    ready_for_prediction: bool
    predicted_price: Optional[float]
    interpretation: str
    message: str
    prompt_version: str
import os
import json
import re
from groq import Groq

# ----------------------------------------
# Load API
# ----------------------------------------
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ----------------------------------------
# Load files
# ----------------------------------------
with open("model/features.json", "r") as f:
    FEATURES = json.load(f)

with open("model/schema.json", "r") as f:
    SCHEMA = json.load(f)

with open("model/stats.json", "r") as f:
    STATS = json.load(f)

# ----------------------------------------
# NEW: Minimum required features
# ----------------------------------------
MIN_REQUIRED_FEATURES = [
    "Gr Liv Area",
    "Overall Qual",
    "Year Built"
]

# ----------------------------------------
# Extract JSON safely
# ----------------------------------------
def _extract_json_block(text: str) -> str:
    text = text.strip()

    if "```" in text:
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]

    return text

# ----------------------------------------
# Type validation
# ----------------------------------------
def _coerce_value(field: str, value):
    spec = SCHEMA[field]
    field_type = spec["type"]

    if value is None:
        return None

    if field_type == "number":
        try:
            return float(value)
        except:
            return None

    if field_type == "string":
        value = str(value).strip()
        allowed = spec.get("allowed_values")
        if allowed and value not in allowed:
            return None
        return value

    return None

# ----------------------------------------
# UPDATED VALIDATION
# ----------------------------------------
def _validate_stage1_output(raw_features: dict, prompt_version: str):
    full_features = {}
    confident_fields = []
    missing_fields = []

    for field in FEATURES:
        value = raw_features.get(field, None)
        value = _coerce_value(field, value)

        full_features[field] = value

        if value is None:
            missing_fields.append(field)
        else:
            confident_fields.append(field)

    # ✅ NEW LOGIC
    present_important = [
        f for f in MIN_REQUIRED_FEATURES if full_features.get(f) is not None
    ]

    ready_for_prediction = len(present_important) >= 2

    confidence_score = round(len(confident_fields) / len(FEATURES), 2)

    return {
        "features": full_features,
        "confident_fields": confident_fields,
        "missing_fields": missing_fields,
        "ready_for_prediction": ready_for_prediction,
        "confidence_score": confidence_score,
        "prompt_version": prompt_version,
    }

# ----------------------------------------
# Prompt V2 (FIXED - no hallucination)
# ----------------------------------------
def _build_prompt_v2(query: str) -> str:
    return f"""
Extract structured real estate features.

Return ONLY JSON:
{{
  "features": {{
    "Gr Liv Area": null,
    "Overall Qual": null,
    "Year Built": null,
    "Total Bsmt SF": null,
    "Garage Cars": null,
    "Full Bath": null,
    "Bedroom AbvGr": null,
    "Neighborhood": null,
    "House Style": null,
    "Lot Area": null
  }}
}}

Rules:
- Do NOT guess values
- Do NOT infer quality from words like "nice", "good"
- Use null if not explicitly stated

User:
{query}
"""

# ----------------------------------------
# Call LLM
# ----------------------------------------
def _call_llm(prompt: str):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Return JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()
    return json.loads(_extract_json_block(content))

# ----------------------------------------
# Stage 1
# ----------------------------------------
def stage1_extract(query: str):
    try:
        data = _call_llm(_build_prompt_v2(query))
        return _validate_stage1_output(data.get("features", {}), "v2")

    except Exception:
        return {
            "features": {f: None for f in FEATURES},
            "confident_fields": [],
            "missing_fields": FEATURES,
            "ready_for_prediction": False,
            "confidence_score": 0,
            "prompt_version": "v2",
        }

# ----------------------------------------
# Stage 2
# ----------------------------------------
def stage2_interpret(features: dict, price: float) -> str:
    if price < STATS["typical_low"]:
        category = "below the typical market range"
    elif price > STATS["typical_high"]:
        category = "above the typical market range"
    else:
        category = "within the typical market range"

    return f"The estimated price is ${price:,.0f}, which is {category}. It is mainly influenced by size, quality, and year built."
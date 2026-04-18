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
# Minimum required features
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
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text

# ----------------------------------------
# Type validation
# ----------------------------------------
def _coerce_value(field: str, value):
    spec = SCHEMA[field]

    if value is None:
        return None

    if spec["type"] == "number":
        try:
            v = float(value)
            # sanity check
            if field == "Gr Liv Area" and (v < 300 or v > 10000):
                return None
            return v
        except:
            return None

    if spec["type"] == "string":
        value = str(value).strip()
        allowed = spec.get("allowed_values")
        if allowed and value not in allowed:
            return None
        return value

    return None

# ----------------------------------------
# Validate Stage 1
# ----------------------------------------
def _validate_stage1_output(raw_features: dict):
    full = {}
    confident = []
    missing = []

    for f in FEATURES:
        val = _coerce_value(f, raw_features.get(f))
        full[f] = val

        if val is None:
            missing.append(f)
        else:
            confident.append(f)

    important_present = [
        f for f in MIN_REQUIRED_FEATURES if full.get(f) is not None
    ]

    ready = len(important_present) >= 2
    confidence = round(len(confident) / len(FEATURES), 2)

    return {
        "features": full,
        "confident_fields": confident,
        "missing_fields": missing,
        "ready_for_prediction": ready,
        "confidence_score": confidence,
    }

# ----------------------------------------
# Prompt
# ----------------------------------------
def _build_prompt(query: str):
    return f"""
Extract real estate features.

Return JSON:
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
- Do NOT guess
- Use null if missing
- Living area must be realistic (300–10000 sqft)
- Do NOT infer quality from words like "nice"

User:
{query}
"""

# ----------------------------------------
# Call LLM
# ----------------------------------------
def _call_llm(prompt: str):
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Return JSON only"},
            {"role": "user", "content": prompt},
        ],
        temperature=0
    )

    content = res.choices[0].message.content
    return json.loads(_extract_json_block(content))

# ----------------------------------------
# Stage 1
# ----------------------------------------
def stage1_extract(query: str):
    try:
        data = _call_llm(_build_prompt(query))
        return _validate_stage1_output(data.get("features", {}))
    except:
        return {
            "features": {f: None for f in FEATURES},
            "confident_fields": [],
            "missing_fields": FEATURES,
            "ready_for_prediction": False,
            "confidence_score": 0,
        }

# ----------------------------------------
# Stage 2 (FIXED LLM)
# ----------------------------------------
def stage2_interpret(features: dict, price: float) -> str:

    prompt = f"""
You are a friendly real estate assistant.

Features:
{features}

Price: {price}

Market:
- Typical: {STATS["typical_low"]} to {STATS["typical_high"]}
- Median: {STATS["median_price"]}

Instructions:
- Write 2 to 3 short paragraphs
- Use clear spacing
- Keep sentences readable
- Mention 2–3 key features
- If missing info exists, mention it

No JSON.
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Explain simply."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6   # ✅ FIXED
        )

        return res.choices[0].message.content.strip()

    except:
        return "Explanation unavailable."
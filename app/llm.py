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
# Extract JSON safely from LLM
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
# Type + schema validation
# ----------------------------------------
def _coerce_value(field: str, value):
    spec = SCHEMA[field]
    field_type = spec["type"]

    if value is None:
        return None

    if field_type == "number":
        try:
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    return None
            return float(value)
        except Exception:
            return None

    if field_type == "string":
        value = str(value).strip()
        if value == "":
            return None

        allowed = spec.get("allowed_values")
        if allowed:
            if value not in allowed:
                return None

        return value

    return None


# ----------------------------------------
# Validate Stage 1 output
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

    return {
        "features": full_features,
        "confident_fields": confident_fields,
        "missing_fields": missing_fields,
        "ready_for_prediction": len(missing_fields) == 0,
        "prompt_version": prompt_version,
    }


# ----------------------------------------
# Prompt V1
# ----------------------------------------
def _build_prompt_v1(query: str) -> str:
    return f"""
You extract structured real-estate features from a user query.

Return ONLY valid JSON with this exact structure:
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
- Output JSON only
- Use null for anything not explicitly stated
- Do not guess missing numbers
- Use exact category names only when clearly stated
- Valid Neighborhood values: {SCHEMA["Neighborhood"]["allowed_values"]}
- Valid House Style values: {SCHEMA["House Style"]["allowed_values"]}
- Numeric fields must be numbers not strings

User query:
{query}
"""


# ----------------------------------------
# Prompt V2 (better)
# ----------------------------------------
def _build_prompt_v2(query: str) -> str:
    return f"""
You are an intelligent real estate extraction engine.

Extract property features from the user query.

Return ONLY valid JSON:
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
- If a range is given (e.g. 1800–2200 sqft) → take the AVERAGE
- If multiple options (e.g. 3 or 4 bedrooms) → take the LOWER value
- If vague quality ("good", "nice", "modern") → map to:
    good → 6
    very good → 7
    excellent → 8+
- If "after 2000" → use 2000
- If garage mentioned → Garage Cars = 2
- If basement not mentioned → leave null
- If neighborhood is vague → leave null
- Do NOT leave obvious values as null

Return JSON only.

User query:
{query}
"""

# ----------------------------------------
# Call LLM
# ----------------------------------------
def _call_llm(prompt: str) -> dict:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()
    json_text = _extract_json_block(content)
    return json.loads(json_text)


# ----------------------------------------
# Stage 1
# ----------------------------------------
def stage1_extract(query: str, version: str = "v2") -> dict:
    prompt = _build_prompt_v1(query) if version == "v1" else _build_prompt_v2(query)

    try:
        data = _call_llm(prompt)
        raw_features = data.get("features", {})
        return _validate_stage1_output(raw_features, version)

    except Exception:
        return {
            "features": {f: None for f in FEATURES},
            "confident_fields": [],
            "missing_fields": FEATURES,
            "ready_for_prediction": False,
            "prompt_version": version,
        }


# ----------------------------------------
# Stage 2 (FIXED VERSION)
# ----------------------------------------
def stage2_interpret(features: dict, price: float) -> str:

    # ✅ Correct price category
    if price < STATS["typical_low"]:
        category = "below the typical market range"
    elif price > STATS["typical_high"]:
        category = "above the typical market range"
    else:
        category = "within the typical market range"

    prompt = f"""
You are a friendly real estate assistant.

A house has these features:
{features}

Its predicted price is: {price}

Market reference:
- Typical range: {STATS["typical_low"]} to {STATS["typical_high"]}
- Median price: {STATS["median_price"]}

The price is {category}.

Explain to a normal user:
- Why this price makes sense
- Mention 2–3 important features only
- Keep it simple and natural

Rules:
- No technical terms
- No JSON format
- Be concise and friendly
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Explain house prices simply."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except Exception:
        return "The price was generated successfully, but explanation is unavailable right now."
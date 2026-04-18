import streamlit as st
import requests

# ----------------------------------------
# Config
# ----------------------------------------
st.set_page_config(
    page_title="AI Real Estate Agent",
    page_icon="🏡",
    layout="wide"
)

API_URL = "https://ai-real-estate-app-production.up.railway.app/predict"

# ----------------------------------------
# Helpers
# ----------------------------------------
rename_map = {
    "Gr Liv Area": "Living Area (sqft)",
    "Overall Qual": "Quality (1–10)",
    "Year Built": "Year Built",
    "Total Bsmt SF": "Basement Size (sqft)",
    "Garage Cars": "Garage (cars)",
    "Full Bath": "Bathrooms",
    "Bedroom AbvGr": "Bedrooms",
    "Neighborhood": "Neighborhood",
    "House Style": "House Style",
    "Lot Area": "Lot Size (sqft)"
}

important_fields = ["Gr Liv Area", "Overall Qual", "Year Built"]


def pretty_label(field_name: str) -> str:
    return rename_map.get(field_name, field_name)


def field_is_important(field_name: str) -> bool:
    return field_name in important_fields


# ----------------------------------------
# Title / Intro
# ----------------------------------------
st.title("🏡 AI Real Estate Agent")
st.write("Describe a house in plain English and get a price estimate with a simple explanation.")

st.info(
    "For the best estimate, try to include at least living area, quality, and year built. "
    "If some details are missing, the app can still try to predict when enough key information is available."
)

# ----------------------------------------
# Input
# ----------------------------------------
query = st.text_area(
    "Describe the property",
    placeholder="Example: 3-bedroom house, 2000 sqft, built in 2010, with garage, in NAmes",
    height=130
)

# ----------------------------------------
# Analyze
# ----------------------------------------
if st.button("🚀 Analyze Property", use_container_width=True):
    if not query.strip():
        st.warning("Please enter a property description first.")
    else:
        try:
            with st.spinner("Analyzing property details..."):
                res = requests.post(API_URL, json={"query": query}, timeout=60)

            if res.status_code == 200:
                st.session_state.data = res.json()
            else:
                st.error(res.text)

        except Exception as e:
            st.error(f"API error: {e}")

# ----------------------------------------
# Display
# ----------------------------------------
if "data" in st.session_state:
    data = st.session_state.data
    features = data.get("extracted_features", {})
    missing_fields = data.get("missing_fields", [])
    ready = data.get("ready_for_prediction", False)
    confidence_score = data.get("confidence_score", 0.0) or 0.0

    st.divider()

    col1, col2 = st.columns([1.1, 0.9])

    # ----------------------------------------
    # LEFT PANEL
    # ----------------------------------------
    with col1:
        st.subheader("📊 Extracted Property Details")

        if not features:
            st.warning("No property details were extracted.")
        else:
            for key, value in features.items():
                label = pretty_label(key)
                badge = "⭐ " if field_is_important(key) else ""

                if value is None:
                    st.markdown(f"❌ **{badge}{label}**: Not provided")
                else:
                    st.markdown(f"✅ **{badge}{label}**: {value}")

        # ----------------------------------------
        # Missing Inputs Form
        # ----------------------------------------
        if missing_fields:
            st.divider()
            st.markdown("### ✏️ Add More Details")

            important_missing = [f for f in missing_fields if f in important_fields]
            other_missing = [f for f in missing_fields if f not in important_fields]

            if important_missing:
                st.warning(
                    "Some key details are missing: "
                    + ", ".join(pretty_label(f) for f in important_missing)
                )
            elif ready:
                st.info(
                    "A prediction is available, but adding the remaining details may improve the estimate."
                )
            else:
                st.info("You can complete the remaining details below.")

            user_inputs = {}

            for field in missing_fields:
                label = pretty_label(field)

                if field == "Neighborhood":
                    user_inputs[field] = st.selectbox(
                        label,
                        ["NAmes", "CollgCr", "OldTown", "Edwards", "Somerst"],
                        key=f"input_{field}"
                    )

                elif field == "House Style":
                    user_inputs[field] = st.selectbox(
                        label,
                        ["1Story", "2Story", "1.5Fin"],
                        key=f"input_{field}"
                    )

                elif field == "Bedroom AbvGr":
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0,
                        max_value=10,
                        step=1,
                        key=f"input_{field}"
                    )

                elif field == "Full Bath":
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0,
                        max_value=5,
                        step=1,
                        key=f"input_{field}"
                    )

                elif field == "Garage Cars":
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0,
                        max_value=5,
                        step=1,
                        key=f"input_{field}"
                    )

                elif field == "Year Built":
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=1900,
                        max_value=2025,
                        step=1,
                        key=f"input_{field}"
                    )

                elif field == "Overall Qual":
                    user_inputs[field] = st.slider(
                        label,
                        min_value=1,
                        max_value=10,
                        value=5,
                        key=f"input_{field}"
                    )

                elif field in ["Gr Liv Area", "Total Bsmt SF"]:
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0,
                        step=100,
                        key=f"input_{field}"
                    )

                elif field == "Lot Area":
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0,
                        step=500,
                        key=f"input_{field}"
                    )

                else:
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0.0,
                        step=10.0,
                        key=f"input_{field}"
                    )

            button_text = "🔄 Update Prediction" if ready else "💰 Get Price"

            if st.button(button_text, use_container_width=True):
                completed = features.copy()

                for k, v in user_inputs.items():
                    completed[k] = v

                try:
                    with st.spinner("Updating prediction..."):
                        res = requests.post(
                            API_URL,
                            json={
                                "query": query,
                                "manual_features": completed
                            },
                            timeout=60
                        )

                    if res.status_code == 200:
                        st.session_state.data = res.json()
                        st.rerun()
                    else:
                        st.error(res.text)

                except Exception as e:
                    st.error(f"Error: {e}")

    # ----------------------------------------
    # RIGHT PANEL
    # ----------------------------------------
    with col2:
        st.subheader("📈 Prediction Summary")

        confidence_percent = int(confidence_score * 100)

        st.markdown("**Extraction Confidence**")
        st.progress(confidence_score)
        st.caption(f"{confidence_percent}% of tracked fields are currently available")

        present_important = [
            f for f in important_fields if features.get(f) is not None
        ]

        st.markdown("**Key Inputs Status**")
        for f in important_fields:
            if f in present_important:
                st.markdown(f"✅ {pretty_label(f)}")
            else:
                st.markdown(f"❌ {pretty_label(f)}")

        st.divider()

        if ready:
            st.subheader("💰 Estimated Price")
            st.metric("Price", f"${data['predicted_price']:,.0f}")

            if missing_fields:
                st.warning(
                    "This estimate was generated using the available information. "
                    "Adding more details may improve accuracy."
                )
            else:
                st.success("All tracked details are available for this estimate.")

            st.subheader("🧠 Explanation")
            st.markdown(data["interpretation"])

            if data.get("message"):
                st.caption(data["message"])

        else:
            st.info(
                "Not enough key information to generate a prediction yet. "
                "Please provide at least two of these: living area, quality, year built."
            )

            if data.get("message"):
                st.caption(data["message"])
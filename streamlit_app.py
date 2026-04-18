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


def pretty_label(field_name: str):
    return rename_map.get(field_name, field_name)


def field_is_important(field_name: str):
    return field_name in important_fields


# ----------------------------------------
# Title
# ----------------------------------------
st.title("🏡 AI Real Estate Agent")
st.write("Describe a house and get a smart price estimate.")

st.info(
    "For best results include: Living Area, Quality, and Year Built.\n"
    "The app can still predict if enough key info is available."
)

# ----------------------------------------
# Input
# ----------------------------------------
query = st.text_area(
    "Describe the property",
    placeholder="Example: 3-bedroom house, 2000 sqft, built in 2010, with garage",
    height=130
)

# ----------------------------------------
# Analyze
# ----------------------------------------
if st.button("🚀 Analyze Property", use_container_width=True):
    if not query.strip():
        st.warning("Please enter a description.")
    else:
        try:
            res = requests.post(API_URL, json={"query": query})
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
    confidence_score = data.get("confidence_score", 0.0)

    st.divider()
    col1, col2 = st.columns([1.1, 0.9])

    # ----------------------------------------
    # LEFT PANEL
    # ----------------------------------------
    with col1:
        st.subheader("📊 Extracted Details")

        for key, value in features.items():
            label = pretty_label(key)
            badge = "⭐ " if field_is_important(key) else ""

            if value is None:
                st.markdown(f"❌ **{badge}{label}**: Not provided")
            else:
                st.markdown(f"✅ **{badge}{label}**: {value}")

        # ----------------------------------------
        # Missing Inputs
        # ----------------------------------------
        if missing_fields:
            st.divider()
            st.subheader("✏️ Add Missing Details")

            user_inputs = {}

            for field in missing_fields:
                label = pretty_label(field)

                # ----------------------------
                # CATEGORICAL
                # ----------------------------
                if field == "Neighborhood":
                    val = st.selectbox(
                        label,
                        ["", "NAmes", "CollgCr", "OldTown", "Edwards", "Somerst"],
                        key=f"input_{field}"
                    )
                    user_inputs[field] = val if val != "" else None

                elif field == "House Style":
                    val = st.selectbox(
                        label,
                        ["", "1Story", "2Story", "1.5Fin"],
                        key=f"input_{field}"
                    )
                    user_inputs[field] = val if val != "" else None

                # ----------------------------
                # INTEGER FIELDS
                # ----------------------------
                elif field in ["Bedroom AbvGr", "Full Bath", "Garage Cars"]:
                    val = st.number_input(
                        label,
                        min_value=0,
                        step=1,
                        value=None,
                        placeholder="Enter value",
                        key=f"input_{field}"
                    )
                    user_inputs[field] = val

                # ----------------------------
                # YEAR
                # ----------------------------
                elif field == "Year Built":
                    val = st.number_input(
                        label,
                        min_value=1900,
                        max_value=2025,
                        step=1,
                        value=None,
                        placeholder="Enter year",
                        key=f"input_{field}"
                    )
                    user_inputs[field] = val

                # ----------------------------
                # QUALITY
                # ----------------------------
                elif field == "Overall Qual":
                    val = st.slider(
                        label,
                        min_value=1,
                        max_value=10,
                        value=5,
                        key=f"input_{field}"
                    )
                    user_inputs[field] = val

                # ----------------------------
                # CONTINUOUS
                # ----------------------------
                elif field in ["Gr Liv Area", "Total Bsmt SF"]:
                    val = st.number_input(
                        label,
                        min_value=0,
                        step=100,
                        value=None,
                        placeholder="Enter sqft",
                        key=f"input_{field}"
                    )
                    user_inputs[field] = val

                elif field == "Lot Area":
                    val = st.number_input(
                        label,
                        min_value=0,
                        step=500,
                        value=None,
                        placeholder="Enter lot size",
                        key=f"input_{field}"
                    )
                    user_inputs[field] = val

                else:
                    val = st.number_input(
                        label,
                        value=None,
                        key=f"input_{field}"
                    )
                    user_inputs[field] = val

            # ----------------------------------------
            # BUTTON
            # ----------------------------------------
            if st.button("💰 Get / Update Price", use_container_width=True):
                completed = features.copy()

                for k, v in user_inputs.items():
                    if v is not None:
                        completed[k] = v

                try:
                    res = requests.post(
                        API_URL,
                        json={
                            "query": query,
                            "manual_features": completed
                        }
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
        st.subheader("📈 Prediction")

        st.progress(confidence_score)
        st.caption(f"{int(confidence_score*100)}% data completeness")

        st.divider()

        if ready:
            st.metric("💰 Price", f"${data['predicted_price']:,.0f}")

            st.subheader("🧠 Explanation")
            st.markdown(data["interpretation"])

        else:
            st.info("Not enough key info to predict yet.")
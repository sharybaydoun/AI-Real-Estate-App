import streamlit as st
import requests
import pandas as pd

# ----------------------------------------
# Config
# ----------------------------------------
st.set_page_config(page_title="AI Real Estate Agent", page_icon="🏡", layout="wide")

API_URL = "https://ai-real-estate-agent.up.railway.app/predict"
# ----------------------------------------
# Title
# ----------------------------------------
st.title("🏡 AI Real Estate Agent")
st.write("Describe a house → get price + explanation")

# ----------------------------------------
# Input
# ----------------------------------------
query = st.text_area(
    "Describe the property",
    placeholder="Example: 3-bedroom house, 2000 sqft, built in 2010, with garage, in NAmes",
)

# ----------------------------------------
# Analyze button
# ----------------------------------------
if st.button("🚀 Analyze"):
    with st.spinner("Analyzing..."):
        try:
            res = requests.post(API_URL, json={"query": query})

            if res.status_code == 200:
                st.session_state.data = res.json()
            else:
                st.error(res.text)

        except Exception as e:
            st.error(f"API error: {e}")

# ----------------------------------------
# Display results
# ----------------------------------------
if "data" in st.session_state:
    data = st.session_state.data

    st.divider()
    col1, col2 = st.columns(2)

    # ----------------------------------------
    # LEFT → FEATURES
    # ----------------------------------------
    with col1:
        st.subheader("📊 Property Details")

        rename_map = {
            "Gr Liv Area": "Living Area (sqft)",
            "Overall Qual": "Quality (1–10)",
            "Year Built": "Year Built",
            "Total Bsmt SF": "Basement Size",
            "Garage Cars": "Garage",
            "Full Bath": "Bathrooms",
            "Bedroom AbvGr": "Bedrooms",
            "Neighborhood": "Neighborhood",
            "House Style": "House Style",
            "Lot Area": "Lot Size"
        }

        features = data["extracted_features"]

        # CLEAN DISPLAY
        for key, value in features.items():
            label = rename_map.get(key, key)

            if value is None:
                st.markdown(f"❌ **{label}**: Not provided")
            else:
                st.markdown(f"✅ **{label}**: {value}")

        # ----------------------------------------
        # FORM FOR MISSING
        # ----------------------------------------
        if data["missing_fields"]:
            st.divider()
            st.warning("Please complete missing details")

            user_inputs = {}

            for field in data["missing_fields"]:
                label = rename_map.get(field, field)

                if field == "Neighborhood":
                    user_inputs[field] = st.selectbox(
                        label,
                        ["NAmes", "CollgCr", "OldTown", "Edwards", "Somerst"]
                    )

                elif field == "House Style":
                    user_inputs[field] = st.selectbox(
                        label,
                        ["1Story", "2Story", "1.5Fin"]
                    )

                else:
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=1.0,
                        step=1.0
                    )

            if st.button("💰 Get Price"):
                completed = features.copy()

                for k, v in user_inputs.items():
                    completed[k] = v

                res = requests.post(API_URL, json={
                    "query": query,
                    "manual_features": completed
                })

                if res.status_code == 200:
                    st.session_state.data = res.json()
                    st.rerun()
                else:
                    st.error(res.text)

    # ----------------------------------------
    # RIGHT → RESULT
    # ----------------------------------------
    with col2:
        if data["ready_for_prediction"]:
            st.subheader("💰 Estimated Price")

            st.metric("Price", f"${data['predicted_price']:,.0f}")

            st.subheader("🧠 Explanation")

            st.markdown(f"""
            <div style="
                background-color:#1e3a5f;
                padding:18px;
                border-radius:12px;
                color:white;
                font-size:16px;
                line-height:1.6;
            ">
            {data["interpretation"]}
            </div>
            """, unsafe_allow_html=True)

        else:
            st.info("Fill missing details to get prediction.")
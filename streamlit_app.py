import streamlit as st
import requests
import pandas as pd

# ----------------------------------------
# Page config
# ----------------------------------------
st.set_page_config(
    page_title="AI Real Estate Agent",
    page_icon="🏡",
    layout="wide"
)

API_URL = "https://ai-real-estate-app-production.up.railway.app/predict"
# ----------------------------------------
# Title
# ----------------------------------------
st.markdown("""
# 🏡 AI Real Estate Agent
Describe a house and get an instant price estimate with explanation.
""")

# ----------------------------------------
# Input
# ----------------------------------------
query = st.text_area(
    "Describe the property",
    placeholder="Example: 3-bedroom house, 2000 sqft, built in 2010, with garage, in NAmes",
    height=120
)

# ----------------------------------------
# Button
# ----------------------------------------
if st.button("🚀 Analyze Property"):
    with st.spinner("Analyzing..."):
        try:
            res = requests.post(API_URL, json={"query": query})
            data = res.json()
            st.session_state.data = data
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
    # LEFT SIDE → FEATURES
    # ----------------------------------------
    with col1:
        st.subheader("📊 Property Details")

        features = data["extracted_features"]

        df_features = pd.DataFrame({
            "Feature": features.keys(),
            "Value": features.values()
        })

        # ✅ Make feature names human-friendly
        rename_map = {
            "Gr Liv Area": "Living Area (sqft)",
            "Overall Qual": "Quality (1–10)",
            "Year Built": "Year Built",
            "Total Bsmt SF": "Basement Size (sqft)",
            "Garage Cars": "Garage Capacity",
            "Full Bath": "Bathrooms",
            "Bedroom AbvGr": "Bedrooms",
            "Neighborhood": "Neighborhood",
            "House Style": "House Style",
            "Lot Area": "Lot Size (sqft)"
        }

        df_features["Feature"] = df_features["Feature"].map(rename_map).fillna(df_features["Feature"])

        for _, row in df_features.iterrows():
           value = row["Value"]

        if pd.isna(value):
          st.markdown(f"❌ **{row['Feature']}**: _Not provided_")
        else:
          st.markdown(f"✅ **{row['Feature']}**: {value}")

        if data["missing_fields"]:
           st.warning("⚠️ Some details are missing. Please complete them below:")

    user_inputs = {}

    for field in data["missing_fields"]:
        label = rename_map.get(field, field)

        if field in ["Neighborhood", "House Style"]:
            user_inputs[field] = st.text_input(f"{label}")
        else:
            user_inputs[field] = st.number_input(f"{label}", value=0.0)

    if st.button("✅ Submit Missing Info"):
        completed_features = {**data["extracted_features"], **user_inputs}

        res = requests.post(API_URL, json={
            "query": query,
            "manual_features": completed_features
        })

        st.session_state.data = res.json()
        st.rerun()

    # ----------------------------------------
    # RIGHT SIDE → PREDICTION
    # ----------------------------------------
    with col2:
        if data["ready_for_prediction"]:
            st.subheader("💰 Estimated Price")

            st.metric(
                label="Price",
                value=f"${data['predicted_price']:,.0f}"
            )

            st.subheader("🧠 Why this price?")

            # ✅ FIXED explanation rendering (NO broken text)
            st.markdown(f"""
            <div style="
                background-color:#1e3a5f;
                padding:18px;
                border-radius:12px;
                color:white;
                font-size:16px;
                line-height:1.6;
                word-wrap:break-word;
            ">
            {data["interpretation"]}
            </div>
            """, unsafe_allow_html=True)

        else:
            st.info("Complete missing features to get prediction.")
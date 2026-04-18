import streamlit as st
import requests

st.set_page_config(page_title="AI Real Estate Agent", layout="wide")

API_URL = "https://ai-real-estate-app-production.up.railway.app/predict"

rename_map = {
    "Gr Liv Area": "Living Area (sqft)",
    "Overall Qual": "Quality (1–10)",
    "Year Built": "Year Built",
    "Total Bsmt SF": "Basement",
    "Garage Cars": "Garage",
    "Full Bath": "Bathrooms",
    "Bedroom AbvGr": "Bedrooms",
    "Neighborhood": "Neighborhood",
    "House Style": "House Style",
    "Lot Area": "Lot Size"
}

important = ["Gr Liv Area", "Overall Qual", "Year Built"]

st.title("🏡 AI Real Estate Agent")

query = st.text_area("Describe property")

if st.button("Analyze"):
    res = requests.post(API_URL, json={"query": query})
    st.session_state.data = res.json()

if "data" in st.session_state:

    data = st.session_state.data
    features = data["extracted_features"]

    col1, col2 = st.columns(2)

    # LEFT
    with col1:
        st.subheader("Details")

        for k, v in features.items():
            label = rename_map.get(k, k)
            if v is None:
                st.write(f"❌ {label}")
            else:
                st.write(f"✅ {label}: {v}")

        # --------------------------
        # INPUT FIXED (NO + BUG)
        # --------------------------
        if data["missing_fields"]:

            st.subheader("Add missing info")

            user_inputs = {}

            for field in data["missing_fields"]:
                label = rename_map.get(field, field)

                val = st.text_input(label, key=field)

                if val.strip() == "":
                    user_inputs[field] = None
                else:
                    try:
                        user_inputs[field] = float(val)
                    except:
                        user_inputs[field] = val

            if st.button("Update"):
                updated = features.copy()
                updated.update(user_inputs)

                res = requests.post(API_URL, json={
                    "query": query,
                    "manual_features": updated
                })

                st.session_state.data = res.json()
                st.rerun()

    # RIGHT
    with col2:
        st.subheader("Prediction")

        if data["ready_for_prediction"]:
            st.metric("Price", f"${data['predicted_price']:,.0f}")

            st.subheader("Explanation")

            # FIX spacing rendering
            explanation = data["interpretation"]
            explanation = explanation.replace("\n", "\n\n")

            st.markdown(explanation)

        else:
            st.warning("Need more key details")
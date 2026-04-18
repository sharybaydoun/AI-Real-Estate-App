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
# Analyze
# ----------------------------------------
if st.button("🚀 Analyze Property"):
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

    st.divider()
    col1, col2 = st.columns(2)

    # ----------------------------------------
    # LEFT PANEL
    # ----------------------------------------
    with col1:
        st.subheader("📊 Property Details")

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

        features = data["extracted_features"]

        for key, value in features.items():
            label = rename_map.get(key, key)

            if value is None:
                st.markdown(f"❌ **{label}**: Not provided")
            else:
                st.markdown(f"✅ **{label}**: {value}")

        # ----------------------------------------
        # Missing Inputs Form
        # ----------------------------------------
        if data["missing_fields"]:
            st.divider()
            st.markdown("### ✏️ Complete Missing Information")
            st.warning("Some important details are missing. Please fill them below.")

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

                elif field == "Bedroom AbvGr":
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0,
                        max_value=10,
                        step=1
                    )

                elif field == "Full Bath":
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0,
                        max_value=5,
                        step=1
                    )

                elif field == "Garage Cars":
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0,
                        max_value=5,
                        step=1
                    )

                elif field == "Year Built":
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=1900,
                        max_value=2025,
                        step=1
                    )

                elif field == "Overall Qual":
                    user_inputs[field] = st.slider(
                        label,
                        min_value=1,
                        max_value=10,
                        value=5
                    )

                elif field in ["Gr Liv Area", "Total Bsmt SF"]:
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0,
                        step=100
                    )

                elif field == "Lot Area":
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0,
                        step=500
                    )

                else:
                    user_inputs[field] = st.number_input(
                        label,
                        min_value=0.0,
                        step=10.0
                    )

            if st.button("💰 Get Price"):
                completed = features.copy()

                for k, v in user_inputs.items():
                    completed[k] = v

                try:
                    res = requests.post(API_URL, json={
                        "query": query,
                        "manual_features": completed
                    })

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
        if data["ready_for_prediction"]:
            st.subheader("💰 Estimated Price")
            st.metric("Price", f"${data['predicted_price']:,.0f}")

            st.subheader("🧠 Explanation")
            st.markdown(data["interpretation"])

        else:
            st.info("Fill missing details to get prediction.")
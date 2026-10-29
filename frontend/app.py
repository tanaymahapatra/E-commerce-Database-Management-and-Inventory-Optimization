import streamlit as st
import requests

# FastAPI backend URL
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Inventory Recommendations", page_icon="📦", layout="wide"
)

st.title("📦 Inventory Optimization")
st.write("Get demand forecasts and restocking recommendations.")


# 1. Product and warehouse selection
with st.form("recommendation_form"):

    col1, col2 = st.columns(2)

    with col1:
        product_id = st.number_input("Product ID", min_value=1, max_value=48, step=1, value=1)

    with col2:
        warehouse_id = st.number_input(
            "Warehouse ID", min_value=10101, step=1, value=10101
        )

    submitted = st.form_submit_button("Get Recommendations", type="primary")


# 2. Fetch recommendations from FastAPI
if submitted:
    try:
        response = requests.get(
            f"{API_URL}/recommendations",
            params={"product_id": product_id, "warehouse_id": warehouse_id},
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        recommendations = data["recommendations"]

        # Clean any T00:00:00 timestamp format to pure date
        for r in recommendations:
            if "forecast_date" in r and r["forecast_date"]:
                r["forecast_date"] = str(r["forecast_date"]).split("T")[0]

        # 3. Display results
        if not recommendations:
            st.warning("No recommendations found.")

        else:
            st.success(f"Found {data['total_records']} recommendations")

            latest = recommendations[0]

            st.subheader("Latest Recommendation")
            st.write("Forecast Date:", latest["forecast_date"])

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Predicted Demand", latest["predicted_demand"])

            col2.metric("Safety Stock", latest["safety_stock"])

            col3.metric("Reorder Quantity", latest["reorder_qty"])

            col4.metric("Status", latest["status"])

            st.subheader("Recommendation History")

            st.dataframe(recommendations, use_container_width=True, hide_index=True)

    except requests.exceptions.RequestException as e:
        st.error("Unable to fetch recommendations from FastAPI.")
        st.caption(str(e))

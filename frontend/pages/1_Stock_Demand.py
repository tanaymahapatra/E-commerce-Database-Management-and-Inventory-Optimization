import requests
import pandas as pd
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Warehouse Stock & Demand", page_icon="📊", layout="wide")

# 1. Check login
token = st.session_state.get("access_token")

if not token:
    st.warning("Please login from the Recommendation page first.")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}


# 2. Identify current user
try:
    response = requests.get(f"{API_URL}/auth/me", headers=headers, timeout=10)

    if response.status_code == 401:
        st.session_state.access_token = None
        st.warning("Session expired. Please login again.")
        st.stop()

    response.raise_for_status()
    user = response.json()

except requests.exceptions.RequestException:
    st.error("Unable to connect to FastAPI.")
    st.stop()


st.title("📊 Warehouse Stock & Demand")


# 3. Select warehouse according to role
if user["role"] == "admin":

    warehouse_id = st.number_input("Warehouse ID", min_value=1, step=1, value=1)

elif user["role"] == "manager":

    warehouse_id = user["user_id"]

    st.info(f"Your assigned Warehouse ID: {warehouse_id}")

else:
    st.error("You do not have access to this page.")
    st.stop()


# 4. Fetch stock and demand
if st.button("View Stock & Demand", type="primary"):

    try:
        response = requests.get(
            f"{API_URL}/stock-demand/{warehouse_id}", headers=headers, timeout=30
        )

        if response.status_code == 401:
            st.session_state.access_token = None
            st.warning("Session expired. Please login again.")
            st.stop()

        if response.status_code == 403:
            st.error("Access denied for this warehouse.")
            st.stop()

        if response.status_code == 404:
            st.warning("Warehouse not found.")
            st.stop()

        response.raise_for_status()
        data = response.json()

        st.subheader(data["warehouse_location"])

        col1, col2 = st.columns(2)

        col1.metric("Total Products", data["total_products"])

        col2.metric("Total Stored Stock", data["total_stock"])

        products = data["products"]

        # 5. Show product-wise stock and demand
        if products:

            df = pd.DataFrame(products)

            df["forecast_date"] = df["forecast_date"].apply(
                lambda value: value[:10] if value else "No forecast"
            )

            df = df.rename(
                columns={
                    "product_id": "Product ID",
                    "product_name": "Product Name",
                    "stock_quantity": "Stored Stock",
                    "predicted_demand": "Predicted Demand",
                    "forecast_date": "Forecast Date",
                }
            )

            st.dataframe(df, use_container_width=True, hide_index=True)

        else:
            st.warning("No inventory records found.")

    except requests.exceptions.RequestException as error:
        st.error("Unable to retrieve warehouse data.")
        st.caption(str(error))

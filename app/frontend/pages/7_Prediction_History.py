from datetime import date, timedelta
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

from utils.api_client import APIClient, APIError
from utils.page_helpers import setup_authenticated_page
from utils.ui_theme import render_empty_state

setup_authenticated_page(
    "Prediction History",
    "Prediction History",
    "Review forecasts recorded by the active model and compare them with actual outcomes.",
    "Forecast workspace",
)

try:
    products = APIClient.get_products(limit=200) or []
    model_runs = APIClient.get_model_runs(limit=200) or []
except Exception as error:
    st.error(f"Could not load history filters: {error}")
    products = []
    model_runs = []
product_by_id = {product["product_id"]: product for product in products}
versions = sorted({run["model_version"] for run in model_runs if run.get("model_version")}, reverse=True)

filter_cols = st.columns([1.3, 1, 1, 1, 1])
with filter_cols[0]:
    search = st.text_input("Search", placeholder="Product or model")
with filter_cols[1]:
    product_id = st.selectbox("Product", [None] + list(product_by_id), format_func=lambda key: "All products" if key is None else product_by_id[key]["product_name"])
with filter_cols[2]:
    start_date = st.date_input("Forecast from", value=date.today() - timedelta(days=30))
with filter_cols[3]:
    end_date = st.date_input("Forecast to", value=date.today() + timedelta(days=90))
with filter_cols[4]:
    model_version = st.selectbox("Model version", ["All versions"] + versions)

try:
    predictions = APIClient.get_predictions(
        product_id=product_id,
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None,
        model_version=None if model_version == "All versions" else model_version,
        search=search.strip() or None,
        limit=200,
    ) or []
except APIError as error:
    st.error(error.message)
    predictions = []
except Exception as error:
    st.error(f"Could not load prediction history: {error}")
    predictions = []

if predictions:
    frame = pd.DataFrame(predictions)
    frame["product"] = frame["product_id"].map(lambda key: product_by_id.get(key, {}).get("product_name", f"Product #{key}"))
    frame["forecast_date"] = pd.to_datetime(frame["forecast_date"], errors="coerce")
    frame["predicted_at"] = pd.to_datetime(frame["predicted_at"], errors="coerce")
    metric_cols = st.columns(3)
    metric_cols[0].metric("Forecasts shown", len(frame))
    metric_cols[1].metric("Products", frame["product_id"].nunique())
    metric_cols[2].metric("Model versions", frame["model_version"].nunique())

    chart = px.line(
        frame.sort_values("forecast_date"),
        x="forecast_date",
        y="predicted_quantity",
        color="product",
        markers=True,
        labels={"forecast_date": "Forecast date", "predicted_quantity": "Predicted quantity", "product": "Product"},
    )
    chart.update_layout(template="plotly_white", height=340, margin={"l": 12, "r": 12, "t": 20, "b": 8})
    st.plotly_chart(chart, use_container_width=True)

    display = frame[["prediction_id", "product", "forecast_date", "horizon_days", "predicted_quantity", "actual_quantity", "model_name", "model_version", "predicted_at"]].copy()
    display.columns = ["ID", "Product", "Forecast date", "Horizon (days)", "Predicted quantity", "Actual quantity", "Model", "Version", "Requested at"]
    st.dataframe(display, use_container_width=True, hide_index=True, column_config={
        "Forecast date": st.column_config.DateColumn(format="YYYY-MM-DD"),
        "Requested at": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm"),
        "Predicted quantity": st.column_config.NumberColumn(format="%.2f"),
        "Actual quantity": st.column_config.NumberColumn(format="%.2f"),
    })
else:
    render_empty_state("No predictions found", "Forecasts appear here after a successful request. Date and product filters use saved API history.")

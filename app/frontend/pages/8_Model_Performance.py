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

user = setup_authenticated_page(
    "Model Performance",
    "Model Performance",
    "Inspect real evaluation results, training history, and active model status.",
    "Forecast workspace",
)
is_admin = str(user.get("role", "")).lower() == "admin"

try:
    active_model = APIClient.get_active_model()
    model_runs = APIClient.get_model_runs(limit=200) or []
except Exception as error:
    st.error(f"Could not load model performance: {error}")
    active_model = None
    model_runs = []

if active_model:
    st.markdown("#### Active model")
    status_cols = st.columns(4)
    status_cols[0].metric("Model", active_model["model_name"])
    status_cols[1].metric("Version", active_model["model_version"])
    status_cols[2].metric("Training records", f"{active_model['training_records']:,}")
    status_cols[3].metric("Trained at", active_model["trained_at"][:19].replace("T", " "))
    metric_cols = st.columns(3)
    metric_cols[0].metric("MAE", f"{active_model['mae']:.4f}" if active_model.get("mae") is not None else "Unavailable", help="Mean Absolute Error on chronological holdout")
    metric_cols[1].metric("RMSE", f"{active_model['rmse']:.4f}" if active_model.get("rmse") is not None else "Unavailable", help="Root Mean Squared Error on chronological holdout")
    metric_cols[2].metric("R²", f"{active_model['r2']:.4f}" if active_model.get("r2") is not None else "Unavailable", help="Coefficient of determination on chronological holdout")
    st.caption(f"Target: {active_model['prediction_target']} · Status: Active · Artifact: {active_model.get('artifact_path') or 'path unavailable'}")
else:
    render_empty_state("No active model", "A successful scheduled or Admin-triggered training run is required before forecasting.")

successful_runs = [run for run in model_runs if run.get("training_status") in {"succeeded", "evaluated"} and run.get("rmse") is not None]
if successful_runs:
    latest_version = max(run["model_version"] for run in successful_runs)
    version_runs = [run for run in successful_runs if run["model_version"] == latest_version]
    st.markdown("#### Candidate comparison")
    st.caption(f"Latest training version: {latest_version}. Lower RMSE is the selection metric; MAE breaks ties.")
    comparison = pd.DataFrame(version_runs)
    figure = px.bar(
        comparison.sort_values("rmse"),
        x="model_name",
        y="rmse",
        color="is_active",
        color_discrete_map={True: "#087E8B", False: "#E46A55"},
        labels={"model_name": "Candidate", "rmse": "Holdout RMSE", "is_active": "Active"},
    )
    figure.update_layout(template="plotly_white", height=330, margin={"l": 10, "r": 10, "t": 18, "b": 8}, showlegend=False)
    st.plotly_chart(figure, use_container_width=True)
    candidate_view = comparison[["model_name", "training_records", "evaluation_records", "mae", "rmse", "r2", "training_status", "is_active"]].copy()
    candidate_view.columns = ["Candidate", "Training rows", "Holdout rows", "MAE", "RMSE", "R²", "Status", "Active"]
    st.dataframe(candidate_view, use_container_width=True, hide_index=True)
else:
    render_empty_state("No candidate metrics yet", "Candidate results are recorded when model training completes.")

st.markdown("#### Training history")
if model_runs:
    history = pd.DataFrame(model_runs)
    for column in ["mae", "rmse", "r2"]:
        if column not in history:
            history[column] = None
    history_view = history[["model_name", "model_version", "training_status", "training_records", "mae", "rmse", "r2", "trained_at", "is_active", "error_message"]].copy()
    history_view.columns = ["Model", "Version", "Status", "Training rows", "MAE", "RMSE", "R²", "Trained at", "Active", "Error"]
    st.dataframe(history_view, use_container_width=True, hide_index=True)
else:
    render_empty_state("No training runs", "Successful and failed attempts will be listed here.")

training_feedback = st.session_state.get("training_feedback")
if training_feedback:
    if training_feedback["training_status"] == "succeeded":
        st.success(f"{training_feedback['selected_model']} is active · version {training_feedback['model_version']}")
    else:
        st.error(f"Training failed: {training_feedback.get('error_message') or 'No model was activated.'}")
    if training_feedback.get("candidates"):
        st.dataframe(pd.DataFrame(training_feedback["candidates"]), use_container_width=True, hide_index=True)
    if st.button("Dismiss training result", key="dismiss_training_feedback"):
        st.session_state.pop("training_feedback", None)
        st.rerun()

if is_admin:
    st.markdown("#### Administrator controls")
    st.caption("Manual retraining uses the latest eligible MySQL sales history and does not run on page refresh.")
    confirm_retrain = st.checkbox("I understand this starts a model training job.", key="confirm_manual_retrain")
    if st.button("Retrain Model", type="primary", disabled=not confirm_retrain, key="manual_retrain"):
        try:
            with st.spinner("Training candidate models on historical sales…"):
                result = APIClient.retrain_model()
            st.session_state["training_feedback"] = result
            st.rerun()
        except APIError as error:
            st.error(error.message)
        except Exception as error:
            st.error(f"Could not run manual retraining: {error}")

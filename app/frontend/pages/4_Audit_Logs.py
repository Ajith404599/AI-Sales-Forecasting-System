import os
import sys
import streamlit as st
import pandas as pd
from datetime import date, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.api_client import APIClient, APIError
from utils.ui_theme import apply_custom_theme, render_hero, render_sidebar

st.set_page_config(page_title="Audit Trail & Security Logs", page_icon="📜", layout="wide")
apply_custom_theme()

if not st.session_state.get("token"):
    st.switch_page("app.py")
    st.stop()

render_sidebar()

user = st.session_state.get("user") or {}
user_role = str(user.get("role", "staff")).lower()

if user_role not in ["admin", "manager"]:
    st.error("⛔ Access Forbidden: Administrative privilege required to inspect compliance security logs.")
    st.stop()

render_hero(
    title="Security & System Audit Trails",
    subtitle="Chronological audit records tracking authentication events, database mutations, and administrative operations.",
    badge="Compliance Log"
)

st.markdown("### 🔍 Filter Audit Events")
col1, col2, col3, col4 = st.columns(4)

with col1:
    module_filter = st.selectbox("System Module", ["All", "AUTH", "PRODUCTS", "SALES", "USERS", "FORECASTING", "SYSTEM"])
with col2:
    action_filter = st.selectbox("Action Code", ["All", "LOGIN", "CREATE_PRODUCT", "UPDATE_PRODUCT", "RECORD_SALE", "CREATE_USER", "UPDATE_PROFILE", "ADMIN_UPDATE_USER", "RETRAIN_MODEL", "INITIALIZE_SYSTEM"])
with col3:
    start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
with col4:
    end_date = st.date_input("End Date", value=date.today() + timedelta(days=1))

try:
    start_iso = start_date.strftime("%Y-%m-%dT00:00:00") if start_date else None
    end_iso = end_date.strftime("%Y-%m-%dT23:59:59") if end_date else None
    
    logs = APIClient.get_audit_logs(
        module=module_filter,
        action=action_filter,
        start_date=start_iso,
        end_date=end_iso,
        limit=200
    ) or []
except Exception as e:
    st.error(f"Error querying audit trails: {e}")
    logs = []

if not logs:
    st.info("No audit logs recorded for the selected criteria.")
else:
    auth_cnt = sum(1 for l in logs if l.get('module') == 'AUTH')
    prod_cnt = sum(1 for l in logs if l.get('module') == 'PRODUCTS')
    sales_cnt = sum(1 for l in logs if l.get('module') == 'SALES')
    users_cnt = sum(1 for l in logs if l.get('module') == 'USERS')

    st.markdown(f"""
    <div style="display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap;">
        <span class="pill-badge pill-staff">Total Events: {len(logs)}</span>
        <span class="pill-badge pill-auth">AUTH: {auth_cnt}</span>
        <span class="pill-badge pill-prod">PRODUCTS: {prod_cnt}</span>
        <span class="pill-badge pill-active">SALES: {sales_cnt}</span>
        <span class="pill-badge pill-user">USERS: {users_cnt}</span>
    </div>
    """, unsafe_allow_html=True)
    
    df_logs = pd.DataFrame(logs)
    for col in ["log_id", "created_at", "username", "module", "action", "description"]:
        if col not in df_logs.columns:
            df_logs[col] = None

    df_logs["created_at"] = pd.to_datetime(df_logs["created_at"])
    display_df = df_logs[["log_id", "created_at", "username", "module", "action", "description"]].copy()
    display_df.columns = ["Event ID", "Timestamp", "Actor", "Module", "Action", "Description"]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss"),
            "Description": st.column_config.TextColumn("Description", width="large")
        }
    )

    st.write("---")
    st.markdown("### 🔬 Inspect Event Payload")
    log_ids = [f"#{l['log_id']} — [{l.get('module')}] {l.get('action')} by {l.get('username') or 'N/A'}" for l in logs]
    selected_idx = st.selectbox("Select Event Details", range(len(logs)), format_func=lambda i: log_ids[i])
    
    if logs and selected_idx is not None and 0 <= selected_idx < len(logs):
        st.json(logs[selected_idx])
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

from utils.api_client import APIClient, APIError
from utils.page_helpers import setup_authenticated_page
from utils.ui_theme import render_empty_state

setup_authenticated_page(
    "Login History",
    "Login History",
    "Review sign-in and session-end times for your account.",
    "Account security",
)

try:
    sessions = APIClient.get_login_history(limit=200) or []
except APIError as error:
    st.error(error.message)
    sessions = []
except Exception:
    st.error("Login history is temporarily unavailable.")
    sessions = []

if not sessions:
    render_empty_state("No login history yet", "A record appears after your next successful sign in.")
else:
    history = pd.DataFrame(sessions)
    login_utc = pd.to_datetime(history["login_at"], utc=True, errors="coerce")
    local_timezone = datetime.now().astimezone().tzinfo
    login_local = login_utc.dt.tz_convert(local_timezone).dt.tz_localize(None)

    logout_utc = pd.to_datetime(history["logout_at"], utc=True, errors="coerce")
    logout_local = logout_utc.dt.tz_convert(local_timezone).dt.tz_localize(None)
    active = history["logout_at"].isna()

    display = pd.DataFrame({
        "Login Date": login_local.dt.strftime("%d-%m-%Y"),
        "Login Time": login_local.dt.strftime("%I:%M:%S %p"),
        "Logout Date": logout_local.dt.strftime("%d-%m-%Y").where(~active, ""),
        "Logout Time": logout_local.dt.strftime("%I:%M:%S %p").where(~active, ""),
        "Session Status": [
            "Active Session" if is_active else (reason.title() if reason else "Ended")
            for is_active, reason in zip(active, history["logout_reason"])
        ],
    })

    active_count = int(active.sum())
    recent = login_local.max()
    summary_cols = st.columns(2)
    summary_cols[0].metric("Recorded sessions", len(history))
    summary_cols[1].metric("Current session", "Active" if active_count else "Signed out")
    st.caption(f"Times shown in your local timezone · Most recent sign in: {recent.strftime('%d-%m-%Y %I:%M:%S %p')}")
    st.dataframe(display, use_container_width=True, hide_index=True)

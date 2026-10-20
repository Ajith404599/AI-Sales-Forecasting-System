import os
import sys

import streamlit as st

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.session_timer import render_secure_session_timer
from utils.ui_theme import apply_custom_theme, render_page_header, render_sidebar


def setup_authenticated_page(page_title: str, title: str, subtitle: str, eyebrow: str = "Workspace") -> dict:
    st.set_page_config(page_title=page_title, page_icon="A", layout="wide")
    apply_custom_theme()
    if not st.session_state.get("token"):
        st.session_state["auth_mode"] = "login"
        st.session_state.setdefault("auth_notice", "Sign in to access your workspace.")
        st.switch_page("app.py")
        st.stop()
    render_sidebar(include_session_timer=False)
    header_column, timer_column = st.columns([4.2, 1.8])
    with header_column:
        render_page_header(title, subtitle, eyebrow)
    with timer_column:
        render_secure_session_timer(width=220, component_key="workspace_secure_session")
    return st.session_state.get("user") or {}

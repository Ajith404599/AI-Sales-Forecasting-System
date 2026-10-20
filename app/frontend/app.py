import streamlit as st

st.set_page_config(
    page_title="AI Sales Analytics",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.app_shell import render_application

render_application()
import base64
import json
import time
from pathlib import Path
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

SESSION_DURATION_SECONDS = 15 * 60
_COMPONENT = components.declare_component(
    "ai_sales_secure_session_timer",
    path=str(Path(__file__).resolve().parents[1] / "components" / "session_timer"),
)


def access_token_expiration(access_token: str) -> Optional[float]:
    try:
        payload_part = access_token.split(".")[1]
        padding = "=" * (-len(payload_part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_part + padding))
        expiration = payload.get("exp")
        return float(expiration) if expiration is not None else None
    except (IndexError, ValueError, TypeError, json.JSONDecodeError):
        return None


def start_session(access_token: str) -> float:
    """Persist the absolute API-issued access-token expiry; reruns never extend it."""
    expiration = access_token_expiration(access_token)
    if expiration is None:
        expiration = time.time() + SESSION_DURATION_SECONDS
    st.session_state["session_expires_at"] = expiration
    return expiration


def clear_authentication_session(message: str, close_backend_session: bool = False) -> None:
    access_token = st.session_state.get("token")
    if close_backend_session and access_token:
        try:
            from utils.api_client import APIClient

            APIClient.close_expired_session(access_token)
        except Exception:
            pass
    st.session_state.clear()
    st.session_state["auth_mode"] = "login"
    st.session_state["auth_notice"] = message


def render_secure_session_timer(width: int = 254, component_key: str = "secure_session_timer") -> None:
    access_token = st.session_state.get("token")
    if not access_token:
        return

    expiration = st.session_state.get("session_expires_at")
    if expiration is None:
        expiration = access_token_expiration(access_token)
        if expiration is None:
            clear_authentication_session("Session expired. Please sign in again.")
            st.rerun()
            return
        st.session_state["session_expires_at"] = expiration

    expiration = float(expiration)
    if time.time() >= expiration:
        clear_authentication_session(
            "Your session expired after 15 minutes. Please sign in again.",
            close_backend_session=True,
        )
        st.rerun()
        return

    result = _COMPONENT(
        expires_at_ms=int(expiration * 1000),
        default=None,
        key=f"{component_key}_{int(expiration)}",
        width=width,
        height=72,
    )
    if result == "expired" or time.time() >= expiration:
        clear_authentication_session(
            "Your session expired after 15 minutes. Please sign in again.",
            close_backend_session=True,
        )
        st.rerun()

import sys
from pathlib import Path

import streamlit as st

# ============================================================
# IMPORT PATH
# ============================================================

frontend_dir = str(Path(__file__).resolve().parents[1])

if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

from utils.api_client import APIClient, APIError
from utils.page_helpers import setup_authenticated_page


# ============================================================
# PAGE SETUP
# ============================================================

setup_authenticated_page(
    "Profile & Settings",
    "Profile & Settings",
    "Manage your personal information and account security.",
    "Account management",
)


# ============================================================
# SUCCESS MESSAGES
# ============================================================

profile_message = st.session_state.pop(
    "profile_success_message", None
)

if profile_message:
    st.success(profile_message)


# ============================================================
# LOAD PROFILE
# ============================================================

try:
    profile = APIClient.get_profile()

    if not isinstance(profile, dict):
        st.error("The server returned an invalid profile.")
        st.stop()

except APIError as error:
    st.error(f"Unable to load profile: {error.message}")
    st.stop()

except Exception:
    st.error("Unable to load profile. Please sign in again.")
    st.stop()


# ============================================================
# ACCOUNT INFORMATION
# ============================================================

st.subheader("👤 My Profile")

st.markdown("### Account Information")

col1, col2 = st.columns(2)

with col1:
    st.text_input(
        "Username",
        value=str(profile.get("username") or ""),
        disabled=True,
    )

with col2:
    st.text_input(
        "Account Role",
        value=str(profile.get("role") or ""),
        disabled=True,
    )

st.divider()


# ============================================================
# EDIT PROFILE
# ============================================================

st.subheader("✏️ Edit Profile")

st.caption(
    "Update your personal information. "
    "Your username and account role cannot be changed here."
)

with st.form("profile_update_form"):

    full_name = st.text_input(
        "Full Name",
        value=str(profile.get("full_name") or ""),
    )

    email = st.text_input(
        "Email Address",
        value=str(profile.get("email") or ""),
    )

    save_changes = st.form_submit_button(
        "💾 Save Changes",
        type="primary",
        use_container_width=True,
    )


if save_changes:

    full_name = full_name.strip()
    email = email.strip()

    if not full_name:
        st.error("Please enter your full name.")

    elif not email or "@" not in email:
        st.error("Please enter a valid email address.")

    else:
        try:
            APIClient.update_profile(
                {
                    "full_name": full_name,
                    "email": email,
                }
            )

            st.session_state[
                "profile_success_message"
            ] = "✅ Profile updated successfully!"

            st.rerun()

        except APIError as error:
            st.error(
                f"Unable to save changes: {error.message}"
            )

        except Exception:
            st.error(
                "Unable to save changes. Please try again."
            )


st.divider()


# ============================================================
# CHANGE PASSWORD
# ============================================================

st.subheader("🔐 Change Password")

st.caption(
    "Enter your current password and choose a new password."
)

with st.form("password_change_form"):

    current_password = st.text_input(
        "Current Password",
        type="password",
    )

    new_password = st.text_input(
        "New Password",
        type="password",
    )

    confirm_password = st.text_input(
        "Confirm New Password",
        type="password",
    )

    update_password = st.form_submit_button(
        "🔒 Update Password",
        type="primary",
        use_container_width=True,
    )


if update_password:

    if not current_password:
        st.error("Please enter your current password.")

    elif len(new_password) < 8:
        st.error(
            "Your new password must contain at least 8 characters."
        )

    elif new_password != confirm_password:
        st.error(
            "New Password and Confirm New Password do not match."
        )

    elif current_password == new_password:
        st.error(
            "Your new password must be different "
            "from your current password."
        )

    else:
        try:
            APIClient.change_password(
                {
                    "current_password": current_password,
                    "new_password": new_password,
                }
            )

            st.session_state[
                "profile_success_message"
            ] = (
                "✅ Password updated successfully! "
                "Please sign in again using your new password."
            )

            st.rerun()

        except APIError as error:
            st.error(
                f"Unable to update password: {error.message}"
            )

        except Exception:
            st.error(
                "Unable to update password. Please try again."
            )


st.divider()


# ============================================================
# ACCOUNT SECURITY
# ============================================================

st.subheader("🛡️ Account Security")

security_col1, security_col2 = st.columns(2)

with security_col1:
    st.success("🔒 Authentication enabled")

with security_col2:
    st.success("⏱️ 15-minute secure session")

st.info(
    "Your login and logout records are available "
    "on the separate Login History page."
)
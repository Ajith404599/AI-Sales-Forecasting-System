import os
import time
from typing import Optional, Dict, Any, List

import requests
import streamlit as st


# ============================================================
# BACKEND CONFIGURATION
# ============================================================

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8001"
).rstrip("/")

REQUEST_TIMEOUT_SECONDS = 20


# ============================================================
# CUSTOM API ERROR
# ============================================================

class APIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# ============================================================
# API CLIENT
# ============================================================

class APIClient:

    # --------------------------------------------------------
    # HEADERS
    # --------------------------------------------------------

    @staticmethod
    def _get_headers() -> Dict[str, str]:

        headers = {
            "Accept": "application/json"
        }

        token = st.session_state.get("token")

        if token:
            headers["Authorization"] = f"Bearer {token}"

        return headers


    # --------------------------------------------------------
    # REQUEST HELPER
    # --------------------------------------------------------

    @staticmethod
    def _request(
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:

        kwargs.setdefault(
            "timeout",
            REQUEST_TIMEOUT_SECONDS
        )

        try:

            return requests.request(
                method=method,
                url=url,
                **kwargs
            )

        except requests.exceptions.ConnectionError as exc:

            raise APIError(
                f"Cannot connect to FastAPI backend at "
                f"{API_BASE_URL}. Make sure the backend "
                f"server is running."
            ) from exc

        except requests.exceptions.Timeout as exc:

            raise APIError(
                "The backend server took too long to respond."
            ) from exc

        except requests.exceptions.RequestException as exc:

            raise APIError(
                f"Backend request failed: {exc}"
            ) from exc


    # --------------------------------------------------------
    # RESPONSE HANDLER
    # --------------------------------------------------------

    @classmethod
    def _handle_response(
        cls,
        response: requests.Response,
        clear_session_on_401: bool = True
    ) -> Any:

        try:
            data = response.json()
        except Exception:
            data = response.text

        # Handle expired / invalid login session
        if (
            response.status_code == 401
            and clear_session_on_401
        ):

            from utils.session_timer import (
                access_token_expiration,
                clear_authentication_session
            )

            token = st.session_state.get("token")

            expiration = (
                access_token_expiration(token)
                if token
                else None
            )

            clear_authentication_session(
                "Session expired. Please sign in again.",
                close_backend_session=(
                    expiration is not None
                    and time.time() >= expiration
                ),
            )

            st.rerun()

        if not response.ok:

            if isinstance(data, dict):
                detail = data.get(
                    "detail",
                    data.get(
                        "message",
                        str(data)
                    )
                )
            else:
                detail = str(data)

            raise APIError(
                detail or "Internal Server Error",
                response.status_code
            )

        return data


    # ========================================================
    # AUTHENTICATION
    # ========================================================

    @classmethod
    def login(
        cls,
        username: str,
        password: str
    ) -> Dict[str, Any]:

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/auth/token",
            data={
                "username": username,
                "password": password
            }
        )

        return cls._handle_response(
            response,
            clear_session_on_401=False
        )


    @classmethod
    def register(
        cls,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/auth/register",
            json={
                "username": username,
                "full_name": full_name,
                "email": email,
                "password": password,
            }
        )

        return cls._handle_response(
            response,
            clear_session_on_401=False
        )


    @classmethod
    def logout(cls) -> Dict[str, Any]:

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/auth/logout",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)


    @classmethod
    def close_expired_session(
        cls,
        access_token: str
    ) -> Dict[str, Any]:

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/auth/session-expired",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            timeout=2
        )

        return cls._handle_response(
            response,
            clear_session_on_401=False
        )


    @classmethod
    def get_login_history(
        cls,
        limit: int = 200,
        offset: int = 0
    ) -> List[Dict[str, Any]]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/auth/history",
            headers=cls._get_headers(),
            params={
                "limit": limit,
                "offset": offset
            }
        )

        return cls._handle_response(response)


    @classmethod
    def refresh_token(
        cls,
        refresh_token: str
    ) -> Dict[str, Any]:

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/auth/refresh",
            json={
                "refresh_token": refresh_token
            }
        )

        return cls._handle_response(response)


    # ========================================================
    # HEALTH
    # ========================================================

    @classmethod
    def get_health(cls) -> Dict[str, Any]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/health"
        )

        return cls._handle_response(
            response,
            clear_session_on_401=False
        )


    @classmethod
    def get_readiness(cls) -> Dict[str, Any]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/health/ready"
        )

        return cls._handle_response(
            response,
            clear_session_on_401=False
        )


    # ========================================================
    # PRODUCTS
    # ========================================================

    @classmethod
    def get_products(
        cls,
        category: Optional[str] = None,
        active_status: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:

        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset
        }

        if category and category != "All Categories":
            params["category"] = category

        if active_status is not None:
            params["active_status"] = (
                "true"
                if active_status
                else "false"
            )

        if search:
            params["search"] = search

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/products",
            headers=cls._get_headers(),
            params=params
        )

        return cls._handle_response(response)


    @classmethod
    def get_product(
        cls,
        product_id: int
    ) -> Dict[str, Any]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/products/{product_id}",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)


    @classmethod
    def create_product(
        cls,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/products",
            headers=cls._get_headers(),
            json=product_data
        )

        return cls._handle_response(response)


    @classmethod
    def update_product(
        cls,
        product_id: int,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        response = cls._request(
            "PUT",
            f"{API_BASE_URL}/products/{product_id}",
            headers=cls._get_headers(),
            json=product_data
        )

        return cls._handle_response(response)


    @classmethod
    def delete_product(
        cls,
        product_id: int
    ) -> Dict[str, Any]:

        response = cls._request(
            "DELETE",
            f"{API_BASE_URL}/products/{product_id}",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)


    # ========================================================
    # SALES
    # ========================================================

    @classmethod
    def record_sale(
        cls,
        sale_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/sales",
            headers=cls._get_headers(),
            json=sale_data
        )

        return cls._handle_response(response)


    @classmethod
    def get_sales(
        cls,
        product_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:

        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset
        }

        if product_id:
            params["product_id"] = product_id

        if user_id:
            params["user_id"] = user_id

        if start_date:
            params["start_date"] = start_date

        if end_date:
            params["end_date"] = end_date

        if search:
            params["search"] = search

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/sales",
            headers=cls._get_headers(),
            params=params
        )

        return cls._handle_response(response)


    @classmethod
    def get_sale(
        cls,
        sale_id: int
    ) -> Dict[str, Any]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/sales/{sale_id}",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)


    @classmethod
    def update_sale(
        cls,
        sale_id: int,
        sale_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        response = cls._request(
            "PUT",
            f"{API_BASE_URL}/sales/{sale_id}",
            headers=cls._get_headers(),
            json=sale_data
        )

        return cls._handle_response(response)


    @classmethod
    def delete_sale(
        cls,
        sale_id: int
    ) -> Any:

        response = cls._request(
            "DELETE",
            f"{API_BASE_URL}/sales/{sale_id}",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)


    # ========================================================
    # ANALYTICS
    # ========================================================

    @classmethod
    def get_analytics_summary(cls) -> Dict[str, Any]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/analytics/summary",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)


    @classmethod
    def get_monthly_sales(cls) -> List[Dict[str, Any]]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/analytics/monthly",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)


    @classmethod
    def get_products_analytics(
        cls,
        sort_by: str = "revenue_desc",
        limit: int = 20
    ) -> List[Dict[str, Any]]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/analytics/products",
            headers=cls._get_headers(),
            params={
                "sort_by": sort_by,
                "limit": limit
            }
        )

        return cls._handle_response(response)


    @classmethod
    def get_categories_analytics(
        cls
    ) -> List[Dict[str, Any]]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/analytics/categories",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)


    # ========================================================
    # PROFILE / USERS
    # ========================================================

    @classmethod
    def get_profile(cls) -> Dict[str, Any]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/profile",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)


    @classmethod
    def update_profile(
        cls,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        response = cls._request(
            "PUT",
            f"{API_BASE_URL}/profile",
            headers=cls._get_headers(),
            json=profile_data
        )

        return cls._handle_response(response)


    @classmethod
    def change_password(
        cls,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Change the signed-in user's password through the auth API."""
        response = cls._request(
            "POST",
            f"{API_BASE_URL}/auth/change-password",
            headers=cls._get_headers(),
            json=payload,
        )
        return cls._handle_response(response)


    @classmethod
    def get_users(
        cls,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/users",
            headers=cls._get_headers(),
            params={
                "limit": limit,
                "offset": offset
            }
        )

        return cls._handle_response(response)


    @classmethod
    def create_user(
        cls,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/users",
            headers=cls._get_headers(),
            json=user_data
        )

        return cls._handle_response(response)


    @classmethod
    def update_user(
        cls,
        user_id: int,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        response = cls._request(
            "PUT",
            f"{API_BASE_URL}/users/{user_id}",
            headers=cls._get_headers(),
            json=user_data
        )

        return cls._handle_response(response)


    # ========================================================
    # AUDIT LOGS
    # ========================================================

    @classmethod
    def get_audit_logs(
        cls,
        user_id: Optional[int] = None,
        module: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:

        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset
        }

        if user_id:
            params["user_id"] = user_id

        if module and module != "All":
            params["module"] = module

        if action and action != "All":
            params["action"] = action

        if start_date:
            params["start_date"] = start_date

        if end_date:
            params["end_date"] = end_date

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/audit-logs",
            headers=cls._get_headers(),
            params=params
        )

        return cls._handle_response(response)


    # ========================================================
    # AI COPILOT
    # ========================================================

    @classmethod
    def ask_ai_copilot(
        cls,
        question: str
    ) -> Dict[str, Any]:

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/ai/query",
            headers=cls._get_headers(),
            json={
                "question": question
            }
        )

        return cls._handle_response(response)


    # ========================================================
    # FORECASTING
    # ========================================================

    @classmethod
    def predict_sales(
        cls,
        product_id: int,
        horizon_days: Optional[int] = None,
        forecast_date: Optional[str] = None
    ) -> Dict[str, Any]:

        payload: Dict[str, Any] = {
            "product_id": product_id
        }

        if horizon_days is not None:
            payload["horizon_days"] = horizon_days

        if forecast_date:
            payload["forecast_date"] = forecast_date

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/forecast/predict",
            headers=cls._get_headers(),
            json=payload
        )

        return cls._handle_response(response)


    # ========================================================
    # PREDICTION HISTORY
    # ========================================================

    @classmethod
    def get_predictions(
        cls,
        product_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        model_version: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:

        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset
        }

        if product_id is not None:
            params["product_id"] = product_id

        if start_date:
            params["start_date"] = start_date

        if end_date:
            params["end_date"] = end_date

        if model_version:
            params["model_version"] = model_version

        if search:
            params["search"] = search

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/predictions",
            headers=cls._get_headers(),
            params=params
        )

        return cls._handle_response(response)


    @classmethod
    def update_prediction_actual(
        cls,
        prediction_id: int,
        actual_quantity: float
    ) -> Dict[str, Any]:

        response = cls._request(
            "PATCH",
            f"{API_BASE_URL}/predictions/"
            f"{prediction_id}/actual",
            headers=cls._get_headers(),
            json={
                "actual_quantity": actual_quantity
            }
        )

        return cls._handle_response(response)


    # ========================================================
    # MODEL PERFORMANCE
    # ========================================================

    @classmethod
    def get_active_model(
        cls
    ) -> Optional[Dict[str, Any]]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/models/active",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)


    @classmethod
    def get_model_runs(
        cls,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:

        response = cls._request(
            "GET",
            f"{API_BASE_URL}/models/runs",
            headers=cls._get_headers(),
            params={
                "limit": limit,
                "offset": offset
            }
        )

        return cls._handle_response(response)


    @classmethod
    def retrain_model(
        cls
    ) -> Dict[str, Any]:

        response = cls._request(
            "POST",
            f"{API_BASE_URL}/models/retrain",
            headers=cls._get_headers()
        )

        return cls._handle_response(response)

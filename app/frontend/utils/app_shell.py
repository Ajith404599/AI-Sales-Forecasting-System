from datetime import datetime
from html import escape
from typing import Any, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components

from utils.api_client import APIClient, APIError
from utils.session_timer import render_secure_session_timer, start_session
from utils.ui_theme import (
    apply_custom_theme,
    render_brand,
    render_empty_state,
    render_kpi,
    render_sidebar,
)


def _store_login(result: dict[str, Any]) -> None:
    st.session_state["token"] = result["access_token"]
    st.session_state["refresh_token"] = result.get("refresh_token")
    st.session_state["user"] = result["user"]
    start_session(result["access_token"])
    st.session_state["auth_mode"] = "home"
    st.session_state["auth_notice"] = "Sign in successful. Your workspace is ready."
    st.rerun()


def _set_auth_mode(mode: str) -> None:
    st.session_state["auth_mode"] = mode
    st.rerun()


def _public_nav() -> None:
    brand_col, action_col = st.columns([1.6, 1])
    with brand_col:
        render_brand()
    with action_col:
        sign_in_col, start_col = st.columns(2)
        with sign_in_col:
            if st.button("Sign In", key="public_signin", use_container_width=True):
                _set_auth_mode("login")
        with start_col:
            if st.button("Get Started", key="public_get_started", type="primary", use_container_width=True):
                _set_auth_mode("signup")
    st.markdown(
        '<nav class="site-nav-links"><a href="#home">Home</a><a href="#features">Features</a>'
        '<a href="#about">About</a></nav>',
        unsafe_allow_html=True,
    )


def _render_landing_page() -> None:
    _public_nav()
    st.markdown('<div id="home"></div>', unsafe_allow_html=True)
    hero_copy, hero_preview = st.columns([1.05, 0.95], gap="large")
    with hero_copy:
        st.markdown(
        '<div class="eyebrow">Sales intelligence, built for decisions</div>'
        '<h1 class="landing-title">Forecast sales.<br>Understand performance.<br>Grow smarter.</h1>'
        '<p class="landing-copy">Bring your sales history into one clear workspace. Compare real demand forecasts, '
        'track business performance, and make the next decision with confidence.</p>',
        unsafe_allow_html=True,
        )
    with hero_preview:
        st.markdown(
        '<div class="preview-window"><div class="preview-top"><i class="preview-dot"></i><i class="preview-dot"></i>'
        '<i class="preview-dot"></i><span style="margin-left:8px">Sales intelligence workspace</span></div>'
        '<div class="preview-body"><div class="eyebrow">Your connected business</div>'
        '<div style="font:700 1.25rem Space Grotesk,sans-serif;margin-top:8px">A clearer view of what is next</div>'
        '<div class="preview-lines" aria-hidden="true"><i style="height:32%"></i><i style="height:46%"></i>'
        '<i style="height:39%"></i><i style="height:61%"></i><i style="height:53%"></i>'
        '<i style="height:77%"></i><i style="height:66%"></i><i style="height:92%"></i></div>'
        '<div style="font-size:.8rem;color:#607477">Live metrics and forecasts appear from your own sales data after sign in.</div>'
        '</div></div>',
        unsafe_allow_html=True,
        )
    action_left, action_right, _ = st.columns([1.7, 1.7, 3])
    with action_left:
        if st.button("Create your account", key="hero_create", type="primary", use_container_width=True):
            _set_auth_mode("signup")
    with action_right:
        if st.button("Sign in to workspace", key="hero_signin", use_container_width=True):
            _set_auth_mode("login")

    st.markdown(
        '<section class="feature-band" id="features"><div class="eyebrow">One operating picture</div>'
        '<div class="section-title">From sales activity to a sharper plan</div>'
        '<div class="feature-grid"><article class="feature-item"><div class="eyebrow">01 / Forecast</div>'
        '<h3>Demand grounded in history</h3><p>Use time-aware model comparisons and saved pipeline versions to forecast product demand.</p>'
        '</article><article class="feature-item"><div class="eyebrow">02 / Understand</div>'
        '<h3>Performance in context</h3><p>Follow revenue, units, products, and transaction trends from the connected sales ledger.</p>'
        '</article><article class="feature-item"><div class="eyebrow">03 / Operate</div>'
        '<h3>One connected workflow</h3><p>Manage sales alongside the existing product catalog, with access controlled by your account role.</p>'
        '</article></div></section>'
        '<section class="feature-band"><div class="eyebrow">AI forecasting</div>'
        '<div class="section-title">A forecast you can inspect</div>'
        '<p class="landing-copy">Compare candidate regressors on a chronological holdout, review the measured errors, '
        'and request forecasts from the active persisted model. Prediction history stays tied to the model version that created it.</p>'
        '</section><section class="feature-band"><div class="eyebrow">Business analytics</div>'
        '<div class="section-title">See the business as it is</div>'
        '<p class="landing-copy">Dashboards and reports are populated by the FastAPI service from your database. '
        'The interface does not substitute sample figures for your actual performance.</p></section>'
        '<section class="feature-band" id="about"><div class="eyebrow">About</div>'
        '<div class="section-title">Built around your existing operation</div>'
        '<p class="landing-copy">AI Sales Analytics connects your existing products, users, and sales records to a '
        'secure business API and a practical forecasting workflow.</p></section>'
        '<footer class="landing-footer"><span>AI Sales Analytics</span><span>FastAPI · MySQL · Streamlit</span>'
        '<span>Real business data. Measured forecasts.</span></footer>',
        unsafe_allow_html=True,
    )


def _render_auth_page(mode: str) -> None:
    _public_nav()
    back_col, _, _ = st.columns([1, 2, 1])
    with back_col:
        if st.button("← Back to home", key="auth_back"):
            _set_auth_mode("home")

    left, form_col, right = st.columns([1, 1.15, 1])
    with form_col:
        render_brand()
        if mode == "login":
            st.markdown('<div class="auth-heading"><div class="eyebrow">Secure workspace access</div>'
                        '<h1>Welcome back</h1><p>Sign in to continue to your sales workspace.</p></div>',
                        unsafe_allow_html=True)
            show_password = st.toggle("Show password", key="login_show_password")
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username or email", placeholder="you@company.com", autocomplete="username")
                password = st.text_input("Password", type="default" if show_password else "password", autocomplete="current-password")
                submit = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                if submit:
                    if not username.strip() or not password:
                        st.error("Enter your username or email and password.")
                    else:
                        try:
                            _store_login(APIClient.login(username.strip(), password))
                        except APIError as error:
                            if error.status_code == 401 and "attempts remaining" in error.message:
                                st.warning(error.message)
                            elif error.status_code == 423:
                                st.error(error.message)
                            elif error.status_code == 403:
                                st.error(error.message)
                            elif error.status_code == 401:
                                st.error(f"Invalid credentials. {error.message}")
                            else:
                                st.error(error.message)
                        except requests.RequestException:
                            st.error("Authentication service is unavailable. Please try again shortly.")
            st.info("Secure login protection · Account temporarily locks after 3 unsuccessful password attempts.")
            st.caption("Credentials are verified by FastAPI. Passwords and session tokens are never shown here.")
            if st.button("Create an account", key="to_signup", use_container_width=True):
                _set_auth_mode("signup")
        else:
            st.markdown('<div class="auth-heading"><div class="eyebrow">Start with your sales data</div>'
                        '<h1>Create your account</h1><p>Public accounts are created with the Sales Analyst role.</p></div>',
                        unsafe_allow_html=True)
            show_password = st.toggle("Show password", key="signup_show_password")
            with st.form("signup_form", clear_on_submit=False):
                full_name = st.text_input("Full Name", max_chars=120, autocomplete="name")
                username = st.text_input("Username", max_chars=50, autocomplete="username")
                email = st.text_input("Email", autocomplete="email")
                password = st.text_input("Password", type="default" if show_password else "password", autocomplete="new-password")
                confirmation = st.text_input("Confirm Password", type="default" if show_password else "password", autocomplete="new-password")
                submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)
                if submit:
                    if not full_name.strip() or not username.strip() or not email.strip() or not password:
                        st.error("Complete all account fields.")
                    elif len(password) < 8:
                        st.error("Password must contain at least 8 characters.")
                    elif password != confirmation:
                        st.error("Password confirmation does not match.")
                    else:
                        try:
                            result = APIClient.register(username.strip(), email.strip(), password, full_name.strip())
                            _store_login(result)
                        except APIError as error:
                            st.error(error.message)
                        except requests.RequestException as error:
                            st.error(f"Could not reach the API: {error}")
            st.caption("Your account receives the Sales Analyst role. Administrator access cannot be self-assigned.")
            if st.button("Already registered? Sign in", key="to_signin", use_container_width=True):
                _set_auth_mode("login")


def _load_dashboard_data() -> dict[str, Any]:
    data: dict[str, Any] = {}
    fetchers = {
        "health": APIClient.get_health,
        "readiness": APIClient.get_readiness,
        "summary": APIClient.get_analytics_summary,
        "monthly": APIClient.get_monthly_sales,
        "products": lambda: APIClient.get_products_analytics(sort_by="volume_desc", limit=10),
        "sales": lambda: APIClient.get_sales(limit=8),
        "catalog": lambda: APIClient.get_products(limit=200),
        "active_model": APIClient.get_active_model,
    }
    for key, fetch in fetchers.items():
        try:
            data[key] = fetch()
        except APIError as error:
            st.warning(f"{key.replace('_', ' ').title()} is unavailable: {error.message}")
        except Exception as error:
            st.warning(f"{key.replace('_', ' ').title()} is unavailable: {error}")
    return data


def _render_live_clock() -> None:
    components.html(
                """<div style='font:500 13px "Plus Jakarta Sans",sans-serif;color:#607477;background:#fff;border:1px solid #dce6e4;border-left:3px solid #087e8b;border-radius:9px;padding:10px 13px;min-width:220px'>
                <div style='display:flex;align-items:center;gap:7px;color:#087e8b;font-size:10px;font-weight:800;letter-spacing:.08em;margin-bottom:4px'><span style='width:7px;height:7px;border-radius:50%;background:#1d8b68'></span>LIVE LOCAL TIME</div>
                <div id='live-date' style='font-size:13px;font-weight:600;color:#244144'></div>
                <div id='live-time' style='font-size:18px;font-weight:700;color:#142b2d;font-variant-numeric:tabular-nums'></div>
                </div>
        <script>
                const dateNode = document.getElementById('live-date');
                const timeNode = document.getElementById('live-time');
                const dateFormatter = new Intl.DateTimeFormat('en-US', {weekday:'long',day:'2-digit',month:'long',year:'numeric'});
                const timeFormatter = new Intl.DateTimeFormat('en-US', {hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:true});
                const updateClock = () => {
                    const now = new Date();
                    const parts = Object.fromEntries(dateFormatter.formatToParts(now).map(part => [part.type, part.value]));
                    dateNode.textContent = `${parts.weekday}, ${parts.day} ${parts.month} ${parts.year}`;
                    timeNode.textContent = timeFormatter.format(now);
                };
        updateClock(); setInterval(updateClock, 1000);
        </script>""",
                height=84,
        scrolling=False,
    )


def _render_dashboard() -> None:
    user = st.session_state.get("user") or {}
    display_name = user.get("full_name") or user.get("username") or "there"
    st.markdown(
        f'<div class="eyebrow">Business overview</div><h1 class="dashboard-title">Good to see you, {escape(display_name)}.</h1>',
        unsafe_allow_html=True,
    )
    role = escape(str(user.get("role") or "User").title())
    st.caption(f"{role} · Authenticated")
    clock_col, timer_col, refresh_col = st.columns([1.5, 1.5, 0.8])
    with clock_col:
        _render_live_clock()
    with timer_col:
        render_secure_session_timer(width=232, component_key="dashboard_secure_session")
    with refresh_col:
        if st.button("Refresh data", key="refresh_dashboard"):
            st.rerun()

    with st.spinner("Loading live business data…"):
        data = _load_dashboard_data()

    summary = data.get("summary")
    products = data.get("products") or []
    catalog = data.get("catalog") or []
    top_product = next((item for item in products if item.get("total_quantity_sold", 0) > 0), None)
    avg_sale = None
    if summary and summary.get("total_sales_count"):
        avg_sale = float(summary.get("total_revenue", 0)) / summary["total_sales_count"]

    metrics = [
        ("Total Revenue", f"${summary['total_revenue']:,.2f}" if summary else "Unavailable", "Revenue recorded", "cyan"),
        ("Units Sold", f"{summary['total_quantity_sold']:,}" if summary else "Unavailable", "Across sales transactions", "emerald"),
        ("Sales Transactions", f"{summary['total_sales_count']:,}" if summary else "Unavailable", "Recorded orders", "indigo"),
        ("Active Products", f"{summary['active_products_count']:,}" if summary else "Unavailable", "From existing catalog", "amber"),
        ("Average Sale Value", f"${avg_sale:,.2f}" if avg_sale is not None else "No sales yet", "Revenue per transaction", "cyan"),
        ("Top-Selling Product", top_product["product_name"] if top_product else "No sales yet", f"{top_product['total_quantity_sold']:,} units" if top_product else "By units sold", "emerald"),
    ]
    for row_start in range(0, len(metrics), 3):
        columns = st.columns(3)
        for column, metric in zip(columns, metrics[row_start:row_start + 3]):
            with column:
                render_kpi(metric[0], metric[1], "", metric[3], metric[2])

    st.markdown('<div class="dashboard-section-title">Sales performance</div>', unsafe_allow_html=True)
    monthly = data.get("monthly") or []
    chart_col, product_col = st.columns([1.55, 1])
    with chart_col:
        st.markdown('<div class="panel-heading">Revenue and sales trend</div>', unsafe_allow_html=True)
        if monthly:
            monthly_frame = pd.DataFrame(monthly)
            figure = go.Figure()
            figure.add_trace(go.Bar(
                x=monthly_frame["month"], y=monthly_frame["total_revenue"], name="Revenue",
                marker_color="#087E8B", yaxis="y",
            ))
            figure.add_trace(go.Scatter(
                x=monthly_frame["month"], y=monthly_frame["total_orders"], name="Transactions",
                mode="lines+markers", line={"color": "#E46A55", "width": 3}, yaxis="y2",
            ))
            figure.update_layout(
                template="plotly_white", height=330, margin={"l": 12, "r": 12, "t": 26, "b": 10},
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                yaxis={"title": "Revenue", "gridcolor": "#E7EEEC"},
                yaxis2={"title": "Transactions", "overlaying": "y", "side": "right", "showgrid": False},
                legend={"orientation": "h", "y": 1.12},
            )
            st.plotly_chart(figure, use_container_width=True)
        else:
            render_empty_state("No sales trend to display", "Monthly charts appear when transaction history is available.")

    with product_col:
        st.markdown('<div class="panel-heading">Top products by units</div>', unsafe_allow_html=True)
        sold_products = [item for item in products if item.get("total_quantity_sold", 0) > 0]
        if sold_products:
            product_frame = pd.DataFrame(sold_products).sort_values("total_quantity_sold")
            figure = px.bar(
                product_frame, x="total_quantity_sold", y="product_name", orientation="h",
                color_discrete_sequence=["#E46A55"], labels={"total_quantity_sold": "Units", "product_name": ""},
            )
            figure.update_layout(template="plotly_white", height=330, margin={"l": 4, "r": 4, "t": 22, "b": 8}, showlegend=False)
            st.plotly_chart(figure, use_container_width=True)
        else:
            render_empty_state("No product sales yet", "Product rankings use recorded sales only.")

    recent_sales = data.get("sales") or []
    st.markdown('<div class="panel-heading">Recent sales</div>', unsafe_allow_html=True)
    if recent_sales:
        names = {item["product_id"]: item["product_name"] for item in catalog if "product_id" in item}
        sales_frame = pd.DataFrame(recent_sales)
        sales_frame["product"] = sales_frame["product_id"].map(names).fillna("Product #" + sales_frame["product_id"].astype(str))
        sales_frame["sale_date"] = pd.to_datetime(sales_frame["sale_date"], errors="coerce")
        show = sales_frame[["sale_id", "product", "quantity", "unit_price", "total_amount", "sale_date"]].copy()
        show.columns = ["Sale", "Product", "Units", "Unit price", "Total", "Sale date"]
        st.dataframe(show, use_container_width=True, hide_index=True, column_config={
            "Unit price": st.column_config.NumberColumn(format="$%.2f"),
            "Total": st.column_config.NumberColumn(format="$%.2f"),
            "Sale date": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm"),
        })
    else:
        render_empty_state("No recent sales", "Transactions recorded through Sales Management will appear here.")

    st.markdown('<div class="dashboard-section-title">System status</div>', unsafe_allow_html=True)
    status_cols = st.columns(3)
    with status_cols[0]:
        st.metric("FastAPI", "Online" if data.get("health", {}).get("status") == "ok" else "Unavailable")
    with status_cols[1]:
        st.metric("Database", "Connected" if data.get("readiness", {}).get("database") == "connected" else "Unavailable")
    with status_cols[2]:
        active_model = data.get("active_model")
        st.metric("Active ML model", active_model["model_name"] if active_model else "Not trained")
        if active_model:
            st.caption(f"Version {active_model['model_version']} · trained {active_model['trained_at']}")


def render_application() -> None:
    apply_custom_theme()
    st.session_state.setdefault("token", None)
    st.session_state.setdefault("refresh_token", None)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("auth_mode", "home")

    if not st.session_state.get("token"):
        st.markdown(
            '<style>section[data-testid="stSidebar"]{display:flex!important;width:0!important;'
            'min-width:0!important;flex-basis:0!important;overflow:hidden!important}'
            '[data-testid="stSidebarCollapsedControl"]{display:none!important}'
            '[data-testid="stToolbar"]{display:none!important}'
            '[data-testid="stDeployButton"]{display:none!important}</style>',
            unsafe_allow_html=True,
        )
        notice = st.session_state.pop("auth_notice", None)
        if notice:
            st.info(notice)
        mode = st.session_state.get("auth_mode", "home")
        if mode == "home":
            _render_landing_page()
        else:
            _render_auth_page(mode)
        return

    st.markdown(
        '<style>section[data-testid="stSidebar"]{display:flex!important;width:280px!important;'
        'min-width:280px!important;flex-basis:280px!important}'
        '@media (min-width:801px){section[data-testid="stSidebar"]{transform:translateX(0)!important}'
        '[data-testid="stSidebarCollapsedControl"]{display:none!important}}</style>',
        unsafe_allow_html=True,
    )
    notice = st.session_state.pop("auth_notice", None)
    if notice:
        st.success(notice)
    render_sidebar(include_session_timer=False)
    _render_dashboard()

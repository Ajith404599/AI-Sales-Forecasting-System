import os
import sys
import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def apply_custom_theme():
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
    
    <style>
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #0F172A;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Space Grotesk', sans-serif !important;
            letter-spacing: -0.025em;
            font-weight: 700;
        }

        :root {
            --primary: #4F46E5;
            --primary-dark: #3730A3;
            --surface-card: #FFFFFF;
            --border-subtle: #E2E8F0;
            --card-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.05), 0 8px 10px -6px rgba(15, 23, 42, 0.03);
            --card-shadow-hover: 0 20px 30px -10px rgba(79, 70, 229, 0.15);
        }

        /* Hero Container */
        .premium-hero {
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.06) 0%, rgba(236, 72, 153, 0.06) 50%, rgba(6, 182, 212, 0.06) 100%);
            border: 1px solid rgba(79, 70, 229, 0.15);
            border-radius: 20px;
            padding: 28px 32px;
            margin-bottom: 24px;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.03);
        }

        .gradient-heading {
            background: linear-gradient(135deg, #1E1B4B 0%, #4F46E5 50%, #7C3AED 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }

        /* KPI Metric Container */
        .kpi-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px;
            border-radius: 16px;
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            box-shadow: var(--card-shadow);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            height: 105px;
            box-sizing: border-box;
        }
        .kpi-container:hover {
            transform: translateY(-3px);
            box-shadow: var(--card-shadow-hover);
            border-color: #CBD5E1;
        }

        .kpi-indigo { border-left: 5px solid #4F46E5; }
        .kpi-cyan { border-left: 5px solid #0891B2; }
        .kpi-emerald { border-left: 5px solid #059669; }
        .kpi-amber { border-left: 5px solid #D97706; }

        .kpi-title {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748B;
            margin-bottom: 6px;
        }

        .kpi-number {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.85rem;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.1;
        }

        .kpi-icon-badge {
            width: 48px;
            height: 48px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
        }
        .icon-indigo { background: rgba(79, 70, 229, 0.1); color: #4F46E5; }
        .icon-cyan { background: rgba(8, 145, 178, 0.1); color: #0891B2; }
        .icon-emerald { background: rgba(5, 150, 105, 0.1); color: #059669; }
        .icon-amber { background: rgba(217, 119, 6, 0.1); color: #D97706; }

        /* Badge Tokens */
        .pill-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .pill-admin { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
        .pill-manager { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
        .pill-staff { background: #E0E7FF; color: #3730A3; border: 1px solid #C7D2FE; }
        .pill-active { background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
        .pill-inactive { background: #F1F5F9; color: #64748B; border: 1px solid #CBD5E1; }
        .pill-auth { background: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }
        .pill-prod { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }
        .pill-user { background: #F3E8FF; color: #6B21A8; border: 1px solid #E9D5FF; }

        /* Unified Workspace Action Cards */
        .module-card {
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            border-radius: 18px;
            padding: 22px;
            box-shadow: var(--card-shadow);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 250px;
            box-sizing: border-box;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 12px;
        }
        .module-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--card-shadow-hover);
            border-color: #818CF8;
        }

        .module-card p {
            min-height: 54px;
            line-height: 1.45;
            margin-top: 6px;
            margin-bottom: 12px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
        }

        /* Sidebar Identity Unit */
        .sidebar-card {
            background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
            color: #FFFFFF;
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.3);
        }

        /* Streamlit Element Overrides */
        div[data-testid="stForm"] {
            background: #FFFFFF;
            border-radius: 16px;
            padding: 24px;
            border: 1px solid var(--border-subtle);
            box-shadow: var(--card-shadow);
        }

        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            padding: 0.5rem 1.25rem;
            transition: all 0.2s ease;
        }

        [data-testid="stDataFrame"] {
            border-radius: 12px;
            border: 1px solid var(--border-subtle);
            box-shadow: var(--card-shadow);
        }

        :root {
            --primary: #087E8B;
            --primary-dark: #075D66;
            --surface-card: #FFFFFF;
            --border-subtle: #DCE6E4;
            --card-shadow: 0 14px 36px -24px rgba(12, 41, 45, 0.42);
            --card-shadow-hover: 0 18px 40px -22px rgba(8, 126, 139, 0.44);
            --ink: #142B2D;
            --muted: #607477;
            --canvas: #F5F8F7;
            --coral: #E46A55;
            --gold: #C99B43;
        }

        html, body, [class*="css"] { color: var(--ink); letter-spacing: 0; }
        h1, h2, h3, h4, h5, h6 { letter-spacing: 0 !important; }
        .stApp { background: var(--canvas); }
        [data-testid="stHeader"] { background: rgba(245, 248, 247, 0.92); }
        [data-testid="stSidebarNav"], #MainMenu, footer { display: none !important; }
        [data-testid="stSidebar"] { background: #EAF1EF; border-right: 1px solid #D5E2DF; }
        [data-testid="stSidebarContent"] { padding: 1.15rem 0.85rem; }
        section[data-testid="stSidebar"] { width:280px !important; min-width:280px !important; flex-basis:280px !important; }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1440px; }
        .stButton > button { border-radius: 8px; min-height: 2.65rem; border-color: #CAD8D5; }
        .stButton > button[kind="primary"] { background: var(--primary); border-color: var(--primary); color: #FFFFFF; }
        [data-testid="stBaseButton-primaryFormSubmit"], [data-testid="stBaseButton-primary"] { background:#087E8B !important; border-color:#087E8B !important; color:#FFFFFF !important; }
        .stButton > button:hover { border-color: var(--primary); color: var(--primary-dark); }
        div[data-testid="stForm"] { border-radius: 10px; border-color: #DCE6E4; box-shadow: var(--card-shadow); }
        [data-testid="stDataFrame"] { border-radius: 10px; }
        [data-testid="stAlert"] { border-radius: 8px; }
        .site-nav { display:flex; align-items:center; justify-content:space-between; padding:14px 0 20px; border-bottom:1px solid #DCE6E4; margin-bottom:30px; }
        .brand-mark { display:flex; align-items:center; gap:10px; font-family:'Space Grotesk',sans-serif; font-size:1.12rem; font-weight:700; color:#142B2D; }
        .brand-symbol { display:grid; place-items:center; width:34px; height:34px; border-radius:9px; background:#087E8B; color:white; font-size:16px; }
        .landing-hero { display:grid; grid-template-columns:minmax(0,1.05fr) minmax(310px,.95fr); gap:52px; align-items:center; padding:58px 0 68px; }
        .landing-title { font:700 2.9rem/1.08 'Space Grotesk',sans-serif; letter-spacing:0; color:#142B2D; margin:12px 0 18px; }
        .landing-copy { max-width:600px; color:#607477; font-size:1.02rem; line-height:1.55; }
        .eyebrow { color:#087E8B; text-transform:uppercase; font-size:.74rem; font-weight:800; letter-spacing:.12em; }
        .preview-window { overflow:hidden; border-radius:12px; background:#FFFFFF; border:1px solid #D8E4E1; box-shadow:0 28px 70px -42px rgba(12,41,45,.55); }
        .preview-top { display:flex; align-items:center; gap:7px; padding:13px 16px; border-bottom:1px solid #E6EEEC; color:#607477; font-size:.78rem; }
        .preview-dot { width:8px; height:8px; border-radius:50%; background:#E46A55; }
        .preview-dot:nth-child(2) { background:#C99B43; } .preview-dot:nth-child(3) { background:#087E8B; }
        .preview-body { padding:22px; min-height:245px; }
        .preview-lines { display:flex; gap:8px; align-items:flex-end; height:108px; margin:20px 0 8px; border-bottom:1px solid #DCE6E4; background:repeating-linear-gradient(to bottom,transparent 0 35px,#EDF2F1 36px); }
        .preview-lines i { display:block; flex:1; border-radius:4px 4px 0 0; background:#B7DCDD; }
        .preview-lines i:nth-child(2n) { background:#087E8B; } .preview-lines i:last-child { background:#E46A55; }
        .feature-band { padding:54px 0; border-top:1px solid #DCE6E4; }
        .feature-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:22px; margin-top:24px; }
        .feature-item { padding:22px; border:1px solid #DCE6E4; border-radius:10px; background:#FFFFFF; min-height:150px; }
        .section-title { color:#142B2D; font:700 2rem/1.15 'Space Grotesk',sans-serif; letter-spacing:0; }
        .landing-footer { display:flex; justify-content:space-between; gap:16px; padding:24px 0; border-top:1px solid #DCE6E4; color:#607477; font-size:.84rem; }
        .site-nav { border:0; margin:0; padding:0; }
        .site-nav-links { display:flex; justify-content:center; gap:26px; }
        .site-nav-links a { color:#607477; text-decoration:none; font-size:.9rem; font-weight:600; }
        .site-nav-links a:hover { color:#087E8B; }
        [data-testid="stAppDeployButton"] { display:none !important; }
        .premium-hero { background:#FFFFFF; border:1px solid #DCE6E4; border-left:4px solid #087E8B; border-radius:10px; box-shadow:none; backdrop-filter:none; }
        .gradient-heading { background:none; color:#142B2D; -webkit-text-fill-color:#142B2D; }
        .kpi-container { border-radius:10px; border-left-width:3px; box-shadow:0 10px 28px -24px rgba(12,41,45,.45); height:auto; min-height:112px; }
        .kpi-number { font-size:1.35rem; line-height:1.18; overflow-wrap:anywhere; }
        .kpi-indigo { border-left-color:#087E8B; } .kpi-cyan { border-left-color:#087E8B; }
        .kpi-emerald { border-left-color:#1D8B68; } .kpi-amber { border-left-color:#C99B43; }
        .icon-indigo, .icon-cyan { background:#E1F1F0; color:#087E8B; }
        .icon-emerald { background:#E4F2EA; color:#1D8B68; } .icon-amber { background:#F7F0E2; color:#A87927; }
        .dashboard-title { margin:5px 0 0; font:700 2rem/1.2 'Space Grotesk',sans-serif; color:#142B2D; }
        .dashboard-section-title { margin:32px 0 15px; font:700 1.35rem/1.2 'Space Grotesk',sans-serif; color:#142B2D; }
        .panel-heading { margin:10px 0; font-weight:700; color:#244144; }
        .auth-heading { margin:28px 0 18px; }
        .auth-heading h1 { margin:8px 0; font:700 2.1rem 'Space Grotesk',sans-serif; }
        .auth-heading p { color:#607477; }
        .forecast-result { margin-top:26px; padding:26px; border:1px solid #B8D8D5; border-left:4px solid #087E8B; border-radius:10px; background:#FFFFFF; }
        .forecast-number { color:#087E8B; font:700 3rem/1.1 'Space Grotesk',sans-serif; }
        .module-card { border-radius:10px; }
        .sidebar-brand { padding:4px 8px 18px; margin-bottom:14px; border-bottom:1px solid #D4E0DD; }
        .sidebar-section { margin:15px 8px 8px; color:#718486; font-size:.68rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
        .sidebar-user { padding:12px; margin:0 0 14px; border-radius:9px; background:#FFFFFF; border:1px solid #D7E3E0; }
        .page-hero { padding:22px 0 20px; margin-bottom:18px; border-bottom:1px solid #DCE6E4; }
        .page-hero h1 { margin:0 0 7px; font-size:2rem; color:#142B2D; }
        .page-hero p { margin:0; color:#607477; }
        .state-panel { padding:18px; border:1px solid #DCE6E4; border-radius:9px; background:#FFFFFF; color:#607477; }
        .metric-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
        @media (max-width: 800px) {
            .landing-hero { grid-template-columns:1fr; gap:28px; padding:34px 0 42px; }
            .feature-grid { grid-template-columns:1fr; }
            .landing-title { font-size:2.35rem; }
            .landing-footer { flex-direction:column; }
            .site-nav-links { gap:10px; }
        }
    </style>
    """, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str, badge: str = "Enterprise Engine"):
    from html import escape

    safe_title = escape(title)
    safe_subtitle = escape(subtitle)
    safe_badge = escape(badge)
    st.markdown(f"""
    <div class="premium-hero">
        <div style="margin-bottom: 8px;">
            <span class="pill-badge pill-staff">{safe_badge}</span>
        </div>
        <h1 style="font-size: 2.2rem; margin: 0 0 8px 0;">
            <span class="gradient-heading">{safe_title}</span>
        </h1>
        <p style="font-size: 1rem; color: #64748B; margin: 0; font-weight: 500;">
            {safe_subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_kpi(title: str, value: str, icon: str, color_scheme: str = "indigo", subtitle: str = ""):
    from html import escape

    safe_scheme = color_scheme if color_scheme in {"indigo", "cyan", "emerald", "amber"} else "cyan"
    title = escape(title)
    value = escape(value)
    icon = escape(icon)
    subtitle = escape(subtitle)
    subtitle_html = f'<div style="font-size:.75rem;color:#607477;margin-top:4px">{subtitle}</div>' if subtitle else ""
    icon_html = f'<div class="kpi-icon-badge icon-{safe_scheme}">{icon}</div>' if icon else ""
    markup = (
        f'<div class="kpi-container kpi-{safe_scheme}"><div>'
        f'<div class="kpi-title">{title}</div><div class="kpi-number">{value}</div>'
        f'{subtitle_html}</div>{icon_html}</div>'
    )
    st.markdown(markup, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = "", eyebrow: str = "Workspace"):
    from html import escape

    st.markdown(
        f'<header class="page-hero"><div class="eyebrow">{escape(eyebrow)}</div>'
        f'<h1>{escape(title)}</h1><p>{escape(subtitle)}</p></header>',
        unsafe_allow_html=True,
    )


def render_empty_state(message: str, detail: str = ""):
    from html import escape

    st.markdown(
        f'<div class="state-panel"><strong>{escape(message)}</strong>'
        f'{f"<div style=\'margin-top:6px\'>{escape(detail)}</div>" if detail else ""}</div>',
        unsafe_allow_html=True,
    )


def render_brand(compact: bool = False):
    brand = "<span class='brand-mark'><span class='brand-symbol'>A</span>AI Sales Analytics</span>"
    st.markdown(brand, unsafe_allow_html=True)


def render_sidebar(include_session_timer: bool = True):
    from html import escape
    from utils.api_client import APIClient
    from utils.session_timer import render_secure_session_timer

    user = st.session_state.get("user") or {}
    role = str(user.get("role", "analyst")).lower()
    name = user.get("full_name") or user.get("username") or "User"
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">', unsafe_allow_html=True)
        render_brand()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="sidebar-user"><strong>{escape(name)}</strong>'
            f'<div style="color:#607477;font-size:.82rem;margin-top:3px">{escape(role.title())}</div></div>',
            unsafe_allow_html=True,
        )
        if include_session_timer:
            render_secure_session_timer(width=220, component_key="sidebar_secure_session")
        st.markdown('<div class="sidebar-section">Workspace</div>', unsafe_allow_html=True)
        st.page_link("app.py", label="Dashboard", icon=":material/dashboard:")
        st.page_link("pages/5_Sales_Management.py", label="Sales Management", icon=":material/receipt_long:")
        st.page_link("pages/1_Products.py", label="Products", icon=":material/inventory_2:")
        st.page_link("pages/6_AI_Forecasting.py", label="AI Forecasting", icon=":material/auto_graph:")
        st.page_link("pages/7_Prediction_History.py", label="Prediction History", icon=":material/history:")
        st.page_link("pages/8_Model_Performance.py", label="Model Performance", icon=":material/monitoring:")
        st.markdown('<div class="sidebar-section">Account</div>', unsafe_allow_html=True)
        st.page_link("pages/2_Analytics.py", label="Analytics", icon=":material/analytics:")
        st.page_link("pages/3_Profile.py", label="Profile & Settings", icon=":material/person:")
        st.page_link("pages/9_Login_History.py", label="Login History", icon=":material/history:")
        if role in {"admin", "manager"}:
            st.page_link("pages/4_Audit_Logs.py", label="Audit Logs", icon=":material/policy:")
        if st.button("Sign out", key="sidebar_signout", use_container_width=True):
            try:
                APIClient.logout()
            except Exception:
                pass
            st.session_state.clear()
            st.session_state["auth_notice"] = "You have signed out."
            st.switch_page("app.py")

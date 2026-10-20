import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.api_client import APIClient
from utils.ui_theme import apply_custom_theme, render_hero, render_kpi, render_sidebar

st.set_page_config(page_title="Executive Analytics", page_icon="📈", layout="wide")
apply_custom_theme()

if not st.session_state.get("token"):
    st.switch_page("app.py")
    st.stop()

render_sidebar()

render_hero(
    title="Executive BI & Revenue Telemetry",
    subtitle="Trajectory modeling, margin distribution, category revenue splits, and elasticity analysis.",
    badge="Analytics OS"
)

st.write("---")

# =========================================================
# --- 1. Summary KPI Strip ---
# =========================================================
try:
    summary = APIClient.get_analytics_summary()
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi("Gross Revenue", f"${summary.get('total_revenue', 0.0):,.2f}", "💰", "indigo",
                   "Aggregate sales turnover")
    with k2:
        render_kpi("Processed Orders", f"{summary.get('total_sales_count', 0):,}", "📦", "cyan",
                   "Completed customer carts")
    with k3:
        render_kpi("Volume Dispatched", f"{summary.get('total_quantity_sold', 0):,}", "📊", "emerald",
                   "Total product items shipped")
    with k4:
        render_kpi("Average Ticket", f"${summary.get('average_order_value', 0.0):,.2f}", "⚡", "amber",
                   "Mean gross basket size")
except Exception as e:
    st.error(f"Failed to load executive summaries: {e}")

st.write("---")

# =========================================================
# --- 2. Monthly Growth & Velocity Chart (Fixed Syntax) ---
# =========================================================
st.markdown("### 📅 Monthly Growth & Transaction Velocity")
try:
    monthly_data = APIClient.get_monthly_sales()
    if monthly_data:
        df_monthly = pd.DataFrame(monthly_data)
        fig_monthly = go.Figure()

        fig_monthly.add_trace(go.Bar(
            x=df_monthly["month"],
            y=df_monthly["total_revenue"],
            name="Gross Revenue ($)",
            marker=dict(
                color=df_monthly["total_revenue"],
                colorscale="Purples",
                line=dict(color="#4F46E5", width=1.5)
            ),
            yaxis="y"
        ))

        fig_monthly.add_trace(go.Scatter(
            x=df_monthly["month"],
            y=df_monthly["total_orders"],
            name="Order Count",
            mode="lines+markers",
            line=dict(color="#EC4899", width=3, shape="spline"),
            marker=dict(size=8, color="#F43F5E"),
            yaxis="y2"
        ))

        fig_monthly.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,250,252,0.8)",
            yaxis=dict(
                title=dict(text="Revenue ($)", font=dict(color="#4F46E5")),
                gridcolor="#E2E8F0"
            ),
            yaxis2=dict(
                title=dict(text="Orders Placed", font=dict(color="#EC4899")),
                overlaying="y",
                side="right",
                showgrid=False
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=30, b=20),
            height=380,
            hovermode="x unified"
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
    else:
        st.info("No transaction ledger records logged yet.")
except Exception as e:
    st.error(f"Error loading trajectory charts: {e}")

st.write("---")

# =========================================================
# --- 3. Product Ranking & Category Split Charts ---
# =========================================================
c_left, c_right = st.columns([1.1, 0.9])

with c_left:
    st.markdown("### 🏆 Top Performing Products")
    sort_option = st.selectbox(
        "Ordering Metric",
        ["Revenue (High to Low)", "Revenue (Low to High)", "Volume (High to Low)", "Volume (Low to High)"]
    )
    sort_map = {
        "Revenue (High to Low)": "revenue_desc",
        "Revenue (Low to High)": "revenue_asc",
        "Volume (High to Low)": "volume_desc",
        "Volume (Low to High)": "volume_asc",
    }

    try:
        prod_analytics = APIClient.get_products_analytics(sort_by=sort_map[sort_option], limit=10)
        if prod_analytics:
            df_prod = pd.DataFrame(prod_analytics)
            y_col = "total_revenue" if "Revenue" in sort_option else "total_quantity_sold"
            y_title = "Revenue ($)" if "Revenue" in sort_option else "Units Sold"

            fig_prod = px.bar(
                df_prod,
                x=y_col,
                y="product_name",
                orientation="h",
                color="category",
                color_discrete_sequence=px.colors.qualitative.Safe,
                labels={"product_name": "Product", y_col: y_title}
            )
            fig_prod.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(248,250,252,0.8)",
                yaxis=dict(autorange="reversed", gridcolor="#E2E8F0"),
                xaxis=dict(gridcolor="#E2E8F0"),
                height=400,
                margin=dict(l=10, r=10, t=20, b=20)
            )
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.info("No product sales data available.")
    except Exception as e:
        st.error(f"Error rendering rank chart: {e}")

with c_right:
    st.markdown("### 🥧 Category Revenue Split")
    try:
        cat_analytics = APIClient.get_categories_analytics()
        if cat_analytics:
            df_cat = pd.DataFrame(cat_analytics)
            fig_cat = px.pie(
                df_cat,
                names="category",
                values="total_revenue",
                hole=0.55,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_cat.update_traces(
                textposition="inside",
                textinfo="percent+label",
                marker=dict(line=dict(color="#FFFFFF", width=2))
            )
            fig_cat.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                height=400,
                margin=dict(l=10, r=10, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No category analytics records.")
    except Exception as e:
        st.error(f"Error generating category split: {e}")

st.write("---")

# =========================================================
# --- 4. Elasticity & Scatter Analysis ---
# =========================================================
st.markdown("### 🔬 Price Elasticity & Sales Density")
try:
    all_prods = APIClient.get_products_analytics(limit=100)
    if all_prods:
        df_scatter = pd.DataFrame(all_prods)
        df_scatter["plot_size"] = df_scatter["total_revenue"].apply(lambda v: max(float(v or 0.0), 8.0))
        fig_scatter = px.scatter(
            df_scatter,
            x="base_price",
            y="total_quantity_sold",
            size="plot_size",
            color="category",
            hover_name="product_name",
            hover_data={"plot_size": False, "total_revenue": ":$.2f", "base_price": ":$.2f",
                        "total_quantity_sold": True},
            color_discrete_sequence=px.colors.qualitative.Vivid,
            labels={"base_price": "Unit Price ($)", "total_quantity_sold": "Units Sold"}
        )
        fig_scatter.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,250,252,0.8)",
            xaxis=dict(gridcolor="#E2E8F0"),
            yaxis=dict(gridcolor="#E2E8F0"),
            height=440,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
except Exception as e:
    st.error(f"Error loading elasticity visualization: {e}")
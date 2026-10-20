import os
import sys
from html import escape
import streamlit as st
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.api_client import APIClient, APIError
from utils.ui_theme import apply_custom_theme, render_hero, render_sidebar

st.set_page_config(page_title="Product Inventory & Sales Dispatch", page_icon="📦", layout="wide")
apply_custom_theme()

if not st.session_state.get("token"):
    st.switch_page("app.py")
    st.stop()

render_sidebar()

user = st.session_state.get("user") or {}
user_role = str(user.get("role", "staff")).lower()
can_edit = user_role in ["admin", "manager"]

render_hero(
    title="Inventory Catalog & Transaction Engine",
    subtitle="Configure catalog items, adjust unit base prices, dispatch customer checkouts, and inspect stock.",
    badge="Inventory Engine"
)

# Workspace Action Tabs
tab_catalog, tab_pos = st.tabs(["📋 Catalog Explorer & Editor", "🛒 Dispatch New Sale (POS)"])

with tab_pos:
    st.markdown("### ⚡ Fast Checkout & Transaction Recording")
    try:
        active_items = APIClient.get_products(active_status=True, limit=200) or []
    except Exception as e:
        st.error(f"Failed to fetch active products: {e}")
        active_items = []

    if not active_items:
        st.warning("No active products currently available in inventory.")
    else:
        product_options = {p["product_id"]: f"{p['product_name']} (${float(p['base_price']):,.2f})" for p in active_items}
        with st.form("pos_sale_form"):
            selected_pid = st.selectbox("Select Product", options=list(product_options.keys()), format_func=lambda pid: product_options[pid])
            matched_prod = next((p for p in active_items if p["product_id"] == selected_pid), None)
            
            p_c1, p_c2, p_c3 = st.columns(3)
            with p_c1:
                qty = st.number_input("Units Quantity", min_value=1, max_value=500, value=1, step=1)
            with p_c2:
                default_price = float(matched_prod["base_price"]) if matched_prod else 0.0
                unit_price = st.number_input("Unit Price ($)", min_value=0.0, value=default_price, step=0.5)
            with p_c3:
                discount = st.number_input("Discount Amount ($)", min_value=0.0, value=0.0, step=0.5)
            
            computed_total = max(0.0, (qty * unit_price) - discount)
            st.markdown(f"**Gross Order Total:** `${computed_total:,.2f}`")

            if st.form_submit_button("💳 Commit Sale Transaction", use_container_width=True):
                try:
                    APIClient.record_sale({
                        "product_id": selected_pid,
                        "quantity": qty,
                        "unit_price": unit_price,
                        "discount_amount": discount
                    })
                    st.toast("🎉 Sale successfully recorded in transaction ledger!", icon="✅")
                    st.rerun()
                except APIError as e:
                    st.error(f"Sale recording failed: {e.message}")

with tab_catalog:
    st.markdown("### 🔍 Filter Inventory")
    f1, f2, f3 = st.columns([2, 1, 1])

    with f1:
        search_query = st.text_input("Search catalog items", placeholder="Search by name, SKU, specifications...")
    with f2:
        status_filter = st.selectbox("Active State", ["All Items", "Active Only", "Inactive Only"])
        active_bool = None
        if status_filter == "Active Only":
            active_bool = True
        elif status_filter == "Inactive Only":
            active_bool = False

    try:
        products_raw = APIClient.get_products(active_status=active_bool, search=search_query if search_query else None) or []
        categories = sorted(list(set(str(p.get("category", "")) for p in products_raw if p.get("category"))))
    except Exception as e:
        st.error(f"Failed to fetch catalog: {e}")
        products_raw = []
        categories = []

    with f3:
        selected_category = st.selectbox("Taxonomy Category", ["All Categories"] + categories)

    if selected_category != "All Categories":
        products = [p for p in products_raw if p.get("category") == selected_category]
    else:
        products = products_raw

    active_count = sum(1 for p in products if p.get("active_status", False))
    inactive_count = len(products) - active_count

    st.markdown(f"""
    <div style="display: flex; gap: 12px; margin-bottom: 20px;">
        <span class="pill-badge pill-staff">Results: {len(products)}</span>
        <span class="pill-badge pill-prod">Active: {active_count}</span>
        <span class="pill-badge pill-inactive">Inactive: {inactive_count}</span>
    </div>
    """, unsafe_allow_html=True)

    if can_edit:
        with st.expander("✨ + Provision New Catalog Item", expanded=False):
            with st.form("create_product_form"):
                st.markdown("##### Specifications")
                c1, c2 = st.columns(2)
                with c1:
                    new_name = st.text_input("Product Name *", placeholder="e.g. UltraHD Smart Monitor")
                    new_cat = st.text_input("Category *", placeholder="e.g. Electronics, Furniture")
                with c2:
                    new_price = st.number_input("Base Price ($) *", min_value=0.0, step=0.5, value=29.99)
                    new_active = st.checkbox("Available for checkout", value=True)
                new_desc = st.text_area("Specification Description", placeholder="Comprehensive item details...")
                
                if st.form_submit_button("🚀 Publish to Catalog", use_container_width=True):
                    if not new_name.strip() or not new_cat.strip():
                        st.error("Both product name and category are required.")
                    else:
                        try:
                            APIClient.create_product({
                                "product_name": new_name.strip(),
                                "category": new_cat.strip(),
                                "base_price": float(new_price),
                                "description": new_desc.strip(),
                                "active_status": new_active
                            })
                            st.toast("Item added to catalog!", icon="📦")
                            st.rerun()
                        except APIError as e:
                            st.error(e.message)

    if not products:
        st.info("No products match the selected filters.")
    else:
        df = pd.DataFrame(products)
        required_cols = ["product_id", "product_name", "category", "base_price", "active_status", "created_at"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        display_df = df[required_cols].copy()
        display_df["base_price"] = display_df["base_price"].apply(lambda x: f"${float(x or 0):,.2f}")
        display_df["active_status"] = display_df["active_status"].apply(lambda x: "🟢 Active" if x else "🔴 Inactive")
        display_df.columns = ["ID", "Product Name", "Category", "Price", "Status", "Created At"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.write("---")
        st.markdown("### 🛠️ Interactive Product Editor")

        for prod in products:
            prod_id = prod.get("product_id")
            prod_name = prod.get("product_name", "Unnamed Item")
            prod_cat = prod.get("category", "Uncategorized")
            prod_active = bool(prod.get("active_status", False))
            prod_price = float(prod.get("base_price") or 0.0)
            safe_name = escape(str(prod_name))
            safe_category = escape(str(prod_cat))
            safe_description = escape(str(prod.get("description") or "No description provided."))

            status_tag = '<span class="pill-badge pill-active">🟢 Active</span>' if prod_active else '<span class="pill-badge pill-inactive">🔴 Inactive</span>'
            expander_title = f"#{prod_id} | {prod_name} — ${prod_price:,.2f} ({prod_cat})"
            
            with st.expander(expander_title, expanded=False):
                info_col, action_col = st.columns([1.5, 2])
                with info_col:
                    st.markdown(f"""
                    <div style="background: #F8FAFC; border-radius: 12px; padding: 18px; border: 1px solid #E2E8F0;">
                        <div style="margin-bottom: 8px;">{status_tag} <span class="pill-badge pill-staff">{safe_category}</span></div>
                        <div style="font-weight: 700; font-size: 1.15rem; color: #0F172A;">{safe_name}</div>
                        <div style="font-size: 1.35rem; font-weight: 800; color: #4F46E5; margin: 4px 0;">${prod_price:,.2f}</div>
                        <p style="font-size: 0.85rem; color: #64748B; margin-top: 8px;">{safe_description}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with action_col:
                    if can_edit:
                        with st.form(f"edit_form_{prod_id}"):
                            st.markdown("##### ✏️ Modify Details")
                            e1, e2 = st.columns(2)
                            with e1:
                                edit_name = st.text_input("Name", value=prod_name, key=f"n_{prod_id}")
                                edit_cat = st.text_input("Category", value=prod_cat, key=f"c_{prod_id}")
                            with e2:
                                edit_price = st.number_input("Price ($)", min_value=0.0, step=0.5, value=max(0.0, prod_price), key=f"p_{prod_id}")
                                edit_active = st.checkbox("Active Status", value=prod_active, key=f"a_{prod_id}")
                            edit_desc = st.text_area("Description", value=prod.get('description') or '', key=f"d_{prod_id}")
                            
                            if st.form_submit_button("💾 Save Updates", use_container_width=True):
                                try:
                                    APIClient.update_product(prod_id, {
                                        "product_name": edit_name.strip(),
                                        "category": edit_cat.strip(),
                                        "base_price": float(edit_price),
                                        "description": edit_desc.strip(),
                                        "active_status": edit_active
                                    })
                                    st.toast("Product parameters updated!", icon="💾")
                                    st.rerun()
                                except APIError as e:
                                    st.error(e.message)
                        
                        if prod_active:
                            if st.button("🚫 Deactivate (Soft Delete)", key=f"del_{prod_id}", use_container_width=True):
                                try:
                                    APIClient.delete_product(prod_id)
                                    st.toast(f"Product #{prod_id} deactivated.", icon="🚫")
                                    st.rerun()
                                except APIError as e:
                                    st.error(e.message)
                    else:
                        st.info("Staff role has read-only privileges.")

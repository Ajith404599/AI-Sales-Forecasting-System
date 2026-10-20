from datetime import date, datetime, time
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

from utils.api_client import APIClient, APIError
from utils.page_helpers import setup_authenticated_page
from utils.ui_theme import render_empty_state

user = setup_authenticated_page(
    "Sales Management",
    "Sales Management",
    "Record and maintain transactions connected to the existing product catalog.",
    "Sales operations",
)
role = str(user.get("role", "analyst")).lower()
user_id = user.get("user_id")
can_manage_all = role in {"admin", "manager"}

try:
    products = APIClient.get_products(limit=200) or []
except Exception as error:
    st.error(f"Product catalog is unavailable: {error}")
    products = []
product_by_id = {product["product_id"]: product for product in products}
active_products = [product for product in products if product.get("active_status")]

add_tab, list_tab = st.tabs(["Add sale", "View sales"])
with add_tab:
    st.markdown("#### New transaction")
    if not active_products:
        render_empty_state("No active products available", "Activate a product in the existing Products workspace before recording a sale.")
    else:
        options = {product["product_id"]: f"{product['product_name']} · ${float(product['base_price']):,.2f}" for product in active_products}
        with st.form("create_sale_form"):
            first_row, second_row = st.columns(2)
            with first_row:
                selected_product_id = st.selectbox("Product", list(options), format_func=lambda key: options[key])
                quantity = st.number_input("Quantity", min_value=1, max_value=100000, value=1, step=1)
                sale_day = st.date_input("Sale date", value=date.today())
            with second_row:
                selected_product = product_by_id[selected_product_id]
                unit_price = st.number_input("Unit / selling price", min_value=0.01, value=float(selected_product["base_price"]), step=1.0, format="%.2f")
                discount = st.number_input("Discount amount", min_value=0.0, value=0.0, step=1.0, format="%.2f")
                sale_time = st.time_input("Sale time", value=datetime.now().time().replace(second=0, microsecond=0))
            total_amount = max(0.0, quantity * unit_price - discount)
            st.metric("Calculated total", f"${total_amount:,.2f}")
            submitted = st.form_submit_button("Record sale", type="primary", use_container_width=True)
            if submitted:
                try:
                    payload = {
                        "product_id": selected_product_id,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "discount_amount": discount,
                        "sale_date": datetime.combine(sale_day, sale_time).isoformat(),
                    }
                    APIClient.record_sale(payload)
                    st.success("Sale recorded.")
                    st.rerun()
                except APIError as error:
                    st.error(error.message)
                except Exception as error:
                    st.error(f"Could not record the sale: {error}")

with list_tab:
    st.markdown("#### Sales ledger")
    filter_cols = st.columns([1.7, 1, 1, 1, 1])
    with filter_cols[0]:
        search = st.text_input("Search product or sale ID", placeholder="Product name, category, or ID")
    with filter_cols[1]:
        product_filter = st.selectbox("Product filter", [None] + list(product_by_id), format_func=lambda key: "All products" if key is None else product_by_id[key]["product_name"])
    with filter_cols[2]:
        start_date = st.date_input("From", value=None, key="sales_start_date")
    with filter_cols[3]:
        end_date = st.date_input("To", value=None, key="sales_end_date")
    with filter_cols[4]:
        page_size = st.selectbox("Rows", [25, 50, 100, 200], index=1)

    start_iso = datetime.combine(start_date, time.min).isoformat() if start_date else None
    end_iso = datetime.combine(end_date, time.max).isoformat() if end_date else None
    try:
        sales = APIClient.get_sales(
            product_id=product_filter,
            start_date=start_iso,
            end_date=end_iso,
            search=search.strip() or None,
            limit=page_size,
        ) or []
    except APIError as error:
        st.error(error.message)
        sales = []
    except Exception as error:
        st.error(f"Could not load the sales ledger: {error}")
        sales = []

    if sales:
        sales_frame = pd.DataFrame(sales)
        sales_frame["product"] = sales_frame["product_id"].map(
            lambda product_id: product_by_id.get(product_id, {}).get("product_name", f"Product #{product_id}")
        )
        sales_frame["sale_date"] = pd.to_datetime(sales_frame["sale_date"], errors="coerce")
        visible = sales_frame[["sale_id", "product", "quantity", "unit_price", "discount_amount", "total_amount", "sale_date", "user_id"]].copy()
        visible.columns = ["Sale ID", "Product", "Quantity", "Unit price", "Discount", "Total", "Sale date", "User ID"]
        st.dataframe(visible, use_container_width=True, hide_index=True, column_config={
            "Unit price": st.column_config.NumberColumn(format="$%.2f"),
            "Discount": st.column_config.NumberColumn(format="$%.2f"),
            "Total": st.column_config.NumberColumn(format="$%.2f"),
            "Sale date": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm"),
        })
        st.caption(f"Showing {len(sales)} matching sale(s).")
    else:
        render_empty_state("No sales match these filters", "Try a wider date range or record a new sale.")

    editable_sales = [sale for sale in sales if can_manage_all or sale.get("user_id") == user_id]
    if editable_sales:
        st.markdown("#### Update a sale")
        sale_options = {sale["sale_id"]: sale for sale in editable_sales}
        edit_id = st.selectbox("Sale to update", list(sale_options), format_func=lambda key: f"Sale #{key} · {product_by_id.get(sale_options[key]['product_id'], {}).get('product_name', 'Product')} · {sale_options[key]['sale_date']}")
        current_sale = sale_options[edit_id]
        active_options = {product["product_id"]: product["product_name"] for product in products if product.get("active_status") or product["product_id"] == current_sale["product_id"]}
        with st.form(f"update_sale_{edit_id}"):
            edit_cols = st.columns(3)
            with edit_cols[0]:
                edit_product = st.selectbox("Product", list(active_options), index=list(active_options).index(current_sale["product_id"]), format_func=lambda key: active_options[key])
                edit_quantity = st.number_input("Quantity", min_value=1, value=int(current_sale["quantity"]), step=1)
            with edit_cols[1]:
                edit_price = st.number_input("Unit / selling price", min_value=0.01, value=float(current_sale["unit_price"]), step=1.0, format="%.2f")
                edit_discount = st.number_input("Discount", min_value=0.0, value=float(current_sale.get("discount_amount") or 0), step=1.0, format="%.2f")
            with edit_cols[2]:
                current_datetime = datetime.fromisoformat(current_sale["sale_date"])
                edit_day = st.date_input("Sale date", value=current_datetime.date())
                edit_time = st.time_input("Sale time", value=current_datetime.time().replace(tzinfo=None, second=0, microsecond=0))
            updated_total = max(0.0, edit_quantity * edit_price - edit_discount)
            st.metric("Recalculated total", f"${updated_total:,.2f}")
            update_col, delete_col = st.columns([1, 1])
            with update_col:
                update_clicked = st.form_submit_button("Save changes", type="primary", use_container_width=True)
            with delete_col:
                delete_clicked = st.form_submit_button("Delete sale", disabled=not can_manage_all, use_container_width=True)
            if update_clicked:
                try:
                    APIClient.update_sale(edit_id, {
                        "product_id": edit_product,
                        "quantity": edit_quantity,
                        "unit_price": edit_price,
                        "discount_amount": edit_discount,
                        "sale_date": datetime.combine(edit_day, edit_time).isoformat(),
                    })
                    st.success("Sale updated.")
                    st.rerun()
                except APIError as error:
                    st.error(error.message)
            if delete_clicked and can_manage_all:
                st.session_state["delete_sale_pending"] = edit_id
                st.rerun()

    pending_delete = st.session_state.get("delete_sale_pending")
    if pending_delete and can_manage_all:
        st.warning(f"Delete sale #{pending_delete}? This action cannot be undone.")
        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            if st.button("Confirm delete", key="confirm_sale_delete", type="primary"):
                try:
                    APIClient.delete_sale(pending_delete)
                    st.session_state.pop("delete_sale_pending", None)
                    st.success("Sale deleted.")
                    st.rerun()
                except APIError as error:
                    st.error(error.message)
        with cancel_col:
            if st.button("Cancel", key="cancel_sale_delete"):
                st.session_state.pop("delete_sale_pending", None)
                st.rerun()

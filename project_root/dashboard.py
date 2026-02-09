from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from src.ml_models.data import load_latest_model_info
from src.ml_models.predict import forecast_product
from src.visualization.components import (
    render_bbce_product_page,
    render_bbce_prices_with_table,
    render_forecast_cards,
    render_generation_history_charts,
    render_header,
    render_indicator_weeks,
    render_selectors,
)
from src.visualization.ui import get_viewport_width, inject_global_ui, panel_close, panel_open
from src.visualization.data import (
    get_bbce_products,
    get_bbce_prices_for_products,
    get_bso_week_data,
    get_last_update,
    get_operational_weeks,
    get_cmo_pld_week,
    get_operational_weeks_table,
    get_bso_history,
    pick_bbce_product,
)


st.set_page_config(
    page_title="Dashboard Energético Brasileiro",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_ui()

st.markdown(
    """
<style>
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--panel2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 14px 16px;
  box-shadow: var(--shadow);
}
.scenario-card {
  background: var(--table-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 12px;
}
.scenario-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text);
}
.scenario-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-table);
  table-layout: fixed;
}
.scenario-table th {
  text-align: center;
  padding: 6px 6px;
  color: var(--muted);
  font-weight: 600;
  border-bottom: 1px solid #1f2937;
  white-space: nowrap;
}
.scenario-table td {
  padding: 6px 6px;
  border-bottom: 1px solid #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.scenario-table .row-label {
  text-align: left;
  color: var(--text);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
@media (max-width: 1100px) {
  .scenario-card { padding: 10px 10px; }
  /* Reduce ~50% further vs previous non-wide size to avoid wraps. */
  .scenario-table { font-size: var(--fs-table-compact); }
  .scenario-table th { padding: 2px 3px; }
  .scenario-table td { padding: 2px 3px; }
  /* Reduce plotly text size on smaller layouts without changing wide mode. */
  .stPlotlyChart svg text { font-size: 7px !important; }
}
</style>
""",
    unsafe_allow_html=True,
)

weeks = get_operational_weeks(limit=10)
products = get_bbce_products(limit=200)

# Route to the BBCE product detail "page" via query params (hides the main dashboard UI).
try:
    _qp_view = st.query_params.get("bbce_view")
    _qp_prod = st.query_params.get("bbce_prod")
    _qp_anchor = st.query_params.get("bbce_anchor")
except Exception:
    _qp_view = None
    _qp_prod = None
    _qp_anchor = None

if isinstance(_qp_view, list):
    _qp_view = _qp_view[0] if _qp_view else None
if isinstance(_qp_prod, list):
    _qp_prod = _qp_prod[0] if _qp_prod else None
if isinstance(_qp_anchor, list):
    _qp_anchor = _qp_anchor[0] if _qp_anchor else None

_qp_view = str(_qp_view or "")
_qp_prod = str(_qp_prod or "")
_qp_anchor = str(_qp_anchor or "")

if _qp_view == "product" and _qp_prod:
    # If anchor not provided, anchor on the most recent BSO week (keeps consistency).
    if weeks:
        bso_tmp = get_bso_week_data(weeks[0])
        base_week_start = pd.to_datetime(bso_tmp["data_inicio"].iloc[0]).date() if not bso_tmp.empty else pd.Timestamp.today().date()
    else:
        base_week_start = pd.Timestamp.today().date()

    try:
        anchor_dt = pd.to_datetime(_qp_anchor, format="%Y%m%d").date() if _qp_anchor else base_week_start
    except Exception:
        anchor_dt = base_week_start

    viewport_w = get_viewport_width()

    panel_open(520)
    render_bbce_product_page(_qp_prod, anchor_dt, viewport_width=viewport_w, all_products=products)
    panel_close()
    st.stop()

# Normal dashboard flow (header + selectors).
panel_open(0)
render_header(last_update=get_last_update())
panel_close()

if not weeks or not products:
    st.info("Carregue os dados no banco para habilitar o dashboard.")
    st.stop()

week, product = render_selectors(weeks, products[:20])
viewport_w = get_viewport_width()

bso_current = get_bso_week_data(week)
if bso_current.empty:
    st.info("Sem dados de BSO para a semana selecionada.")
    st.stop()

base_week_start = pd.to_datetime(bso_current["data_inicio"].iloc[0]).date()
base_week_end = pd.to_datetime(bso_current["data_fim"].iloc[0]).date()

cmo_pld = None
data_inicio = str(bso_current["data_inicio"].iloc[0])
cmo_pld = get_cmo_pld_week(data_inicio)

model_info = load_latest_model_info(product)
predictions = forecast_product(product, [1, 4, 12], anchor_date=base_week_start)

panel_open(80)
render_forecast_cards(predictions, base_week_start=base_week_start, model_info=model_info)
panel_close()

# Module 2: scenario (S-2, S-1, S) grouped by submarket.
weeks_table = get_operational_weeks_table(limit=200)
idx = weeks_table.index[weeks_table["bso_week"] == week].tolist()
week_blocks = []
if idx:
    i0 = idx[0]
    # We fetch 3 display weeks + 1 extra older week to compute delta for S-2.
    # weeks_table is ordered desc, so this is [S, S-1, S-2, S-3]
    picked = weeks_table.iloc[i0 : i0 + 4].copy()
    picked = picked.reset_index(drop=True)

    bso_by_week = {}
    cmo_by_start = {}
    for w in picked["bso_week"].tolist():
        bso_by_week[w] = get_bso_week_data(w)
        if not bso_by_week[w].empty:
            start = str(bso_by_week[w]["data_inicio"].iloc[0])
            cmo_by_start[start] = get_cmo_pld_week(start)

    # Display order: [S-2, S-1, S]
    display_weeks = []
    if len(picked) >= 3:
        display_weeks = [picked.loc[2, "bso_week"], picked.loc[1, "bso_week"], picked.loc[0, "bso_week"]]

    def _week_label(df: pd.DataFrame) -> str:
        start = pd.to_datetime(df["data_inicio"].iloc[0]).date()
        end = pd.to_datetime(df["data_fim"].iloc[0]).date()
        return f"{start:%d.%m} a {end:%d.%m}"

    # Build blocks in display order with compare pointing to the immediately older week.
    for w in display_weeks:
        bso_df = bso_by_week.get(w, pd.DataFrame())
        if bso_df.empty:
            continue

        compare_bso = None
        compare_cmo = None
        # Find the next older week for deltas (e.g. S compares to S-1).
        # picked is [S, S-1, S-2, S-3]
        if w == picked.loc[0, "bso_week"] and len(picked) >= 2:
            compare_bso = bso_by_week.get(picked.loc[1, "bso_week"])
        elif w == picked.loc[1, "bso_week"] and len(picked) >= 3:
            compare_bso = bso_by_week.get(picked.loc[2, "bso_week"])
        elif w == picked.loc[2, "bso_week"] and len(picked) >= 4:
            compare_bso = bso_by_week.get(picked.loc[3, "bso_week"])

        if compare_bso is not None and not compare_bso.empty:
            prev_start = str(compare_bso["data_inicio"].iloc[0])
            compare_cmo = cmo_by_start.get(prev_start)

        start_key = str(bso_df["data_inicio"].iloc[0])
        week_blocks.append(
            {
                "label": _week_label(bso_df),
                "bso": bso_df,
                "cmo_pld": cmo_by_start.get(start_key),
                "compare_bso": compare_bso,
                "compare_cmo_pld": compare_cmo,
            }
        )

panel_open(160)
render_indicator_weeks(week_blocks)
panel_close()

# Module 3: BBCE products (fixed logic anchored to the operational week end-year/period).
# For weeks crossing year boundary (e.g. 27/12 to 02/01), this treats the week as the end year.
op_year = base_week_end.year
op_month = base_week_end.month

# 4 annual products: op_year+1 .. op_year+4
annual_products = []
for yr in range(op_year + 1, op_year + 5):
    p = pick_bbce_product("ANU", yr, 1, 12)
    if p:
        annual_products.append(p)

# 2 semester products: next 2 semesters after current one
sem_products = []
current_sem = 1 if op_month <= 6 else 2
if current_sem == 1:
    sem_defs = [(op_year, 7, 12), (op_year + 1, 1, 6)]
else:
    sem_defs = [(op_year + 1, 1, 6), (op_year + 1, 7, 12)]
for yr, mi, mf in sem_defs:
    p = pick_bbce_product("SEM", yr, mi, mf)
    if p:
        sem_products.append(p)

# 2 quarter products: next 2 quarters after current one
tri_products = []
current_q = (op_month - 1) // 3 + 1
q_defs = []
q = current_q
yr = op_year
for _ in range(2):
    q += 1
    if q == 5:
        q = 1
        yr += 1
    mi = 1 + (q - 1) * 3
    mf = mi + 2
    q_defs.append((yr, mi, mf))
for yr, mi, mf in q_defs:
    p = pick_bbce_product("TRI", yr, mi, mf)
    if p:
        tri_products.append(p)

start_hist = str(base_week_start - timedelta(weeks=10))
end_hist = str(base_week_end)

panel_open(240)
# Exactly: 4 annual + 2 semi + 2 tri (per spec).
combined_products = []
for p in (annual_products + sem_products + tri_products):
    if p and p not in combined_products:
        combined_products.append(p)

if combined_products:
    df_all = get_bbce_prices_for_products(combined_products, start_hist, end_hist)
    render_bbce_prices_with_table(
        df_all,
        base_week_start,
        title="Preços Médios BBCE (R$/MWh)",
        viewport_width=viewport_w,
    )
panel_close()

# Module 4: history charts from BSO (10 weeks anchored at selected week).
bso_history = get_bso_history(anchor_start=str(base_week_start), weeks_back=10)
panel_open(320)
render_generation_history_charts(
    bso_history,
    bso_current=bso_current,
    week_label=f"{base_week_start:%d.%m} a {base_week_end:%d.%m}",
    viewport_width=viewport_w,
)
panel_close()

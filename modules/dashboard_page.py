import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    Employee, CountMaster, DailyProduction
)

# --------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------
def dashboard_page():

    st.markdown("""
    <style>
    .block-container { padding-top: 0.6rem; padding-bottom: 0.4rem; }

    div[data-testid="stDataFrame"] {
        overflow-x: auto;
    }

    div[data-testid="stDataFrame"] thead th {
        position: sticky;
        top: 0;
        background: #f9fafb;
        z-index: 5;
    }

    div[data-testid="stDataFrame"] tbody tr td:first-of-type,
    div[data-testid="stDataFrame"] thead tr th:first-of-type {
        position: sticky;
        left: 0;
        background: white;
        z-index: 6;
        font-weight: 600;
        border-right: 1px solid #e5e7eb;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📊 Production Dashboard")

    session: Session = next(get_session())

    # ---------------- FILTERS ----------------
    c1, c2, c3, c4 = st.columns(4)

    date = c1.date_input("Date")

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = c2.selectbox("Mill", [None] + list(mill_map), format_func=lambda x: "All" if x is None else mill_map[x])

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = c3.selectbox("Department", [None] + list(dept_map), format_func=lambda x: "All" if x is None else dept_map[x])

    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = c4.selectbox("Shift", [None] + list(shift_map), format_func=lambda x: "All" if x is None else shift_map[x])

    st.divider()

    # ---------------- QUERY ----------------
    q = session.query(DailyProduction).filter(DailyProduction.date == date)

    if mill_id:
        q = q.filter(DailyProduction.mill_id == mill_id)
    if dept_id:
        q = q.filter(DailyProduction.department_id == dept_id)
    if shift_id:
        q = q.filter(DailyProduction.shift_id == shift_id)

    rows = q.all()

    if not rows:
        st.warning("No records found.")
        return

    # ---------------- BUILD DATAFRAME ----------------
    data = []

    for r in rows:
        machine = session.get(Machine, r.machine_id)
        count = session.get(CountMaster, r.count_id)

        # ✅ RECOMPUTE ALWAYS (DO NOT TRUST STORED)
        std_gps = (r.target_kgs / r.spindles * 1000) if r.spindles else 0
        actual_gps = (r.actual_prdn / r.worked_spindles * 1000) if r.worked_spindles else 0
        diff_gps = actual_gps - std_gps
        conv_40s_gps = actual_gps * (count.conv_40s_factor if count else 0)

        data.append({
            "Machine": machine.machine_name if machine else "",

            "Spindles": r.spindles,
            "Count": count.count_name if count else "",
            "Speed": r.spdl_speed,
            "TPI": r.tpi,
            "Std Hank": r.std_hank,

            "Worked Spindles": r.worked_spindles,
            "Target Kgs": r.target_kgs,

            "Actual Hank": r.act_hank,
            "Stop Min": r.stop_min,
            "Prod Kgs": r.prod_kgs,
            "Pne Bondas": r.pne_bondas,

            "Actual Production": r.actual_prdn,
            "Waste %": r.waste_percent,

            "Std GPS": std_gps,
            "Actual GPS": actual_gps,
            "Diff (+/-)": diff_gps,
            "40s Conv GPS": conv_40s_gps,

            "W.O.H": r.woh,
            "MW": r.mw,
            "CLG/LC": r.clg_lc,
            "ER": r.er,
            "LA,PF": r.la_pf,
            "BSS": r.bss,
            "LAP": r.lap,
            "DD": r.dd,
            "Total Loss": r.total_loss,
        })

    df = pd.DataFrame(data)

    numeric_cols = df.select_dtypes(include=["float", "int"]).columns

    st.dataframe(
        df.style.format({c: "{:.2f}" for c in numeric_cols}),
        use_container_width=True,
        height=650
    )

    # ---------------- SUMMARY ----------------
    st.divider()
    st.subheader("📌 Production Summary")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("🎯 Total Target Kgs", round(df["Target Kgs"].sum(), 2))
        st.metric("⚙️ Total Prod Kgs", round(df["Prod Kgs"].sum(), 2))

    with c2:
        st.metric("📦 Actual Production", round(df["Actual Production"].sum(), 2))
        st.metric("🧵 Total Pne Bondas", round(df["Pne Bondas"].sum(), 2))

    with c3:
        st.metric("⏱️ Total Stop Minutes", round(df["Stop Min"].sum(), 2))
        st.metric("♻️ Avg Waste %", round(df["Waste %"].mean(), 2))

    # ---------------- LOSS SUMMARY ----------------
    st.subheader("📉 Loss Summary")

    loss_cols = ["W.O.H", "MW", "CLG/LC", "ER", "LA,PF", "BSS", "LAP", "DD"]

    loss_df = pd.DataFrame(
        [{"Loss Type": col, "Total": round(df[col].sum(), 2)} for col in loss_cols]
    )

    st.dataframe(loss_df, use_container_width=True)

    st.metric("🔻 Total Loss", round(df["Total Loss"].sum(), 2))

    # ---------------- EXPORT ----------------
    st.download_button(
        "⬇ Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        "dashboard_export.csv",
        "text/csv"
    )
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    Employee, CountMaster, DailyProduction
)

def dashboard_page():

    st.markdown("## 📊 Production Dashboard")
    session: Session = next(get_session())

    # ---------------- FILTER PANEL ----------------
    col1, col2, col3, col4 = st.columns(4)

    date = col1.date_input("Date (optional)", value=None)

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = col2.selectbox("Mill", [None] + list(mill_map.keys()),
                             format_func=lambda x: "All" if x is None else mill_map[x])

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = col3.selectbox("Department", [None] + list(dept_map.keys()),
                             format_func=lambda x: "All" if x is None else dept_map[x])

    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = col4.selectbox("Shift", [None] + list(shift_map.keys()),
                              format_func=lambda x: "All" if x is None else shift_map[x])

    col5, col6 = st.columns(2)

    employees = session.query(Employee).all()
    emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
    emp_id = col5.selectbox("Employee", [None] + list(emp_map.keys()),
                            format_func=lambda x: "All" if x is None else emp_map[x])

    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}
    count_id = col6.selectbox("Count", [None] + list(count_map.keys()),
                              format_func=lambda x: "All" if x is None else count_map[x])

    st.divider()

    # ---------------- QUERY ----------------
    q = session.query(DailyProduction)

    if date:
        q = q.filter(DailyProduction.date == date)
    if mill_id:
        q = q.filter(DailyProduction.mill_id == mill_id)
    if dept_id:
        q = q.filter(DailyProduction.department_id == dept_id)
    if shift_id:
        q = q.filter(DailyProduction.shift_id == shift_id)
    if emp_id:
        q = q.filter(DailyProduction.employee_id == emp_id)
    if count_id:
        q = q.filter(DailyProduction.count_id == count_id)

    rows = q.order_by(DailyProduction.date, DailyProduction.shift_id).all()

    if not rows:
        st.warning("No records found.")
        return

    # ---------------- BUILD DATAFRAME ----------------
    data = []

    for r in rows:
        m = session.get(Machine, r.machine_id)
        c = session.get(CountMaster, r.count_id)
        e = session.get(Employee, r.employee_id) if r.employee_id else None
        s = session.get(Shift, r.shift_id)

        data.append({
            "Date": r.date,
            "Mill": mill_map.get(r.mill_id),
            "Department": dept_map.get(r.department_id),
            "Shift": s.shift_name if s else "",
            "Machine": m.machine_name if m else "",

            "Spindles": r.spindles,
            "Count": c.count_name if c else "",
            "Target Kgs": r.target_kgs,
            "Prod Kgs": r.prod_kgs,
            "Actual Production": r.actual_prdn,
            "Waste %": r.waste_percent,
            "Stop Min": r.stop_min,

            "Std GPS": r.std_gps,
            "Actual GPS": r.actual_gps,
            "Diff GPS": r.diff_gps,
            "40s Conv GPS": r.conv_40s_gps,

            "W.O.H": r.woh,
            "MW": r.mw,
            "CLG/LC": r.clg_lc,
            "ER": r.er,
            "LA,PF": r.la_pf,
            "BSS": r.bss,
            "LAP": r.lap,
            "DD": r.dd,
            "Total Loss": r.total_loss,

            "Employee": e.employee_name if e else "",
            "Remarks": r.remarks or ""
        })

    df = pd.DataFrame(data)
    numeric_cols = df.select_dtypes(include=["float", "int"]).columns

    st.dataframe(
        df.style.format({c: "{:.2f}" for c in numeric_cols}),
        use_container_width=True,
        height=650
    )

    # ---------------- SAFE DELETE ----------------
    st.divider()
    st.subheader("🗑️ Delete Production Entry")

    if st.button("Delete Selected Filter Data", type="secondary"):

        if not date or not shift_id:
            st.error("⚠️ Select BOTH Date and Shift to delete.")
        else:
            deleted = session.query(DailyProduction).filter(
                DailyProduction.date == date,
                DailyProduction.shift_id == shift_id
            ).delete(synchronize_session=False)

            session.commit()
            st.success(f"✅ Deleted {deleted} record(s).")
            st.rerun()

    # ---------------- SUMMARY ----------------
    st.divider()
    st.subheader("📌 Production Summary")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("🎯 Total Target Kgs", round(df["Target Kgs"].sum(), 2))
        st.metric("⚙️ Total Prod Kgs", round(df["Prod Kgs"].sum(), 2))

    with c2:
        st.metric("📦 Actual Production", round(df["Actual Production"].sum(), 2))
        st.metric("⏱️ Total Stop Min", round(df["Stop Min"].sum(), 2))

    with c3:
        st.metric("♻️ Avg Waste %", round(df["Waste %"].mean(), 2))

    # ---------------- LOSS SUMMARY ----------------
    st.subheader("📉 Loss Summary")

    loss_cols = ["W.O.H", "MW", "CLG/LC", "ER", "LA,PF", "BSS", "LAP", "DD"]

    loss_df = pd.DataFrame(
        [{"Loss Type": c, "Total": round(df[c].sum(), 2)} for c in loss_cols]
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
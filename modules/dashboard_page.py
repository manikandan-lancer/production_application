import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    Employee, CountMaster, DailyProduction
)


def dashboard_page():
    st.title("📊 Production Dashboard")

    session: Session = next(get_session())

    # -------------------------------
    # FILTER PANEL
    # -------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        date = st.date_input("Date")

    with col2:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox(
            "Mill", [None] + list(mill_map.keys()),
            format_func=lambda x: "All" if x is None else mill_map[x]
        )

    with col3:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_id = st.selectbox(
            "Department", [None] + list(dept_map.keys()),
            format_func=lambda x: "All" if x is None else dept_map[x]
        )

    with col4:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_id = st.selectbox(
            "Shift", [None] + list(shift_map.keys()),
            format_func=lambda x: "All" if x is None else shift_map[x]
        )

    col5, col6 = st.columns(2)

    with col5:
        employees = session.query(Employee).all()
        emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
        emp_id = st.selectbox(
            "Employee", [None] + list(emp_map.keys()),
            format_func=lambda x: "All" if x is None else emp_map[x]
        )

    with col6:
        counts = session.query(CountMaster).all()
        count_map = {c.id: c.count_name for c in counts}
        count_id = st.selectbox(
            "Count", [None] + list(count_map.keys()),
            format_func=lambda x: "All" if x is None else count_map[x]
        )

    st.divider()
    st.subheader("📌 Production Summary (Saved Data)")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🎯 Total Target Kgs", round(df["Target Kgs"].sum(), 2))
        st.metric("⚙️ Total Prod Kgs", round(df["Prod Kgs"].sum(), 2))

    with col2:
        st.metric("⏱️ Total Stop Min", round(df["Stop Min"].sum(), 2))
        st.metric("🧵 Total Pne Bondas", round(df["Pne Bondas"].sum(), 2))

    with col3:
        st.metric("📦 Actual Production", round(df["Actual Production"].sum(), 2))

    st.subheader("📉 Loss Summary")

    loss_cols = ["W.O.H", "MW", "CLG/LC", "ER", "LA,PF", "BSS", "LAP", "DD"]

    loss_totals = {
        col: round(df[col].sum(), 2)
        for col in loss_cols
        if col in df.columns
    }

    loss_df = pd.DataFrame(
        [{"Loss Type": k, "Total": v} for k, v in loss_totals.items()]
    )

    st.dataframe(loss_df, use_container_width=True)

    st.metric(
        "🔻 Total Loss",
        round(df["Total"].sum(), 2)
    )


    # -------------------------------
    # QUERY
    # -------------------------------
    q = session.query(DailyProduction).filter(DailyProduction.date == date)

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

    rows = q.all()

    if not rows:
        st.warning("No records found.")
        return

    # -------------------------------
    # BUILD DATAFRAME (MATCH DAILY ENTRY)
    # -------------------------------
    data = []

    for r in rows:
        machine = session.query(Machine).get(r.machine_id)
        count = session.query(CountMaster).get(r.count_id)
        emp = session.query(Employee).get(r.employee_id) if r.employee_id else None
        shift = session.query(Shift).get(r.shift_id)

        data.append({
            "Date": r.date,
            "Mill": mill_map.get(r.mill_id),
            "Department": dept_map.get(r.department_id),
            "Shift": shift.shift_name if shift else "",
            "Machine": machine.machine_name if machine else "",

            "Spindles": r.spindles,
            "Speed": r.spdl_speed,
            "TPI": r.tpi,
            "Std Hank": r.std_hank,

            "Count": count.count_name if count else "",
            "Conversion Factor": r.conversion_factor,
            "40s Conv Factor": getattr(count, "conv_40s_factor", 0),

            "Worked Spindles": r.worked_spindles,
            "Target Kgs": r.target_kgs,

            "Actual Hank": r.act_hank,
            "Stop Min": r.stop_min,
            "Prod Kgs": r.prod_kgs,
            "Pne Bondas": r.pne_bondas,

            "Actual Production": r.actual_prdn,
            "Waste %": r.waste_percent,

            "Std GPS": r.std_gps,
            "Actual GPS": r.actual_gps,
            "Diff (+/-)": r.diff_gps,
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

            "Employee": emp.employee_name if emp else "",
            "Remarks": r.remarks or "",
        })

    df = pd.DataFrame(data)

    # -------------------------------
    # DISPLAY (2 DECIMAL FORMAT ONLY)
    # -------------------------------
    numeric_cols = df.select_dtypes(include=["float", "int"]).columns

    st.dataframe(
        df.style.format({col: "{:.2f}" for col in numeric_cols}),
        use_container_width=True
    )

    # -------------------------------
    # EXPORT
    # -------------------------------
    st.download_button(
        label="⬇ Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="dashboard_export.csv",
        mime="text/csv"
    )
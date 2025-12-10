import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine, Employee,
    CountMaster, DailyProduction
)

from utils.calc_engine import (
    safe_float,
    calc_worked_spindles,
    calc_actual_production,
    calc_waste_percent,
    calc_target_kgs,
)


# ---------------------------------------------------------
# DASHBOARD PAGE (Excel Style)
# ---------------------------------------------------------
def dashboard_page():
    st.title("📊 PRODUCTION DASHBOARD (Excel Layout)")

    session: Session = next(get_session())

    # ---------------------------------------------------------
    # FILTER PANEL
    # ---------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        date = st.date_input("Date")

    with col2:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox(
            "Mill",
            [None] + list(mill_map.keys()),
            format_func=lambda x: "All" if x is None else mill_map[x],
        )

    with col3:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_id = st.selectbox(
            "Department",
            [None] + list(dept_map.keys()),
            format_func=lambda x: "All" if x is None else dept_map[x],
        )

    with col4:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_id = st.selectbox(
            "Shift",
            [None] + list(shift_map.keys()),
            format_func=lambda x: "All" if x is None else shift_map[x],
        )

    col5, col6, col7 = st.columns(3)

    with col5:
        employees = session.query(Employee).all()
        emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
        emp_id = st.selectbox(
            "Employee",
            [None] + list(emp_map.keys()),
            format_func=lambda x: "All" if x is None else emp_map[x],
        )

    with col6:
        counts = session.query(CountMaster).all()
        count_map = {c.id: c.count_name for c in counts}
        count_id = st.selectbox(
            "Count",
            [None] + list(count_map.keys()),
            format_func=lambda x: "All" if x is None else count_map[x],
        )

    with col7:
        machines = session.query(Machine).order_by(Machine.machine_name).all()
        machine_map = {m.id: m.machine_name for m in machines}
        machine_filter = st.selectbox(
            "Machine",
            [None] + list(machine_map.keys()),
            format_func=lambda x: "All" if x is None else machine_map[x],
        )

    st.divider()

    # ---------------------------------------------------------
    # BUILD QUERY BASED ON FILTERS
    # ---------------------------------------------------------
    query = session.query(DailyProduction).filter(
        DailyProduction.date == date
    )

    if mill_id:
        query = query.filter(DailyProduction.mill_id == mill_id)
    if dept_id:
        query = query.filter(DailyProduction.department_id == dept_id)
    if shift_id:
        query = query.filter(DailyProduction.shift_id == shift_id)
    if emp_id:
        query = query.filter(DailyProduction.employee_id == emp_id)
    if count_id:
        query = query.filter(DailyProduction.count_id == count_id)
    if machine_filter:
        query = query.filter(DailyProduction.machine_id == machine_filter)

    records = query.all()

    if not records:
        st.warning("No records found for selected filters.")
        return

    # ---------------------------------------------------------
    # BUILD TABLE
    # ---------------------------------------------------------
    rows = []
    for r in records:

        machine = session.query(Machine).filter_by(id=r.machine_id).first()
        count = session.query(CountMaster).filter_by(id=r.count_id).first()
        emp = session.query(Employee).filter_by(id=r.employee_id).first() if r.employee_id else None

        # Recompute values (always based on master)
        worked_spindles = calc_worked_spindles(
            safe_float(machine.spindles), safe_float(r.stop_min)
        )

        actual_prdn = calc_actual_production(r.prod_kgs, r.pne_bondas)

        waste_pct = calc_waste_percent(r.pne_bondas, r.prod_kgs)

        target_kgs = calc_target_kgs(
            std_hank=safe_float(r.std_hank),
            worked_spindles=worked_spindles,
            conversion_factor=safe_float(count.conversion_factor) if count else 0,
            run_hours=8,
        )

        rows.append({
            "Date": r.date,
            "Shift": shift_map.get(r.shift_id, ""),
            "Mill": mill_map.get(r.mill_id, ""),
            "Department": dept_map.get(r.department_id, ""),
            "RF.NO": machine.machine_name if machine else "",
            "Count": count.count_name if count else "",
            "Spdl Speed": float(machine.spdl_speed or 0),
            "TPI": float(machine.tpi or 0),
            "STD Hank": float(r.std_hank or 0),
            "ACT Hank": float(r.act_hank or 0),
            "Stop Min": float(r.stop_min or 0),
            "Worked Spindles": worked_spindles,
            "Target Kgs": target_kgs,
            "Prodn Kgs": float(r.prod_kgs or 0),
            "Pne Bondas": float(r.pne_bondas or 0),
            "Waste %": waste_pct,
            "Actual Prdn": actual_prdn,
            "Employee": emp.employee_name if emp else "",
            "Remarks": r.remarks or "",
        })

    df = pd.DataFrame(rows)

    # ---------------------------------------------------------
    # DISPLAY TABLE
    # ---------------------------------------------------------
    st.subheader("📄 Production Records")
    st.dataframe(df, use_container_width=True)

    # ---------------------------------------------------------
    # KPIs
    # ---------------------------------------------------------
    st.divider()
    st.subheader("📌 Summary")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Total Production (Kgs)", round(df["Prodn Kgs"].sum(), 2))
    c2.metric("Total Actual Production", round(df["Actual Prdn"].sum(), 2))
    c3.metric("Avg Waste %", round(df["Waste %"].mean(), 2))
    c4.metric("Avg STD Hank", round(df["STD Hank"].mean(), 4))
    c5.metric("Avg ACT Hank", round(df["ACT Hank"].mean(), 4))

    # ---------------------------------------------------------
    # EXPORT SECTION
    # ---------------------------------------------------------
    st.divider()
    st.subheader("📥 Export Data")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="dashboard_export.csv",
        mime="text/csv",
    )

    excel_path = "dashboard_export.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dashboard")

    with open(excel_path, "rb") as f:
        st.download_button(
            label="Download Excel",
            data=f,
            file_name="dashboard_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
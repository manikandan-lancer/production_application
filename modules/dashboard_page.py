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
    calc_actual_production,
    calc_waste_percent,
    calc_efficiency,
    calc_oee,
    calc_worked_spindles,
    calc_target_kgs
)


# -------------------------------------------------------
# DASHBOARD PAGE
# -------------------------------------------------------
def dashboard_page():
    st.title("📊 Production Dashboard")

    session: Session = next(get_session())

    # -------------------------------------------------------
    # FILTER PANEL
    # -------------------------------------------------------
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

    # -------------------------------------------------------
    # BUILD QUERY
    # -------------------------------------------------------
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

    records = query.all()

    if not records:
        st.warning("No records found for the selected filters.")
        return

    # -------------------------------------------------------
    # BUILD DATAFRAME
    # -------------------------------------------------------
    rows = []

    for r in records:
        machine = r.machine
        count = r.count
        shift = r.shift
        emp = r.employee

        # Always pull latest conversion factor
        conv_factor = safe_float(count.conversion_factor) if count else 0

        # Rebuild calculations to always reflect master changes
        worked_sp = calc_worked_spindles(
            machine.spindles, r.stop_min
        )

        actual_prdn = calc_actual_production(r.prod_kgs, r.pne_bondas)
        waste_pct = calc_waste_percent(r.waste, r.prod_kgs)
        eff = calc_efficiency(r.act_hank, r.std_hank)
        oee = calc_oee(eff, r.run_hours, r.stop_min)
        target_kgs = calc_target_kgs(r.std_hank, worked_sp, r.run_hours, conv_factor)

        rows.append({
            "Date": r.date,
            "Mill": machine.mill.mill_name,
            "Department": machine.department.department_name,
            "Shift": shift.shift_name if shift else "",
            "Machine": machine.machine_name,
            "Count": count.count_name if count else "",
            "Employee": emp.employee_name if emp else "",

            "Spindles": safe_float(machine.spindles),
            "Spdl Speed": safe_float(machine.spdl_speed),
            "TPI": safe_float(machine.tpi),

            "STD Hank": safe_float(r.std_hank),
            "ACT Hank": safe_float(r.act_hank),
            "Stop Min": safe_float(r.stop_min),

            "Worked Spindles": worked_sp,
            "Target Kgs": target_kgs,

            "Prod Kgs": safe_float(r.prod_kgs),
            "Pne Bondas": safe_float(r.pne_bondas),
            "Waste": safe_float(r.waste),
            "Waste %": waste_pct,

            "Actual Prdn": actual_prdn,
            "Efficiency %": eff,
            "OEE %": oee,

            "Run Hours": safe_float(r.run_hours),
            "Remarks": r.remarks or ""
        })

    df = pd.DataFrame(rows)

    # -------------------------------------------------------
    # DISPLAY TABLE
    # -------------------------------------------------------
    st.subheader("📄 Production Records")
    st.dataframe(df, use_container_width=True)

    # -------------------------------------------------------
    # KPI SUMMARY
    # -------------------------------------------------------
    st.subheader("📊 Summary Statistics")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Total Prod (Kgs)", round(df["Prod Kgs"].sum(), 2))
    c2.metric("Actual Production", round(df["Actual Prdn"].sum(), 2))
    c3.metric("Total Waste (Kgs)", round(df["Waste"].sum(), 2))
    c4.metric("Avg Efficiency %", round(df["Efficiency %"].mean(), 2))
    c5.metric("Avg OEE %", round(df["OEE %"].mean(), 2))

    # -------------------------------------------------------
    # EXPORT SECTION
    # -------------------------------------------------------
    st.subheader("📥 Export Data")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="production_dashboard.csv",
        mime="text/csv"
    )

    excel_path = "dashboard_export.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dashboard")

    with open(excel_path, "rb") as f:
        st.download_button(
            label="Download Excel",
            data=f,
            file_name="production_dashboard.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
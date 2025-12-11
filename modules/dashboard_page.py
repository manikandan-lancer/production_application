import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    Employee, CountMaster, DailyProduction
)

from utils.calc_engine import (
    safe_float,
    calc_actual_production,
    calc_efficiency,
    calc_worked_spindles,
    calc_waste_percent,
    calc_oee,
    calc_target_kgs,
)


# ----------------------------------------------------------
# DASHBOARD PAGE
# ----------------------------------------------------------
def dashboard_page():
    st.title("📊 Production Dashboard")

    session: Session = next(get_session())

    # ----------------------------------------------------------
    # FILTER PANEL
    # ----------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        date = st.date_input("Date")

    with c2:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox(
            "Mill", [None] + list(mill_map.keys()),
            format_func=lambda x: "All" if x is None else mill_map[x]
        )

    with c3:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_id = st.selectbox(
            "Department", [None] + list(dept_map.keys()),
            format_func=lambda x: "All" if x is None else dept_map[x]
        )

    with c4:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_id = st.selectbox(
            "Shift", [None] + list(shift_map.keys()),
            format_func=lambda x: "All" if x is None else shift_map[x]
        )

    c5, c6 = st.columns(2)

    with c5:
        employees = session.query(Employee).all()
        emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
        emp_id = st.selectbox(
            "Employee", [None] + list(emp_map.keys()),
            format_func=lambda x: "All" if x is None else emp_map[x]
        )

    with c6:
        counts = session.query(CountMaster).all()
        count_map = {c.id: c.count_name for c in counts}
        count_id = st.selectbox(
            "Count", [None] + list(count_map.keys()),
            format_func=lambda x: "All" if x is None else count_map[x]
        )

    st.divider()

    # ----------------------------------------------------------
    # QUERY BUILDING
    # ----------------------------------------------------------
    query = session.query(DailyProduction).filter(DailyProduction.date == date)

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

    rows = query.all()

    if not rows:
        st.warning("⚠ No production records found for selected filters.")
        return

    # ----------------------------------------------------------
    # BUILD DATAFRAME FOR DISPLAY
    # ----------------------------------------------------------
    data = []

    for r in rows:
        machine = session.query(Machine).get(r.machine_id)
        count = session.query(CountMaster).get(r.count_id)
        shift_obj = session.query(Shift).get(r.shift_id)
        emp = session.query(Employee).get(r.employee_id) if r.employee_id else None

        data.append({
            "Date": r.date,
            "Mill": mill_map.get(r.mill_id),
            "Department": dept_map.get(r.department_id),
            "Shift": shift_obj.shift_name if shift_obj else "",
            "Machine": machine.machine_name if machine else "",
            "Spindles": r.spindles,
            "Speed": r.spdl_speed,
            "TPI": r.tpi,
            "STD Hank": r.std_hank,
            "Count": count.count_name if count else "",
            "Conversion Factor": r.conversion_factor,

            "Worked Spindles": r.worked_spindles,
            "Target Kgs": r.target_kgs,

            "ACT Hank": r.act_hank,
            "Stop Min": r.stop_min,
            "Run Hours": r.run_hours,

            "Prod Kgs": r.prod_kgs,
            "Pneumafil": r.pne_bondas,
            "Actual Production": r.actual_prdn,
            "Waste": r.waste,
            "Waste %": r.waste_percent,
            "Efficiency %": r.efficiency,
            "OEE %": r.oee,

            "Employee": emp.employee_name if emp else "",
            "Remarks": r.remarks or "",
        })

    df = pd.DataFrame(data)

    st.dataframe(df, use_container_width=True)

    # ----------------------------------------------------------
    # SUMMARY KPI
    # ----------------------------------------------------------
    st.subheader("📌 Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Production (Kgs)", round(df["Prod Kgs"].sum(), 2))
    col2.metric("Total Actual Production", round(df["Actual Production"].sum(), 2))
    col3.metric("Average Efficiency (%)", round(df["Efficiency %"].mean(), 2))
    col4.metric("Average OEE (%)", round(df["OEE %"].mean(), 2))

    # ----------------------------------------------------------
    # EXPORT OPTIONS
    # ----------------------------------------------------------
    st.subheader("📥 Export")

    st.download_button(
        label="Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="production_dashboard.csv",
        mime="text/csv",
    )

    excel_path = "dashboard_export.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    with open(excel_path, "rb") as f:
        st.download_button(
            label="Download Excel",
            data=f,
            file_name="production_dashboard.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

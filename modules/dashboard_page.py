import streamlit as st
import pandas as pd

from database.connection import get_session
from database.models import (
    Mill,
    Department,
    Shift,
    Machine,
    Employee,
    CountMaster,
    DailyProduction
)


# -------------------------------------------------------
# DASHBOARD PAGE
# -------------------------------------------------------
def dashboard_page():
    st.title("📊 Production Dashboard")

    session = next(get_session())

    # -------------------------
    # FILTER PANEL
    # -------------------------
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

    colA, colB = st.columns(2)

    with colA:
        employees = session.query(Employee).all()
        emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
        emp_id = st.selectbox(
            "Employee",
            [None] + list(emp_map.keys()),
            format_func=lambda x: "All" if x is None else emp_map[x],
        )

    with colB:
        counts = session.query(CountMaster).all()
        count_map = {c.id: c.count_name for c in counts}
        count_id = st.selectbox(
            "Count",
            [None] + list(count_map.keys()),
            format_func=lambda x: "All" if x is None else count_map[x],
        )

    st.divider()

    # -------------------------
    # BUILD QUERY
    # -------------------------
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
        st.warning("No records found for selected filters.")
        return

    # -------------------------
    # BUILD DATAFRAME
    # -------------------------
    rows = []
    for r in records:

        machine = session.query(Machine).filter_by(id=r.machine_id).first()
        count = session.query(CountMaster).filter_by(id=r.count_id).first()
        employee = session.query(Employee).filter_by(id=r.employee_id).first()
        shift = session.query(Shift).filter_by(id=r.shift_id).first()

        rows.append({
            "Date": r.date,
            "Mill": mill_map.get(r.mill_id, ""),
            "Department": dept_map.get(r.department_id, ""),
            "Shift": shift.shift_name if shift else "",
            "Machine": machine.machine_name if machine else "",
            "Count": count.count_name if count else "",
            "Employee": employee.employee_name if employee else "",
            "Spindle Speed": float(r.spdl_speed or 0),
            "TPI": float(r.tpi or 0),
            "STD Hank": float(r.std_hank or 0),
            "ACT Hank": float(r.act_hank or 0),
            "Worked Spindles": float(r.worked_spindles or 0),
            "Run Hours": float(r.run_hours or 0),
            "Stop Minutes": float(r.stop_min or 0),
            "Conversion Factor": float(r.conversion_factor or 0),
            "Target (kgs)": float(r.target_kgs or 0),
            "Prod (kgs)": float(r.prod_kgs or 0),
            "Pneuma Bondas": float(r.pne_bondas or 0),
            "Actual Production": float(r.actual_prdn or 0),
            "Waste (kgs)": float(r.waste or 0),
            "Waste %": float(r.waste_percent or 0),
            "Efficiency %": float(r.efficiency or 0),
            "OEE %": float(r.oee or 0),
            "Remarks": r.remarks or ""
        })

    df = pd.DataFrame(rows)

    # -------------------------
    # DISPLAY TABLE
    # -------------------------
    st.subheader("📄 Production Records")
    st.dataframe(df, use_container_width=True)

    # -------------------------
    # SUMMARY KPI
    # -------------------------
    st.subheader("📌 Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Prod (kgs)", round(df["Prod (kgs)"].sum(), 2))
    col2.metric("Actual Production", round(df["Actual Production"].sum(), 2))
    col3.metric("Total Waste (kgs)", round(df["Waste (kgs)"].sum(), 2))
    col4.metric("Avg Efficiency %", round(df["Efficiency %"].mean(), 2))
    col5.metric("Avg OEE %", round(df["OEE %"].mean(), 2))

    # -------------------------
    # EXPORT OPTIONS
    # -------------------------
    st.subheader("📥 Export Data")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇ Download CSV",
        data=csv,
        file_name="production_dashboard.csv",
        mime="text/csv"
    )

    excel_file = "dashboard_export.xlsx"
    df.to_excel(excel_file, index=False)

    with open(excel_file, "rb") as f:
        st.download_button(
            label="⬇ Download Excel",
            data=f,
            file_name="production_dashboard.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

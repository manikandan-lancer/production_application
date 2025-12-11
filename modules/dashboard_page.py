import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    Employee, CountMaster, DailyProduction
)


# ----------------------------------------------------------
# DASHBOARD PAGE — FINAL VERSION
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
        mill_val = st.selectbox(
            "Mill", [None] + list(mill_map.keys()),
            format_func=lambda x: "All" if x is None else mill_map[x]
        )

    with c3:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_val = st.selectbox(
            "Department", [None] + list(dept_map.keys()),
            format_func=lambda x: "All" if x is None else dept_map[x]
        )

    with c4:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_val = st.selectbox(
            "Shift", [None] + list(shift_map.keys()),
            format_func=lambda x: "All" if x is None else shift_map[x]
        )

    c5, c6 = st.columns(2)

    with c5:
        employees = session.query(Employee).all()
        emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
        emp_val = st.selectbox(
            "Employee", [None] + list(emp_map.keys()),
            format_func=lambda x: "All" if x is None else emp_map[x]
        )

    with c6:
        counts = session.query(CountMaster).all()
        count_map = {c.id: c.count_name for c in counts}
        count_val = st.selectbox(
            "Count", [None] + list(count_map.keys()),
            format_func=lambda x: "All" if x is None else count_map[x]
        )

    st.divider()

    # ----------------------------------------------------------
    # BUILD QUERY
    # ----------------------------------------------------------
    q = session.query(DailyProduction).filter(DailyProduction.date == date)

    if mill_val:
        q = q.filter(DailyProduction.mill_id == mill_val)
    if dept_val:
        q = q.filter(DailyProduction.department_id == dept_val)
    if shift_val:
        q = q.filter(DailyProduction.shift_id == shift_val)
    if emp_val:
        q = q.filter(DailyProduction.employee_id == emp_val)
    if count_val:
        q = q.filter(DailyProduction.count_id == count_val)

    rows = q.all()

    if not rows:
        st.warning("⚠ No production records found for selected filters.")
        return

    # ----------------------------------------------------------
    # BUILD DATAFRAME FOR DISPLAY
    # ----------------------------------------------------------
    table = []

    for r in rows:
        machine = session.query(Machine).get(r.machine_id)
        count = session.query(CountMaster).get(r.count_id)
        shift = session.query(Shift).get(r.shift_id)
        emp = session.query(Employee).get(r.employee_id) if r.employee_id else None

        table.append({
            "Date": r.date,
            "Mill": mill_map.get(r.mill_id),
            "Department": dept_map.get(r.department_id),
            "Shift": shift.shift_name if shift else "",

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

            "Prod Kgs": r.prod_kgs,
            "Pneumafil Kgs": r.pne_bondas,
            "Actual Production": r.actual_prdn,

            "Waste %": r.waste_percent,

            "Remarks": r.remarks or "",
        })

    df = pd.DataFrame(table)

    # ----------------------------------------------------------
    # DISPLAY TABLE
    # ----------------------------------------------------------
    st.subheader("📄 Daily Production Records")
    st.dataframe(df, use_container_width=True)

    # ----------------------------------------------------------
    # SUMMARY KPI
    # ----------------------------------------------------------
    st.subheader("📌 Summary")

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Production (Kgs)", round(df["Prod Kgs"].sum(), 2))
    c2.metric("Total Actual Production", round(df["Actual Production"].sum(), 2))
    c3.metric("Avg. Waste %", round(df["Waste %"].mean(), 2))

    # ----------------------------------------------------------
    # EXPORT SECTION
    # ----------------------------------------------------------
    st.subheader("📥 Export Data")

    st.download_button(
        label="Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="daily_production_report.csv",
        mime="text/csv",
    )

    excel_path = "daily_production_export.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    with open(excel_path, "rb") as f:
        st.download_button(
            label="Download Excel",
            data=f,
            file_name="daily_production_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    DailyProduction, Machine, Mill, Department,
    Shift, Employee, CountMaster
)

SessionLocal = sessionmaker(bind=engine)


def dashboard_page():
    st.title("📊 Production Dashboard")

    session = SessionLocal()

    # -------------------------------------------------------
    # FILTERS
    # -------------------------------------------------------
    st.subheader("Filters")

    date = st.date_input("Select Date")

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = st.selectbox("Mill", [None] + list(mill_map.keys()),
                           format_func=lambda x: "All" if x is None else mill_map[x])

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = st.selectbox("Department", [None] + list(dept_map.keys()),
                           format_func=lambda x: "All" if x is None else dept_map[x])

    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = st.selectbox("Shift", [None] + list(shift_map.keys()),
                            format_func=lambda x: "All" if x is None else shift_map[x])

    machines = session.query(Machine).all()
    machine_map = {m.id: m.machine_name for m in machines}
    machine_id = st.selectbox("Machine", [None] + list(machine_map.keys()),
                              format_func=lambda x: "All" if x is None else machine_map[x])

    employees = session.query(Employee).all()
    emp_map = {e.id: f"{e.employee_no}-{e.employee_name}" for e in employees}
    emp_id = st.selectbox("Employee", [None] + list(emp_map.keys()),
                          format_func=lambda x: "All" if x is None else emp_map[x])

    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}
    count_id = st.selectbox("Count / Product", [None] + list(count_map.keys()),
                            format_func=lambda x: "All" if x is None else count_map[x])

    # -------------------------------------------------------
    # QUERY BUILD
    # -------------------------------------------------------
    query = session.query(DailyProduction).filter(DailyProduction.date == date)

    if mill_id:
        query = query.filter(DailyProduction.mill_id == mill_id)
    if dept_id:
        query = query.filter(DailyProduction.department_id == dept_id)
    if shift_id:
        query = query.filter(DailyProduction.shift_id == shift_id)
    if machine_id:
        query = query.filter(DailyProduction.machine_id == machine_id)
    if emp_id:
        query = query.filter(DailyProduction.employee_id == emp_id)
    if count_id:
        query = query.filter(DailyProduction.count_id == count_id)

    records = query.all()

    if not records:
        st.warning("No data found for selected filters.")
        return

    # -------------------------------------------------------
    # BUILD TABLE
    # -------------------------------------------------------
    rows = []

    for r in records:
        rows.append({
            "Date": r.date,
            "Mill": mill_map[r.mill_id],
            "Department": dept_map[r.department_id],
            "Shift": shift_map[r.shift_id],
            "Machine": machine_map[r.machine_id],
            "Employee": emp_map[r.employee_id] if r.employee_id else "",
            "Count": count_map[r.count_id] if r.count_id else "",

            "Prod Kgs": r.prod_kgs,
            "Pne Bondas": r.pne_bondas,
            "Actual Prdn": r.actual_prdn,
            "Waste": r.waste,
            "Run Hours": r.run_hours,

            "Efficiency": r.efficiency,
            "OEE": r.oee,
            "Remarks": r.remarks,
        })

    df = pd.DataFrame(rows)

    # -------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------
    st.subheader("Summary")

    st.metric("Total Production (Kgs)", df["Prod Kgs"].sum())
    st.metric("Total Actual Production", df["Actual Prdn"].sum())
    st.metric("Total Waste", df["Waste"].sum())
    st.metric("Avg Efficiency", round(df["Efficiency"].mean(), 2))
    st.metric("Avg OEE", round(df["OEE"].mean(), 2))

    st.subheader("Production Records")
    st.dataframe(df, use_container_width=True)

    # -------------------------------------------------------
    # EXPORT
    # -------------------------------------------------------
    st.subheader("Export")

    # CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "prod_data.csv", mime="text/csv")

    # Excel
    excel_file = "prod_export.xlsx"
    df.to_excel(excel_file, index=False)

    with open(excel_file, "rb") as f:
        st.download_button(
            "Download Excel",
            f,
            "prod_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
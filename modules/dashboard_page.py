import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    DailyProduction,
    Machine,
    Employee,
    CountMaster,
    Shift
)

SessionLocal = sessionmaker(bind=engine)


def dashboard_page():
    st.title("📊 Production Dashboard")

    session = SessionLocal()

    # -------------------------------
    # FILTERS
    # -------------------------------
    st.subheader("Filters")

    date = st.date_input("Select Date")

    # Shift list
    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = st.selectbox("Shift", [None] + list(shift_map.keys()),
                            format_func=lambda x: "All" if x is None else shift_map[x])

    machines = session.query(Machine).all()
    machine_map = {m.id: m.frame_no for m in machines}
    machine_id = st.selectbox("Machine", [None] + list(machine_map.keys()),
                              format_func=lambda x: "All" if x is None else machine_map[x])

    employees = session.query(Employee).all()
    emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
    emp_id = st.selectbox("Employee", [None] + list(emp_map.keys()),
                          format_func=lambda x: "All" if x is None else emp_map[x])

    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}
    count_id = st.selectbox("Count/Product", [None] + list(count_map.keys()),
                            format_func=lambda x: "All" if x is None else count_map[x])

    # -----------------------------------
    # QUERY DATA
    # -----------------------------------
    query = session.query(DailyProduction).filter(DailyProduction.date == date)

    if shift_id:
        query = query.filter(DailyProduction.shift_id == shift_id)
    if machine_id:
        query = query.filter(DailyProduction.machine_id == machine_id)
    if emp_id:
        query = query.filter(DailyProduction.employee_id == emp_id)
    if count_id:
        query = query.filter(DailyProduction.count_id == count_id)

    records = query.all()

    # No Data Case
    if not records:
        st.warning("No production records found for the selected filters.")
        return

    # -----------------------------------
    # FORMAT TABLE
    # -----------------------------------
    rows = []
    for r in records:

        machine = session.query(Machine).filter(Machine.id == r.machine_id).first()
        employee = session.query(Employee).filter(Employee.id == r.employee_id).first()
        count = session.query(CountMaster).filter(CountMaster.id == r.count_id).first()
        shift = session.query(Shift).filter(Shift.id == r.shift_id).first()

        rows.append({
            "Date": r.date,
            "Shift": shift.shift_name if shift else "",
            "Machine": machine.frame_no if machine else "",
            "Employee": employee.employee_name if employee else "",
            "Count/Product": count.count_name if count else "",
            "Target": r.target,
            "Actual": r.actual,
            "Waste": r.waste,
            "Run Hours": r.run_hours,
            "Efficiency": r.efficiency,
            "OEE": r.oee,
            "Remarks": r.remarks
        })

    df = pd.DataFrame(rows)

    # -----------------------------------
    # SUMMARY SECTION
    # -----------------------------------
    st.subheader("Summary")

    total_actual = df["Actual"].sum()
    total_target = df["Target"].sum()
    total_waste = df["Waste"].sum()
    avg_eff = df["Efficiency"].mean()
    avg_oee = df["OEE"].mean()

    st.metric("Total Actual", round(total_actual, 2))
    st.metric("Total Target", round(total_target, 2))
    st.metric("Total Waste", round(total_waste, 2))
    st.metric("Avg Efficiency (%)", round(avg_eff, 2))
    st.metric("Avg OEE (%)", round(avg_oee, 2))

    st.subheader("Production Records")
    st.dataframe(df, use_container_width=True)

    # -----------------------------------
    # EXPORT OPTIONS
    # -----------------------------------
    st.subheader("Export Data")

    # CSV Export
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="production_data.csv",
        mime="text/csv"
    )

    # Excel Export
    excel_buffer = pd.ExcelWriter("prod_export.xlsx", engine="openpyxl")
    df.to_excel(excel_buffer, index=False, sheet_name="ProductionData")
    excel_buffer.save()

    with open("prod_export.xlsx", "rb") as f:
        st.download_button(
            label="Download Excel (.xlsx)",
            data=f,
            file_name="production_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
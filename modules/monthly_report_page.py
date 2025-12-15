import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    Employee, CountMaster, DailyProduction
)


def monthly_report_page():
    st.title("📅 Monthly Production Report")

    session: Session = next(get_session())

    # -----------------------------------
    # FILTER PANEL
    # -----------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        year = st.selectbox("Year", list(range(2022, date.today().year + 1)))
        month = st.selectbox("Month", list(range(1, 13)))

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

    col4, col5, col6 = st.columns(3)

    with col4:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_id = st.selectbox(
            "Shift", [None] + list(shift_map.keys()),
            format_func=lambda x: "All" if x is None else shift_map[x]
        )

    with col5:
        counts = session.query(CountMaster).all()
        count_map = {c.id: c.count_name for c in counts}
        count_id = st.selectbox(
            "Count", [None] + list(count_map.keys()),
            format_func=lambda x: "All" if x is None else count_map[x]
        )

    with col6:
        employees = session.query(Employee).all()
        emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
        emp_id = st.selectbox(
            "Employee", [None] + list(emp_map.keys()),
            format_func=lambda x: "All" if x is None else emp_map[x]
        )

    st.divider()

    # -----------------------------------
    # DATE RANGE
    # -----------------------------------
    start_date = date(year, month, 1)
    end_date = date(year + (month // 12), (month % 12) + 1, 1)

    # -----------------------------------
    # QUERY (AGGREGATED)
    # -----------------------------------
    q = session.query(
        Machine.machine_name.label("Machine"),
        CountMaster.count_name.label("Count"),

        func.sum(DailyProduction.target_kgs).label("Target Kgs"),
        func.sum(DailyProduction.prod_kgs).label("Prod Kgs"),
        func.sum(DailyProduction.actual_prdn).label("Actual Production"),
        func.sum(DailyProduction.stop_min).label("Stop Min"),
        func.sum(DailyProduction.pne_bondas).label("Pne Bondas"),

        func.avg(DailyProduction.waste_percent).label("Avg Waste %"),
        func.avg(DailyProduction.actual_gps).label("Avg Actual GPS"),

        func.sum(DailyProduction.total_loss).label("Total Loss"),
    ) \
    .join(Machine, Machine.id == DailyProduction.machine_id) \
    .join(CountMaster, CountMaster.id == DailyProduction.count_id)

    q = q.filter(DailyProduction.date >= start_date)
    q = q.filter(DailyProduction.date < end_date)

    if mill_id:
        q = q.filter(DailyProduction.mill_id == mill_id)
    if dept_id:
        q = q.filter(DailyProduction.department_id == dept_id)
    if shift_id:
        q = q.filter(DailyProduction.shift_id == shift_id)
    if count_id:
        q = q.filter(DailyProduction.count_id == count_id)
    if emp_id:
        q = q.filter(DailyProduction.employee_id == emp_id)

    q = q.group_by(Machine.machine_name, CountMaster.count_name)

    rows = q.all()

    if not rows:
        st.warning("No records found for selected month.")
        return

    # -----------------------------------
    # DATAFRAME (RAW)
    # -----------------------------------
    df = pd.DataFrame(rows)

    # -----------------------------------
    # DISPLAY (UI ONLY → 4 DECIMALS)
    # -----------------------------------
    display_df = df.copy()

    numeric_cols = display_df.select_dtypes(include=["float", "int"]).columns
    display_df[numeric_cols] = display_df[numeric_cols].round(4)

    st.dataframe(display_df, use_container_width=True)

    # -----------------------------------
    # MONTHLY SUMMARY
    # -----------------------------------
    st.divider()
    st.subheader("📊 Monthly Summary")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("🎯 Total Target Kgs", round(df["Target Kgs"].sum(), 2))
        st.metric("⚙️ Total Prod Kgs", round(df["Prod Kgs"].sum(), 2))

    with c2:
        st.metric("📦 Total Actual Production", round(df["Actual Production"].sum(), 2))
        st.metric("⏱️ Total Stop Min", round(df["Stop Min"].sum(), 2))

    with c3:
        st.metric("🧵 Total Pne Bondas", round(df["Pne Bondas"].sum(), 2))
        st.metric("🔻 Total Loss", round(df["Total Loss"].sum(), 2))

    # -----------------------------------
    # EXPORT (NO ROUNDING)
    # -----------------------------------
    export_df = df.copy()

    st.download_button(
        "⬇ Download Monthly CSV",
        export_df.to_csv(index=False).encode("utf-8"),
        f"monthly_report_{year}_{month:02d}.csv",
        "text/csv"
    )
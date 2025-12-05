import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    DailyProduction,
    Machine,
    Employee,
    CountMaster,
    Mill,
    Department
)
from modules.formulas import (
    calc_efficiency,
    calc_availability,
    calc_performance,
    calc_quality,
    calc_oee
)

SessionLocal = sessionmaker(bind=engine)


def daily_entry_page():
    st.title("📝 Daily Production Entry")

    session = SessionLocal()

    # -------------------------------
    # FILTERS
    # -------------------------------
    date = st.date_input("Select Date")

    shifts = ["Shift 1", "Shift 2", "Shift 3"]
    shift_name = st.selectbox("Shift", shifts)

    # Convert shift name into index 1–3
    shift_id = shifts.index(shift_name) + 1

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    departments = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in departments}
    dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    # Machines for selected mill + dept
    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).all()

    # Count (Product) Master
    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}

    # Employees (mill + department filtered)
    employees = session.query(Employee).filter(
        Employee.mill_id == mill_id,
        Employee.department_id == dept_id
    ).all()
    emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}

    # -------------------------------
    # LOAD EXISTING RECORDS
    # -------------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.shift_id == shift_id,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id
    ).all()

    if saved:
        st.success("Loaded saved entries for this date.")

        rows = []
        for r in saved:
            machine = session.query(Machine).filter(Machine.id == r.machine_id).first()
            emp = session.query(Employee).filter(Employee.id == r.employee_id).first()
            cnt = session.query(CountMaster).filter(CountMaster.id == r.count_id).first()

            rows.append({
                "machine_id": r.machine_id,
                "frame_no": machine.frame_no if machine else "",
                "employee_id": r.employee_id,
                "employee": f"{emp.employee_no} - {emp.employee_name}" if emp else "",
                "count_id": r.count_id,
                "count_name": cnt.count_name if cnt else "",
                "target": r.target,
                "actual": r.actual,
                "waste": r.waste,
                "run_hours": r.run_hours,
                "efficiency": r.efficiency,
                "oee": r.oee,
                "remarks": r.remarks
            })
        df = pd.DataFrame(rows)

    else:
        st.info("No saved data found — generating blank entry list.")

        df = pd.DataFrame([
            {
                "machine_id": m.id,
                "frame_no": m.frame_no,
                "employee_id": None,
                "employee": "",
                "count_id": None,
                "count_name": "",
                "target": 0,
                "actual": 0,
                "waste": 0,
                "run_hours": 0,
                "efficiency": 0,
                "oee": 0,
                "remarks": ""
            }
            for m in machines
        ])

    # -------------------------------
    # Editable Table
    # -------------------------------
    edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # -------------------------------
    # CALCULATIONS
    # -------------------------------
    for idx, r in edited.iterrows():
        availability = calc_availability(r["run_hours"], 8)
        performance = calc_performance(r["actual"], 1, 1, 1)  # placeholder, since machine formulas may differ
        quality = calc_quality(r["actual"], r["waste"])
        efficiency = calc_efficiency(r["actual"], r["target"])
        oee = calc_oee(availability, performance, quality)

        edited.at[idx, "efficiency"] = efficiency
        edited.at[idx, "oee"] = oee

    # -------------------------------
    # SAVE DATA
    # -------------------------------
    if st.button("💾 Save Production Data"):
        # Delete previous records for same date + shift + mill + dept
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.shift_id == shift_id,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id
        ).delete()
        session.commit()

        # Insert new data
        for _, r in edited.iterrows():
            dp = DailyProduction(
                date=date,
                shift_id=shift_id,
                mill_id=mill_id,
                department_id=dept_id,
                machine_id=r["machine_id"],
                employee_id=r["employee_id"],
                count_id=r["count_id"],
                target=r["target"],
                actual=r["actual"],
                waste=r["waste"],
                run_hours=r["run_hours"],
                efficiency=r["efficiency"],
                oee=r["oee"],
                remarks=r["remarks"]
            )
            session.add(dp)

        session.commit()
        st.success("Production data saved successfully!")


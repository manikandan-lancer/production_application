import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    Machine, Shift, DailyProduction, Employee, Mill, Department
)
from modules.formulas import (
    calc_efficiency,
    calc_oee,
    calc_availability,
    calc_performance,
    calc_quality
)

SessionLocal = sessionmaker(bind=engine)


def daily_entry_page():
    st.title("Daily Production Entry")

    session = SessionLocal()

    # ------------------ FILTERS ------------------
    date = st.date_input("Select Date")

    mills = session.query(Mill).order_by(Mill.id).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    depts = session.query(Department).order_by(Department.id).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    shifts = session.query(Shift).order_by(Shift.id).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = st.selectbox("Shift", shift_map.keys(), format_func=lambda x: shift_map[x])

    # ------------------ LOAD EXISTING ------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id
    ).all()

    if saved:
        st.success("Loaded saved records.")

        rows = []
        for s in saved:
            machine = session.query(Machine).filter(Machine.id == s.machine_id).first()
            emp = session.query(Employee).filter(Employee.id == s.employee_id).first()

            rows.append({
                "machine_id": s.machine_id,
                "frame_number": machine.frame_number if machine else "",
                "employee_id": emp.employee_no if emp else "",
                "employee_name": emp.employee_name if emp else "",
                "actual": s.actual,
                "waste": s.waste,
                "run_hr": s.run_hr,
                "prod": s.prod,
                "ts": s.ts,
                "count": s.count,
                "remarks": s.remarks,
                "efficiency": s.efficiency,
                "oee": s.oee,
                "target": s.target,
                "speed": machine.speed if machine else 0,
                "tpi": machine.tpi if machine else 0,
                "std_hank": machine.std_hank if machine else 0
            })

        df = pd.DataFrame(rows)

    else:
        st.warning("No saved data found. Generating new rows...")

        machines = session.query(Machine).filter(
            Machine.mill_id == mill_id,
            Machine.department_id == dept_id
        ).order_by(Machine.id).all()

        if not machines:
            st.error("No machines found for this Mill + Department.")
            return

        df = pd.DataFrame([
            {
                "machine_id": m.id,
                "frame_number": m.frame_number,
                "employee_id": "",
                "employee_name": "",
                "actual": 0,
                "waste": 0,
                "run_hr": 0,
                "prod": 0,
                "ts": "",
                "count": "",
                "remarks": "",
                "efficiency": 0,
                "oee": 0,
                "target": m.target,
                "speed": m.speed,
                "tpi": m.tpi,
                "std_hank": m.std_hank
            }
            for m in machines
        ])

    # ------------------ AUTO-FILL EMPLOYEE NAME ------------------
    for idx, row in df.iterrows():
        emp_no = str(row["employee_id"]).strip()
        if emp_no:
            emp = session.query(Employee).filter(Employee.employee_no == emp_no).first()
            if emp:
                df.at[idx, "employee_name"] = emp.employee_name

    # ------------------ SHOW EDITOR ------------------
    edited_df = st.data_editor(df, use_container_width=True)

    # ------------------ AUTO CALCULATIONS ------------------
    for idx, r in edited_df.iterrows():
        availability = calc_availability(r["run_hr"])
        performance = calc_performance(r["actual"], r["speed"], r["tpi"], r["std_hank"])
        quality = calc_quality(r["actual"], r["waste"])
        efficiency = calc_efficiency(r["actual"], r["target"])
        oee = calc_oee(availability, performance, quality)

        edited_df.at[idx, "efficiency"] = efficiency
        edited_df.at[idx, "oee"] = oee

    # ------------------ SAVE TO DATABASE ------------------
    if st.button("Save Data"):

        # Delete old records for this date+mill+dept+shift
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        # Insert updated records
        for _, r in edited_df.iterrows():

            emp = session.query(Employee).filter(
                Employee.employee_no == str(r["employee_id"])
            ).first()
            emp_id = emp.id if emp else None

            new_entry = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                employee_id=emp_id,
                actual=r["actual"],
                waste=r["waste"],
                run_hr=r["run_hr"],
                prod=r["prod"],
                ts=r["ts"],
                count=r["count"],
                remarks=r["remarks"],
                target=r["target"],
                efficiency=r["efficiency"],
                oee=r["oee"]
            )

            session.add(new_entry)

        session.commit()
        st.success("Data Saved Successfully!")

        # Clear session df to avoid reuse
        if "production_df" in st.session_state:
            del st.session_state["production_df"]
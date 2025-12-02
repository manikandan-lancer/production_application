import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    Machine, Shift, DailyProduction, Employee,
    Mill, Department
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

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    shifts = session.query(Shift).order_by(Shift.id).all()
    shift_map = {s.id: s.shift_name for s in shifts}

    shift_id = st.selectbox(
        "Shift",
        options=list(shift_map.keys()),
        format_func=lambda x: shift_map[x]
    )


    # ------------------ LOAD EXISTING ------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == int(mill_id),
        DailyProduction.department_id == int(dept_id),
        DailyProduction.shift_id == int(shift_id)
    ).all()

    st.write("DEBUG Saved Count:", len(saved))


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
                "ts": s.ts or "",
                "count": s.count or "",
                "efficiency": s.efficiency or 0,
                "oee": s.oee or 0,
                "remarks": s.remarks,
                "target": s.target,
            })

        df = pd.DataFrame(rows)

    else:
        st.warning("Generating new data...")

        machines = session.query(Machine).filter(
            Machine.mill_id == mill_id,
            Machine.department_id == dept_id
        ).all()

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
                "efficiency": 0,
                "oee": 0,
                "remarks": "",
                "target": m.target,
                "speed": m.speed,
                "tpi": m.tpi,
                "std_hank": m.std_hank
            }
            for m in machines
        ])

    # ------------------ AUTO-FILL EMPLOYEE NAME ------------------
    for idx, row in df.iterrows():
        emp_no = str(row.get("employee_id", "")).strip()
        if emp_no:
            emp = session.query(Employee).filter(Employee.employee_no == emp_no).first()
            if emp:
                df.at[idx, "employee_name"] = emp.employee_name

    edited_df = st.data_editor(df, use_container_width=True)

    # -------------------- AUTO CALCULATIONS --------------------
    for idx, r in edited_df.iterrows():
        availability = calc_availability(r.get("run_hr", 0))
        performance = calc_performance(
            r.get("actual", 0),
            r.get("speed", 0),
            r.get("tpi", 0),
            r.get("std_hank", 0)
        )
        quality = calc_quality(r.get("actual", 0), r.get("waste", 0))
        efficiency = calc_efficiency(r.get("actual", 0), r.get("target", 0))
        oee = calc_oee(availability, performance, quality)

        edited_df.at[idx, "efficiency"] = efficiency
        edited_df.at[idx, "oee"] = oee

    # -------------------- SAVE --------------------
    if st.button("Save Data"):

        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        for _, r in edited_df.iterrows():

            emp = session.query(Employee).filter(
                Employee.employee_no == str(r.get("employee_id", ""))
            ).first()
            emp_id = emp.id if emp else None

            entry = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                employee_id=emp_id,
                actual=r.get("actual", 0),
                waste=r.get("waste", 0),
                run_hr=r.get("run_hr", 0),
                prod=r.get("prod", 0),
                ts=r.get("ts", ""),       # <---- FIXED
                count=r.get("count", ""), # <---- FIXED
                remarks=r.get("remarks", ""),
                target=r.get("target", 0)
            )
            session.add(entry)

        session.commit()
        st.success("Saved successfully!")
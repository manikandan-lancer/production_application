import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    Machine, Shift, DailyProduction, Employee,
    Mill, Department
)

SessionLocal = sessionmaker(bind=engine)


def daily_entry_page():
    st.title("Daily Production Entry")

    session = SessionLocal()

    # ------------------ FILTERS ------------------
    date = st.date_input("Select Date")

    # Mill
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = st.selectbox(
        "Select Mill",
        mill_map.keys(),
        format_func=lambda x: mill_map[x]
    )

    # Department
    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = st.selectbox(
        "Select Department",
        dept_map.keys(),
        format_func=lambda x: dept_map[x]
    )

    # Shift
    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = st.selectbox(
        "Select Shift",
        shift_map.keys(),
        format_func=lambda x: shift_map[x]
    )

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
            rows.append({
                "id": s.id,
                "machine_id": s.machine_id,
                "frame_number": machine.frame_number if machine else "",
                "employee_id": s.employee_id,
                "employee_name": s.employee.employee_name if s.employee else "",
                "actual": s.actual,
                "waste": s.waste,
                "run_hr": s.run_hr,
                "prod": s.prod,
                "ts": s.ts,
                "count": s.count,
                "remarks": s.remarks,
                "target": s.target
            })

        df = pd.DataFrame(rows)

    else:
        st.warning("No records found. Generating new rows.")

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
                "remarks": "",
                "target": m.target
            }
            for m in machines
        ])

    # ------------------ AUTO-FILL EMPLOYEE NAME ------------------
    def fill_employee_name(df):
        for index, row in df.iterrows():
            if str(row["employee_id"]).strip() != "":
                emp = session.query(Employee).filter(
                    Employee.employee_no == str(row["employee_id"])
                ).first()
                if emp:
                    df.at[index, "employee_name"] = emp.employee_name
        return df

    df = fill_employee_name(df)

    # ------------------ SHOW EDITOR ------------------
    edited_df = st.data_editor(df, use_container_width=True)

    # ------------------ SAVE TO DB ------------------
    if st.button("Save Data"):
        # Delete old rows for the filter
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        # Insert updated rows
        for _, r in edited_df.iterrows():
            new = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                employee_id=r["employee_id"],
                actual=r["actual"],
                waste=r["waste"],
                run_hr=r["run_hr"],
                prod=r["prod"],
                ts=r["ts"],
                count=r["count"],
                remarks=r["remarks"],
                target=r["target"]
            )
            session.add(new)

        session.commit()
        st.success("Data Saved Successfully!")

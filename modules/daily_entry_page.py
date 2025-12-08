import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    DailyProduction, Machine, CountMaster,
    Employee, Mill, Department, Shift
)

SessionLocal = sessionmaker(bind=engine)

def daily_entry_page():
    st.title("📝 Daily Production Entry")

    session = SessionLocal()

    # -------------------------
    # BASIC FILTERS
    # -------------------------
    date = st.date_input("Select Date")

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = st.selectbox("Shift", shift_map.keys(), format_func=lambda x: shift_map[x])

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    # -------------------------
    # LOAD MACHINES FOR MILL
    # -------------------------
    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).all()

    if not machines:
        st.warning("No machines found for this mill & department.")
        return

    # Build template rows
    rows = []
    for m in machines:
        rows.append({
            "machine_id": m.id,
            "machine": m.machine_name,
            "count": "",
            "prod_kgs": 0,
            "pne_bondas": 0,
            "actual_prdn": 0,
            "waste": 0,
            "run_hours": 0,
            "employee": "",
            "remarks": ""
        })

    df = pd.DataFrame(rows)

    st.subheader("Enter Production Data")

    edited = st.data_editor(df, use_container_width=True)

    # -------------------------
    # SAVE
    # -------------------------
    if st.button("💾 Save Entries"):

        # Delete existing records
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        for _, r in edited.iterrows():

            emp = session.query(Employee).filter(
                Employee.employee_no == str(r["employee"])
            ).first()

            count = session.query(CountMaster).filter(
                CountMaster.count_name == str(r["count"]),
                CountMaster.mill_id == mill_id
            ).first()

            session.add(
                DailyProduction(
                    date=date,
                    mill_id=mill_id,
                    department_id=dept_id,
                    shift_id=shift_id,
                    machine_id=r["machine_id"],
                    employee_id=emp.id if emp else None,
                    count_id=count.id if count else None,
                    prod_kgs=r["prod_kgs"],
                    pne_bondas=r["pne_bondas"],
                    actual_prdn=r["prod_kgs"] - r["pne_bondas"],
                    waste=r["waste"],
                    run_hours=r["run_hours"],
                    remarks=r["remarks"]
                )
            )

        session.commit()
        st.success("Saved Successfully!")
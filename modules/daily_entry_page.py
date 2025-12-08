import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    Machine, Employee, CountMaster, Shift,
    DailyProduction, Department, Mill
)

SessionLocal = sessionmaker(bind=engine)


# -----------------------------------------------------
# DAILY ENTRY PAGE
# -----------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session = SessionLocal()

    # -----------------------------------------------------
    # 1. FILTERS
    # -----------------------------------------------------
    st.subheader("Filters")

    date = st.date_input("Select Date")

    # MILL
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    # DEPARTMENT
    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    # SHIFT
    shifts = session.query(Shift).order_by(Shift.id).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = st.selectbox("Shift", shift_map.keys(), format_func=lambda x: shift_map[x])

    # -----------------------------------------------------
    # 2. LOAD MACHINES FOR SELECTED MILL + DEPT
    # -----------------------------------------------------
    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).all()

    if not machines:
        st.warning("⚠ No machines found for this Mill + Department.")
        return

    # -----------------------------------------------------
    # 3. CHECK IF RECORDS ALREADY EXIST
    # -----------------------------------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id
    ).all()

    if saved:
        st.success("Previous records loaded.")

        rows = []
        for s in saved:
            machine = s.machine
            emp = s.employee
            count = s.count

            rows.append({
                "machine_id": s.machine_id,
                "machine_name": machine.machine_name,
                "employee_no": emp.employee_no if emp else "",
                "employee_name": emp.employee_name if emp else "",
                "count_name": count.count_name if count else "",

                "worked_spindles": s.worked_spindles,
                "spdl_speed": s.spdl_speed,
                "tpi": s.tpi,
                "std_hank": s.std_hank,
                "act_hank": s.act_hank,
                "stop_min": s.stop_min,
                "target_kgs": s.target_kgs,

                "prod_kgs": s.prod_kgs,
                "pne_bondas": s.pne_bondas,
                "actual_prdn": s.actual_prdn,
                "waste": s.waste,
                "run_hours": s.run_hours,
                "remarks": s.remarks
            })

        df = pd.DataFrame(rows)

    else:
        st.info("No saved records — generating new entry form.")

        df = pd.DataFrame([
            {
                "machine_id": m.id,
                "machine_name": m.machine_name,
                "employee_no": "",
                "employee_name": "",
                "count_name": m.allocated_count.count_name if m.allocated_count else "",

                "worked_spindles": m.spindles or 0,
                "spdl_speed": 0,
                "tpi": 0,
                "std_hank": 0,
                "act_hank": 0,
                "stop_min": 0,
                "target_kgs": 0,

                "prod_kgs": 0,
                "pne_bondas": 0,
                "actual_prdn": 0,
                "waste": 0,
                "run_hours": 0,
                "remarks": ""
            }
            for m in machines
        ])

    # -----------------------------------------------------
    # 4. AUTO-FILL EMPLOYEE NAME
    # -----------------------------------------------------
    def autofill_employee(row):
        emp_no = str(row["employee_no"]).strip()
        if emp_no:
            emp = session.query(Employee).filter(Employee.employee_no == emp_no).first()
            return emp.employee_name if emp else ""
        return ""

    for idx, row in df.iterrows():
        df.at[idx, "employee_name"] = autofill_employee(row)

    # -----------------------------------------------------
    # 5. DATA EDITOR UI
    # -----------------------------------------------------
    edited_df = st.data_editor(df, use_container_width=True, key="daily_editor")

    # -----------------------------------------------------
    # 6. CALCULATE FIELDS IN UI
    # -----------------------------------------------------
    for idx, row in edited_df.iterrows():
        prod = row["prod_kgs"] or 0
        pne = row["pne_bondas"] or 0

        edited_df.at[idx, "actual_prdn"] = prod - pne

    st.dataframe(edited_df, use_container_width=True)

    # -----------------------------------------------------
    # 7. SAVE TO DATABASE
    # -----------------------------------------------------
    if st.button("💾 Save Daily Production"):
        # Remove old entries
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        # Insert new rows
        for _, r in edited_df.iterrows():

            emp = None
            if r["employee_no"]:
                emp = session.query(Employee).filter(
                    Employee.employee_no == str(r["employee_no"])
                ).first()

            count = session.query(CountMaster).filter(
                CountMaster.count_name == str(r["count_name"])
            ).first()

            entry = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                employee_id=emp.id if emp else None,
                count_id=count.id if count else None,

                worked_spindles=r["worked_spindles"],
                spdl_speed=r["spdl_speed"],
                tpi=r["tpi"],
                std_hank=r["std_hank"],
                act_hank=r["act_hank"],
                stop_min=r["stop_min"],
                target_kgs=r["target_kgs"],

                prod_kgs=r["prod_kgs"],
                pne_bondas=r["pne_bondas"],
                actual_prdn=r["actual_prdn"],
                waste=r["waste"],
                run_hours=r["run_hours"],
                remarks=r["remarks"]
            )

            session.add(entry)

        session.commit()
        st.success("✅ Daily Production Saved Successfully!")
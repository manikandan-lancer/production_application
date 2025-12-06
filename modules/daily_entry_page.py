import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    Machine, Shift, DailyProduction,
    Employee, CountMaster
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
    st.title("📘 Daily Production Entry")

    session = SessionLocal()

    # ---------------------------------------------------
    # DATE SELECTION
    # ---------------------------------------------------
    date = st.date_input("Select Date")

    # ---------------------------------------------------
    # SHIFT SELECTION
    # ---------------------------------------------------
    shifts = session.query(Shift).order_by(Shift.id).all()

    if not shifts:
        st.error("⚠ No shifts found. Please configure Shift Master.")
        return

    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = st.selectbox("Shift", list(shift_map.keys()), format_func=lambda x: shift_map[x])

    # ---------------------------------------------------
    # LOAD MACHINES
    # ---------------------------------------------------
    machines = session.query(Machine).all()
    if not machines:
        st.warning("⚠ No machines found. Add machines first.")
        return

    # ---------------------------------------------------
    # LOAD SAVED PRODUCTION IF EXISTS
    # ---------------------------------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.shift_id == shift_id
    ).all()

    # ---------------------------------------------------
    # LOAD MASTERS
    # ---------------------------------------------------
    employees = session.query(Employee).all()
    employee_map = {e.employee_no: e for e in employees}

    counts = session.query(CountMaster).all()
    count_map = {c.count_name: c for c in counts}

    # ---------------------------------------------------
    # PREPARE DATAFRAME
    # ---------------------------------------------------
    if saved:
        st.success("Loaded existing saved production data.")

        rows = []
        for s in saved:
            emp = session.query(Employee).filter(Employee.id == s.employee_id).first()
            count = session.query(CountMaster).filter(CountMaster.id == s.count_id).first()
            machine = session.query(Machine).filter(Machine.id == s.machine_id).first()

            rows.append({
                "machine_id": s.machine_id,
                "frame_no": machine.frame_no if machine else "",
                "employee_no": emp.employee_no if emp else "",
                "employee_name": emp.employee_name if emp else "",
                "count_name": count.count_name if count else "",
                "target": s.target,
                "actual": s.actual,
                "waste": s.waste,
                "run_hours": s.run_hours,
                "efficiency": s.efficiency,
                "oee": s.oee,
                "remarks": s.remarks
            })

        df = pd.DataFrame(rows)

    else:
        st.warning("No saved data — generating new entry template.")

        df = pd.DataFrame([
            {
                "machine_id": m.id,
                "frame_no": m.frame_no,
                "employee_no": "",
                "employee_name": "",
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

    # ---------------------------------------------------
    # AUTOFILL EMPLOYEE NAME FROM NUMBER
    # ---------------------------------------------------
    for idx, row in df.iterrows():
        emp_no = str(row["employee_no"]).strip()
        if emp_no and emp_no in employee_map:
            df.at[idx, "employee_name"] = employee_map[emp_no].employee_name

    # ---------------------------------------------------
    # EDITOR UI
    # ---------------------------------------------------
    st.subheader("Enter Production Data")

    edited_df = st.data_editor(df, use_container_width=True)

    # ---------------------------------------------------
    # CALCULATE FORMULAS
    # ---------------------------------------------------
    for idx, r in edited_df.iterrows():

        availability = calc_availability(r["run_hours"])
        performance = calc_performance(r["actual"])
        quality = calc_quality(r["actual"], r["waste"])
        efficiency = calc_efficiency(r["actual"], r["target"])
        oee = calc_oee(availability, performance, quality)

        edited_df.at[idx, "efficiency"] = efficiency
        edited_df.at[idx, "oee"] = oee

    # ---------------------------------------------------
    # SAVE DATA
    # ---------------------------------------------------
    if st.button("💾 Save Data"):
        # delete existing for date+shift
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        for _, r in edited_df.iterrows():

            # employee lookup
            emp_obj = employee_map.get(str(r["employee_no"]).strip())

            # count lookup
            count_obj = count_map.get(str(r["count_name"]).strip())

            new_entry = DailyProduction(
                date=date,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                employee_id=emp_obj.id if emp_obj else None,
                count_id=count_obj.id if count_obj else None,
                target=r["target"],
                actual=r["actual"],
                waste=r["waste"],
                run_hours=r["run_hours"],
                efficiency=r["efficiency"],
                oee=r["oee"],
                remarks=r["remarks"]
            )

            session.add(new_entry)

        session.commit()
        st.success("✅ Production Data Saved Successfully!")
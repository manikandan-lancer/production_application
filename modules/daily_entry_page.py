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

    # ---------------------------
    # SELECT DATE
    # ---------------------------
    date = st.date_input("Select Date")

    # ---------------------------
    # SELECT SHIFT
    # ---------------------------
    shifts = session.query(Shift).order_by(Shift.id).all()
    if not shifts:
        st.error("⚠ No shifts found. Please add 3 shifts in Shift Master.")
        return

    shift_map = {s.id: s.shift_name for s in shifts}

    shift_id = st.selectbox(
        "Shift",
        list(shift_map.keys()),
        format_func=lambda x: shift_map[x]
    )

    # ---------------------------
    # LOAD MACHINES
    # ---------------------------
    machines = session.query(Machine).all()
    if not machines:
        st.warning("⚠ No machines available. Please add machines first.")
        return

    # ---------------------------
    # CHECK EXISTING RECORDS
    # ---------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.shift_id == shift_id
    ).all()

    if saved:
        st.success("Loaded saved records.")

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
        st.warning("No saved data — generating blank template.")

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

    # ---------------------------
    # AUTO-FILL EMPLOYEE NAME
    # ---------------------------
    for idx, row in df.iterrows():
        if row["employee_no"]:
            emp = session.query(Employee).filter(
                Employee.employee_no == str(row["employee_no"])
            ).first()
            if emp:
                df.at[idx, "employee_name"] = emp.employee_name

    # ---------------------------
    # DATA EDITOR
    # ---------------------------
    edited_df = st.data_editor(df, use_container_width=True)

    # ---------------------------
    # FORMULA CALCULATIONS
    # ---------------------------
    for idx, r in edited_df.iterrows():

        availability = calc_availability(r["run_hours"])
        performance = calc_performance(r["actual"])   # FIXED
        quality = calc_quality(r["actual"], r["waste"])
        efficiency = calc_efficiency(r["actual"], r["target"])
        oee = calc_oee(availability, performance, quality)

        edited_df.at[idx, "efficiency"] = efficiency
        edited_df.at[idx, "oee"] = oee

    # ---------------------------
    # SAVE DATA
    # ---------------------------
    if st.button("💾 Save Data"):

        # Delete old entries
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        # Insert fresh entries
        for _, r in edited_df.iterrows():

            # Employee
            emp_obj = None
            if r["employee_no"]:
                emp_obj = session.query(Employee).filter(
                    Employee.employee_no == str(r["employee_no"])
                ).first()

            # Count
            count_obj = None
            if r["count_name"]:
                count_obj = session.query(CountMaster).filter(
                    CountMaster.count_name == str(r["count_name"])
                ).first()

            entry = DailyProduction(
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

            session.add(entry)

        session.commit()
        st.success("✅ Daily Production Saved Successfully!")
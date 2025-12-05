import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    Mill, Machine, Employee, CountMaster,
    Shift, DailyProduction
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
    st.title("📝 Daily Production Entry")

    session = SessionLocal()

    # -----------------------------
    # FILTERS
    # -----------------------------
    date = st.date_input("Select Production Date")

    # Mill selection
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = st.selectbox("Select Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    # Shift selection
    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = st.selectbox("Select Shift", shift_map.keys(), format_func=lambda x: shift_map[x])

    # -----------------------------
    # LOAD EXISTING SAVED DATA
    # -----------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.shift_id == shift_id
    ).all()

    if saved:
        st.success("Loaded existing saved records!")

        rows = []
        for s in saved:
            rows.append({
                "machine_id": s.machine_id,
                "frame_no": s.machine.frame_no if s.machine else "",
                "employee_id": s.employee_id,
                "employee_no": s.employee.employee_no if s.employee else "",
                "employee_name": s.employee.employee_name if s.employee else "",
                "count_id": s.count_id,
                "count_name": s.count.count_name if s.count else "",
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
        st.warning("No saved records found — generating fresh entry table.")

        machines = session.query(Machine).filter(Machine.mill_id == mill_id).all()
        counts = session.query(CountMaster).all()

        df = pd.DataFrame([
            {
                "machine_id": m.id,
                "frame_no": m.frame_no,
                "employee_id": "",
                "employee_no": "",
                "employee_name": "",
                "count_id": "",
                "count_name": "",
                "target": m.speed or 0,
                "actual": 0,
                "waste": 0,
                "run_hours": 0,
                "efficiency": 0,
                "oee": 0,
                "remarks": ""
            }
            for m in machines
        ])

    # -----------------------------
    # EMPLOYEE AUTO FILL
    # -----------------------------
    def fill_employee_name(df):
        for i, row in df.iterrows():
            emp_no = str(row["employee_no"]).strip()
            if emp_no:
                emp = session.query(Employee).filter(Employee.employee_no == emp_no).first()
                if emp:
                    df.at[i, "employee_id"] = emp.id
                    df.at[i, "employee_name"] = emp.employee_name
        return df

    df = fill_employee_name(df)

    # -----------------------------
    # DATA EDITOR UI
    # -----------------------------
    edited_df = st.data_editor(df, use_container_width=True)

    # -----------------------------
    # AUTO CALCULATIONS
    # -----------------------------
    for i, r in edited_df.iterrows():
        availability = calc_availability(r["run_hours"])
        performance = calc_performance(
            r["actual"],
            speed=None,     # Not used currently
            tpi=None,
            std_hank=None
        )
        quality = calc_quality(r["actual"], r["waste"])
        efficiency = calc_efficiency(r["actual"], r["target"])
        oee = calc_oee(availability, performance, quality)

        edited_df.at[i, "efficiency"] = efficiency
        edited_df.at[i, "oee"] = oee

    # -----------------------------
    # SAVE BUTTON
    # -----------------------------
    if st.button("💾 Save Production Data"):
        # Remove old records for same date + shift
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        # Insert new rows
        for _, r in edited_df.iterrows():

            emp = None
            if str(r["employee_no"]).strip():
                emp = session.query(Employee).filter(Employee.employee_no == str(r["employee_no"])).first()

            count_obj = None
            if r["count_name"]:
                count_obj = session.query(CountMaster).filter(CountMaster.count_name == r["count_name"]).first()

            entry = DailyProduction(
                date=date,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                employee_id=emp.id if emp else None,
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
        st.success("✅ Production Data Saved Successfully!")
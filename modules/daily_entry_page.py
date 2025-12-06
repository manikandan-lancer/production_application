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
        st.error("⚠ No shifts found in database. Please add shifts in Shift Master.")
        return

    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = st.selectbox("Shift", shift_map.keys(), format_func=lambda x: shift_map[x])

    # ---------------------------
    # LOAD MACHINES
    # ---------------------------
    machines = session.query(Machine).order_by(Machine.id).all()

    if not machines:
        st.warning("⚠ No machines found. Please add machines first.")
        return

    # ---------------------------
    # LOOKUP MAPS
    # ---------------------------
    employees = session.query(Employee).all()
    employee_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}

    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}

    # ---------------------------
    # CHECK IF SAVED RECORDS EXIST
    # ---------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.shift_id == shift_id
    ).all()

    if saved:
        st.success("Loaded saved records.")

        rows = []
        for s in saved:
            rows.append({
                "machine_id": s.machine_id,
                "frame_no": session.query(Machine).get(s.machine_id).frame_no,
                "employee": s.employee_id,
                "count": s.count_id,
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
        st.warning("No saved data found — generating new entry template.")

        df = pd.DataFrame([
            {
                "machine_id": m.id,
                "frame_no": m.frame_no,
                "employee": None,
                "count": None,
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
    # EDITOR UI
    # ---------------------------
    st.write("### Enter Production Data")

    # Replace employee and count columns with dropdown widgets
    edited = []

    for idx, row in df.iterrows():
        cols = st.columns([1, 2, 2, 2, 1, 1, 1, 1, 1, 2])

        with cols[0]:
            st.write(row["frame_no"])

        with cols[1]:
            emp = st.selectbox(
                "Employee",
                [None] + list(employee_map.keys()),
                index=([None] + list(employee_map.keys())).index(row["employee"]) 
                    if row["employee"] in employee_map else 0,
                key=f"emp_{idx}",
                format_func=lambda x: "Select" if x is None else employee_map[x]
            )

        with cols[2]:
            cnt = st.selectbox(
                "Count/Product",
                [None] + list(count_map.keys()),
                index=([None] + list(count_map.keys())).index(row["count"]) 
                    if row["count"] in count_map else 0,
                key=f"count_{idx}",
                format_func=lambda x: "Select" if x is None else count_map[x]
            )

        with cols[3]:
            target = st.number_input("Target", min_value=0.0, key=f"target_{idx}", value=row["target"])

        with cols[4]:
            actual = st.number_input("Actual", min_value=0.0, key=f"actual_{idx}", value=row["actual"])

        with cols[5]:
            waste = st.number_input("Waste", min_value=0.0, key=f"waste_{idx}", value=row["waste"])

        with cols[6]:
            run_hours = st.number_input("Run Hrs", min_value=0.0, key=f"run_{idx}", value=row["run_hours"])

        # ---- Formulas ----
        availability = calc_availability(run_hours)
        performance = calc_performance(actual)
        quality = calc_quality(actual, waste)
        eff = calc_efficiency(actual, target)
        oee = calc_oee(availability, performance, quality)

        with cols[7]:
            st.write(round(eff, 2))

        with cols[8]:
            st.write(round(oee, 2))

        with cols[9]:
            remarks = st.text_input("Remarks", key=f"rmk_{idx}", value=row["remarks"])

        edited.append({
            "machine_id": row["machine_id"],
            "employee": emp,
            "count": cnt,
            "target": target,
            "actual": actual,
            "waste": waste,
            "run_hours": run_hours,
            "efficiency": eff,
            "oee": oee,
            "remarks": remarks
        })

    # ---------------------------
    # SAVE DATA
    # ---------------------------
    if st.button("💾 Save Data"):
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        for row in edited:
            entry = DailyProduction(
                date=date,
                shift_id=shift_id,
                machine_id=row["machine_id"],
                employee_id=row["employee"],
                count_id=row["count"],
                target=row["target"],
                actual=row["actual"],
                waste=row["waste"],
                run_hours=row["run_hours"],
                efficiency=row["efficiency"],
                oee=row["oee"],
                remarks=row["remarks"]
            )
            session.add(entry)

        session.commit()
        st.success("✅ Daily Production Saved Successfully!")
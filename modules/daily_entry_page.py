import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    Machine, Employee, CountMaster, DailyProduction, Shift
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

    # ----------------------------------------------------------------------
    # FILTERS
    # ----------------------------------------------------------------------
    st.subheader("Select Production Details")

    date = st.date_input("Date")

    # Shift selection
    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = st.selectbox("Shift", shift_map.keys(), format_func=lambda x: shift_map[x])

    # Machine selection (MULTIPLE)
    machines = session.query(Machine).all()
    machine_map = {m.id: f"{m.frame_no} ({m.mill})" for m in machines}
    selected_machines = st.multiselect(
        "Select Machines", machine_map.keys(), format_func=lambda x: machine_map[x]
    )

    # Count selection
    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}
    count_id = st.selectbox("Count (Product)", count_map.keys(), format_func=lambda x: count_map[x])

    # Employee selection
    employees = session.query(Employee).all()
    emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
    emp_id = st.selectbox("Employee", emp_map.keys(), format_func=lambda x: emp_map[x])

    st.divider()

    # ----------------------------------------------------------------------
    # GENERATE TABLE FOR ENTRY
    # ----------------------------------------------------------------------
    rows = []
    for m_id in selected_machines:
        m = session.query(Machine).filter(Machine.id == m_id).first()

        rows.append({
            "machine_id": m.id,
            "machine": m.frame_no,
            "count_id": count_id,
            "employee_id": emp_id,
            "target": 0,
            "actual": 0,
            "waste": 0,
            "run_hours": 0,
            "efficiency": 0,
            "oee": 0,
            "remarks": ""
        })

    df = pd.DataFrame(rows)

    if df.empty:
        st.info("Select machines to begin entering production.")
        return

    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    # ----------------------------------------------------------------------
    # AUTO CALCULATIONS
    # ----------------------------------------------------------------------
    for idx, row in edited_df.iterrows():
        availability = calc_availability(row["run_hours"])
        performance = calc_performance(row["actual"], 1, 1, 1)  # simplified, optional future update
        quality = calc_quality(row["actual"], row["waste"])
        efficiency = calc_efficiency(row["actual"], row["target"])
        oee = calc_oee(availability, performance, quality)

        edited_df.at[idx, "efficiency"] = efficiency
        edited_df.at[idx, "oee"] = oee

    # ----------------------------------------------------------------------
    # SAVE
    # ----------------------------------------------------------------------
    if st.button("💾 Save Production"):
        for _, r in edited_df.iterrows():
            new_entry = DailyProduction(
                date=date,
                shift_id=shift_id,
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
            session.add(new_entry)

        session.commit()
        st.success("Production Saved Successfully!")
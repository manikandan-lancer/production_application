import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine, Employee,
    CountMaster, DailyProduction
)

from utils.calc_engine import (
    safe_float,
    calc_worked_spindles,
    calc_target_kgs,
    calc_actual_production,
    calc_waste_percent
)


# ----------------------------------------------------------
# DAILY ENTRY PAGE — FINAL VERSION (NO run_hours / efficiency / oee / waste)
# ----------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session: Session = next(get_session())

    # ----------------------------------------------------------
    # FILTER PANEL
    # ----------------------------------------------------------
    colA, colB, colC, colD = st.columns(4)

    with colA:
        date = st.date_input("Date")

    with colB:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    with colC:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    with colD:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_id = st.selectbox("Shift", shift_map.keys(), format_func=lambda x: shift_map[x])

    st.divider()

    # ----------------------------------------------------------
    # GET MACHINES FOR THIS MILL + DEPARTMENT
    # ----------------------------------------------------------
    machines = (
        session.query(Machine)
        .filter(Machine.mill_id == mill_id, Machine.department_id == dept_id)
        .order_by(Machine.machine_name)
        .all()
    )

    if not machines:
        st.warning("❗ No machines found for this Mill & Department.")
        return

    # ----------------------------------------------------------
    # CHECK IF RECORDS ALREADY EXIST
    # ----------------------------------------------------------
    saved_rows = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id,
    ).all()

    # ----------------------------------------------------------
    # CASE 1 — LOAD EXISTING ENTRIES
    # ----------------------------------------------------------
    if saved_rows:
        st.success("Loaded previously saved entries.")

        df = []
        for r in saved_rows:
            c = session.query(CountMaster).get(r.count_id)

            df.append({
                "machine_id": r.machine_id,
                "machine_name": r.machine.machine_name,

                "spindles": r.spindles,
                "speed": r.spdl_speed,
                "tpi": r.tpi,
                "std_hank": r.std_hank,

                "count_id": r.count_id,
                "count_name": c.count_name if c else "",
                "conversion_factor": float(r.conversion_factor or 0),

                "act_hank": float(r.act_hank or 0),
                "stop_min": float(r.stop_min or 0),

                "worked_spindles": float(r.worked_spindles or 0),
                "target_kgs": float(r.target_kgs or 0),

                "prod_kgs": float(r.prod_kgs or 0),
                "pne_bondas": float(r.pne_bondas or 0),

                "actual_prdn": float(r.actual_prdn or 0),
                "waste_percent": float(r.waste_percent or 0),

                "remarks": r.remarks or "",
            })

        df = pd.DataFrame(df)

    # ----------------------------------------------------------
    # CASE 2 — NEW DAY → AUTOLOAD FROM MASTERS
    # ----------------------------------------------------------
    else:
        st.info("Generating new sheets using Machine Master + Count Master.")

        df = []
        for m in machines:
            count = session.query(CountMaster).get(m.allocated_count_id)

            std_hank = safe_float(m.std_hank)
            conv_factor = safe_float(count.conversion_factor) if count else 0

            df.append({
                "machine_id": m.id,
                "machine_name": m.machine_name,

                "spindles": m.spindles,
                "speed": float(m.spdl_speed or 0),
                "tpi": float(m.tpi or 0),
                "std_hank": std_hank,

                "count_id": m.allocated_count_id,
                "count_name": count.count_name if count else "",
                "conversion_factor": conv_factor,

                # user inputs
                "act_hank": 0.0,
                "stop_min": 0.0,
                "prod_kgs": 0.0,
                "pne_bondas": 0.0,

                # calculations to be filled later
                "worked_spindles": 0.0,
                "target_kgs": 0.0,
                "actual_prdn": 0.0,
                "waste_percent": 0.0,

                "remarks": "",
            })

        df = pd.DataFrame(df)

    # ----------------------------------------------------------
    # SET READONLY FIELDS
    # ----------------------------------------------------------
    readonly = [
        "machine_name", "spindles", "speed", "tpi", "std_hank",
        "count_name", "conversion_factor",
        "worked_spindles", "target_kgs",
        "actual_prdn", "waste_percent"
    ]

    edited = st.data_editor(
        df,
        disabled=readonly,
        use_container_width=True
    )

    # ----------------------------------------------------------
    # LIVE CALCULATIONS
    # ----------------------------------------------------------
    for idx, row in edited.iterrows():

        worked_sp = calc_worked_spindles(row["spindles"], row["stop_min"])
        edited.at[idx, "worked_spindles"] = worked_sp

        target = calc_target_kgs(
            row["conversion_factor"],
            row["spindles"],
            row["std_hank"]
        )
        edited.at[idx, "target_kgs"] = target

        actual = calc_actual_production(row["prod_kgs"], row["pne_bondas"])
        edited.at[idx, "actual_prdn"] = actual

        waste_pct = calc_waste_percent(row["pne_bondas"], row["prod_kgs"])
        edited.at[idx, "waste_percent"] = waste_pct

    # ----------------------------------------------------------
    # SAVE BUTTON
    # ----------------------------------------------------------
    if st.button("💾 Save Daily Production"):

        # remove previous entries
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id,
        ).delete()
        session.commit()

        # insert updated rows
        for _, row in edited.iterrows():
            entry = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,

                machine_id=row["machine_id"],
                count_id=row["count_id"],

                spindles=row["spindles"],
                spdl_speed=row["speed"],
                tpi=row["tpi"],
                std_hank=row["std_hank"],
                conversion_factor=row["conversion_factor"],

                act_hank=row["act_hank"],
                stop_min=row["stop_min"],

                worked_spindles=row["worked_spindles"],
                target_kgs=row["target_kgs"],

                prod_kgs=row["prod_kgs"],
                pne_bondas=row["pne_bondas"],
                actual_prdn=row["actual_prdn"],
                waste_percent=row["waste_percent"],

                remarks=row["remarks"]
            )
            session.add(entry)

        session.commit()
        st.success("✅ Daily Production Saved Successfully!")
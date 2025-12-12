import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    CountMaster, DailyProduction
)

from utils.calc_engine import (
    safe_float,
    calc_worked_spindles,
    calc_target_kgs,
    calc_actual_prdn,
    calc_waste_percent
)


# ----------------------------------------------------------
# DAILY ENTRY PAGE — FINAL VERSION
# ----------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session: Session = next(get_session())

    # ------------------------------------------------------
    # FILTER PANEL
    # ------------------------------------------------------
    colA, colB, colC, colD = st.columns(4)

    with colA:
        date = st.date_input("Date")

    with colB:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox("Mill", mill_map.keys(),
                               format_func=lambda x: mill_map[x])

    with colC:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_id = st.selectbox("Department", dept_map.keys(),
                               format_func=lambda x: dept_map[x])

    with colD:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_id = st.selectbox("Shift", shift_map.keys(),
                                format_func=lambda x: shift_map[x])

    st.divider()

    # ------------------------------------------------------
    # LOAD MACHINES
    # ------------------------------------------------------
    machines = (
        session.query(Machine)
        .filter(Machine.mill_id == mill_id,
                Machine.department_id == dept_id)
        .order_by(Machine.machine_name)
        .all()
    )

    if not machines:
        st.warning("No machines found for this Mill & Department.")
        return

    # ------------------------------------------------------
    # CHECK EXISTING SAVED DATA
    # ------------------------------------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id,
    ).all()

    # ------------------------------------------------------
    # CASE 1 — Load existing saved production entries
    # ------------------------------------------------------
    if saved:
        st.success("Loaded previously saved entries.")

        df = []
        for r in saved:
            cnt = session.query(CountMaster).get(r.count_id)

            df.append({
                "machine_id": r.machine_id,
                "machine_name": r.machine.machine_name,

                "spindles": r.spindles,
                "speed": r.spdl_speed,
                "tpi": r.tpi,
                "std_hank": r.std_hank,

                "count_id": r.count_id,
                "count_name": cnt.count_name if cnt else "",
                "conversion_factor": float(r.conversion_factor or 0),

                "act_hank": float(r.act_hank or 0),
                "stop_min": float(r.stop_min or 0),
                "prod_kgs": float(r.prod_kgs or 0),
                "pne_bondas": float(r.pne_bondas or 0),

                "worked_spindles": float(r.worked_spindles or 0),
                "target_kgs": float(r.target_kgs or 0),
                "actual_prdn": float(r.actual_prdn or 0),
                "waste_percent": float(r.waste_percent or 0),

                "remarks": r.remarks or "",
            })

        df = pd.DataFrame(df)

    # ------------------------------------------------------
    # CASE 2 — New entry sheet
    # ------------------------------------------------------
    else:
        df = []
        for m in machines:
            cnt = session.query(CountMaster).get(m.allocated_count_id)
            conv = safe_float(cnt.conversion_factor) if cnt else 0

            df.append({
                "machine_id": m.id,
                "machine_name": m.machine_name,

                "spindles": m.spindles,
                "speed": float(m.spdl_speed or 0),
                "tpi": float(m.tpi or 0),
                "std_hank": float(m.std_hank or 0),

                "count_id": m.allocated_count_id,
                "count_name": cnt.count_name if cnt else "",
                "conversion_factor": conv,

                # user input
                "act_hank": 0.0,
                "stop_min": 0.0,
                "prod_kgs": 0.0,
                "pne_bondas": 0.0,

                # calculated
                "worked_spindles": 0.0,
                "target_kgs": 0.0,
                "actual_prdn": 0.0,
                "waste_percent": 0.0,

                "remarks": "",
            })

        df = pd.DataFrame(df)

    # ------------------------------------------------------
    # READONLY FIELDS
    # ------------------------------------------------------
    readonly = [
        "machine_name", "spindles", "speed", "tpi", "std_hank",
        "count_name", "conversion_factor",
        "worked_spindles", "target_kgs",
        "actual_prdn", "waste_percent",
    ]

    edited = st.data_editor(
        df,
        disabled=readonly,
        use_container_width=True
    )

    # ------------------------------------------------------
    # LIVE CALCULATIONS
    # ------------------------------------------------------
    for i, row in edited.iterrows():

        worked = calc_worked_spindles(row["spindles"], row["stop_min"])
        edited.at[i, "worked_spindles"] = worked

        target = calc_target_kgs(
            row["conversion_factor"],
            row["spindles"],
            row["std_hank"],
        )
        edited.at[i, "target_kgs"] = target

        actual = calc_actual_prdn(row["prod_kgs"], row["pne_bondas"])
        edited.at[i, "actual_prdn"] = actual

        waste_pct = calc_waste_percent(row["pne_bondas"], row["prod_kgs"])
        edited.at[i, "waste_percent"] = waste_pct

    # ------------------------------------------------------
    # SAVE
    # ------------------------------------------------------
    if st.button("💾 Save Daily Production"):

        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id,
        ).delete()
        session.commit()

        for _, row in edited.iterrows():
            dp = DailyProduction(
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
            session.add(dp)

        session.commit()
        st.success("✅ Daily Production Saved!")
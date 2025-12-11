import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    Employee, CountMaster, DailyProduction
)

from utils.calc_engine import (
    safe_float,
    calc_worked_spindles,
    calc_actual_production,
    calc_efficiency,
    calc_waste_percent,
    calc_oee,
    calc_target_kgs,
)


# ----------------------------------------------------------
# DAILY ENTRY PAGE (Dynamic Master-Driven)
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
    # CHECK IF ALREADY SAVED DATA EXISTS
    # ----------------------------------------------------------
    saved_rows = (
        session.query(DailyProduction)
        .filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id,
        )
        .all()
    )

    # ----------------------------------------------------------
    # IF EXISTING RECORDS FOUND → LOAD THEM
    # ----------------------------------------------------------
    if saved_rows:
        st.success("Loaded previously saved data.")

        df = []
        for r in saved_rows:

            c = session.query(CountMaster).filter_by(id=r.count_id).first()

            df.append({
                "machine_id": r.machine_id,
                "machine_name": r.machine.machine_name,

                "spindles": r.spindles,
                "speed": r.spdl_speed,
                "tpi": r.tpi,
                "std_hank": r.std_hank,

                "count_id": r.count_id,
                "count_name": c.count_name if c else "",
                "conversion_factor": float(c.conversion_factor or 0),

                "act_hank": float(r.act_hank or 0),
                "stop_min": float(r.stop_min or 0),
                "run_hours": float(r.run_hours or 0),

                "worked_spindles": float(r.worked_spindles or 0),
                "target_kgs": float(r.target_kgs or 0),

                "prod_kgs": float(r.prod_kgs or 0),
                "pne_bondas": float(r.pne_bondas or 0),
                "actual_prdn": float(r.actual_prdn or 0),
                "waste": float(r.waste or 0),
                "waste_percent": float(r.waste_percent or 0),

                "efficiency": float(r.efficiency or 0),
                "oee": float(r.oee or 0),
                "remarks": r.remarks or "",
            })

        df = pd.DataFrame(df)

    # ----------------------------------------------------------
    # NO SAVED DATA → GENERATE NEW ROWS USING MASTERS
    # ----------------------------------------------------------
    else:
        st.info("Generating new entry sheet...")

        df = []
        for m in machines:

            count = session.query(CountMaster).filter_by(id=m.allocated_count_id).first()

            std_eff = safe_float(count.std_hank_efficiency) if count else 0
            std_hank = (safe_float(m.spdl_speed) / safe_float(m.tpi)) * 0.01587394 * (std_eff / 100)

            df.append({
                "machine_id": m.id,
                "machine_name": m.machine_name,

                "spindles": m.spindles,
                "speed": float(m.spdl_speed or 0),
                "tpi": float(m.tpi or 0),
                "std_hank": round(std_hank, 4),

                "count_id": m.allocated_count_id,
                "count_name": count.count_name if count else "",
                "conversion_factor": float(count.conversion_factor or 0) if count else 0,

                "act_hank": 0.0,
                "stop_min": 0.0,
                "run_hours": 8.0,

                "worked_spindles": 0.0,
                "target_kgs": 0.0,

                "prod_kgs": 0.0,
                "pne_bondas": 0.0,
                "actual_prdn": 0.0,
                "waste": 0.0,
                "waste_percent": 0.0,

                "efficiency": 0.0,
                "oee": 0.0,
                "remarks": "",
            })

        df = pd.DataFrame(df)

    # ----------------------------------------------------------
    # READ-ONLY FIELDS
    # ----------------------------------------------------------
    readonly = [
        "machine_name", "spindles", "speed", "tpi", "std_hank",
        "count_name", "conversion_factor",
        "worked_spindles", "target_kgs",
        "actual_prdn", "waste_percent", "efficiency", "oee"
    ]

    edited = st.data_editor(df, disabled=readonly, use_container_width=True)

    # ----------------------------------------------------------
    # LIVE CALCULATIONS
    # ----------------------------------------------------------
    for idx, row in edited.iterrows():

        worked_sp = calc_worked_spindles(row["spindles"], row["stop_min"])
        edited.at[idx, "worked_spindles"] = worked_sp

        actual_prod = calc_actual_production(row["prod_kgs"], row["pne_bondas"])
        edited.at[idx, "actual_prdn"] = actual_prod

        efficiency = calc_efficiency(row["act_hank"], row["std_hank"])
        edited.at[idx, "efficiency"] = efficiency

        waste_pct = calc_waste_percent(row["waste"], row["prod_kgs"])
        edited.at[idx, "waste_percent"] = waste_pct

        oee = calc_oee(efficiency, row["run_hours"], row["stop_min"])
        edited.at[idx, "oee"] = oee

        target = calc_target_kgs(
            row["std_hank"],
            worked_sp,
            row["run_hours"],
            row["conversion_factor"],
        )
        edited.at[idx, "target_kgs"] = target

    # ----------------------------------------------------------
    # SAVE TO DB
    # ----------------------------------------------------------
    if st.button("💾 Save Daily Production"):

        # Remove previous entries for this date+mill+dept+shift
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id,
        ).delete()

        session.commit()

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
                run_hours=row["run_hours"],

                worked_spindles=row["worked_spindles"],
                target_kgs=row["target_kgs"],

                prod_kgs=row["prod_kgs"],
                pne_bondas=row["pne_bondas"],
                actual_prdn=row["actual_prdn"],
                waste=row["waste"],
                waste_percent=row["waste_percent"],

                efficiency=row["efficiency"],
                oee=row["oee"],
                remarks=row["remarks"],
            )

            session.add(entry)

        session.commit()
        st.success("✔ Daily Production Saved Successfully!")

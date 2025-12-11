import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift,
    Machine, CountMaster, DailyProduction
)

from utils.calc_engine import (
    safe_float,
    calc_worked_spindles,
    calc_target_kgs,
    calc_actual_production,
    calc_waste_percent,
)


# ----------------------------------------------------------
# DAILY ENTRY PAGE (FINAL UPDATED)
# ----------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session: Session = next(get_session())

    # ----------------------------------------------------------
    # FILTER PANEL
    # ----------------------------------------------------------
    c1, c2, c3 = st.columns(3)

    with c1:
        date = st.date_input("Date")

    with c2:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    with c3:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    c4 = st.columns(1)[0]
    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = c4.selectbox("Shift", shift_map.keys(), format_func=lambda x: shift_map[x])

    st.divider()

    # ----------------------------------------------------------
    # LOAD MACHINES FOR THIS MILL + DEPARTMENT
    # ----------------------------------------------------------
    machines = (
        session.query(Machine)
        .filter(Machine.mill_id == mill_id, Machine.department_id == dept_id)
        .order_by(Machine.machine_name)
        .all()
    )

    if not machines:
        st.warning("❗ No machines found for the selected Mill & Department.")
        return

    # ----------------------------------------------------------
    # CHECK IF DAILY ENTRY ALREADY EXISTS
    # ----------------------------------------------------------
    saved = (
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
    # IF SAVED DATA EXISTS → LOAD IT
    # ----------------------------------------------------------
    if saved:
        st.success("✔ Loaded previously saved Daily Entry data.")

        rows = []
        for r in saved:
            count_obj = session.query(CountMaster).get(r.count_id)

            rows.append({
                "machine_id": r.machine_id,
                "machine": r.machine.machine_name,

                "spindles": r.spindles,
                "speed": float(r.spdl_speed or 0),
                "tpi": float(r.tpi or 0),
                "std_hank": float(r.std_hank or 0),

                "conversion_factor": float(count_obj.conversion_factor) if count_obj else 0,

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

        df = pd.DataFrame(rows)

    # ----------------------------------------------------------
    # OTHERWISE CREATE NEW SHEET FROM MASTER VALUES
    # ----------------------------------------------------------
    else:
        st.info("Creating fresh Daily Entry sheet from Master values...")

        rows = []
        for m in machines:

            count = session.query(CountMaster).get(m.allocated_count_id)

            std_eff = safe_float(count.std_hank_eff) if count else 0

            # Generate STD HANK fresh
            std_hank = (
                safe_float(m.spdl_speed) / safe_float(m.tpi)
            ) * 0.01587394 * (std_eff / 100)

            rows.append({
                "machine_id": m.id,
                "machine": m.machine_name,

                "spindles": m.spindles,
                "speed": float(m.spdl_speed),
                "tpi": float(m.tpi),
                "std_hank": round(std_hank, 4),

                "conversion_factor": float(count.conversion_factor) if count else 0,

                "act_hank": 0.0,
                "stop_min": 0.0,

                "worked_spindles": 0.0,
                "target_kgs": 0.0,

                "prod_kgs": 0.0,
                "pne_bondas": 0.0,
                "actual_prdn": 0.0,

                "waste_percent": 0.0,

                "remarks": "",
            })

        df = pd.DataFrame(rows)

    # ----------------------------------------------------------
    # SHOW EDITABLE TABLE (Excel-like sheet)
    # ----------------------------------------------------------
    readonly = [
        "machine", "spindles", "speed", "tpi", "std_hank",
        "conversion_factor", "worked_spindles",
        "target_kgs", "actual_prdn", "waste_percent"
    ]

    edited = st.data_editor(df, disabled=readonly, use_container_width=True)

    # ----------------------------------------------------------
    # LIVE CALCULATIONS
    # ----------------------------------------------------------
    for idx, row in edited.iterrows():

        # Worked Spindles
        ws = calc_worked_spindles(row["spindles"], row["stop_min"])
        edited.at[idx, "worked_spindles"] = ws

        # Target Kgs
        tg = calc_target_kgs(row["std_hank"], ws, row["conversion_factor"])
        edited.at[idx, "target_kgs"] = tg

        # Actual Production
        ap = calc_actual_production(row["prod_kgs"], row["pne_bondas"])
        edited.at[idx, "actual_prdn"] = ap

        # Waste %
        wp = calc_waste_percent(row["pne_bondas"], row["prod_kgs"])
        edited.at[idx, "waste_percent"] = wp

    # ----------------------------------------------------------
    # SAVE BUTTON
    # ----------------------------------------------------------
    if st.button("💾 Save Daily Production"):

        # Delete existing entry for same filter → clean update
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id,
        ).delete()

        session.commit()

        # Insert new data
        for _, row in edited.iterrows():

            new = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,

                machine_id=row["machine_id"],
                count_id=session.query(Machine).get(row["machine_id"]).allocated_count_id,

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

                remarks=row["remarks"],
            )

            session.add(new)

        session.commit()
        st.success("✔ Daily Production Saved Successfully!")
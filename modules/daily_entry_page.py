import streamlit as st
import pandas as pd

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine, Employee,
    CountMaster, DailyProduction
)

# CALC ENGINE
from utils.calc_engine import (
    calc_actual_prdn,
    calc_worked_spindles,
    calc_target_kgs,
    calc_efficiency,
    calc_oee,
    calc_waste_percent
)


# -------------------------------------------------------
# DAILY ENTRY PAGE
# -------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session = next(get_session())

    # -------------------------------------------------------
    # TOP FILTER PANEL
    # -------------------------------------------------------
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

    # -------------------------------------------------------
    # MACHINE LIST
    # -------------------------------------------------------
    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name.asc()).all()

    if not machines:
        st.error("No machines found for selected mill + department")
        return

    # -------------------------------------------------------
    # LOAD SAVED RECORDS
    # -------------------------------------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id
    ).all()

    # -------------------------------------------------------
    # IF SAVED → LOAD INTO DF
    # -------------------------------------------------------
    if saved:
        st.success("Loaded saved records.")

        rows = []
        for r in saved:
            count_obj = r.count
            mach_obj = r.machine

            rows.append({
                "machine_id": r.machine_id,
                "machine_name": mach_obj.machine_name,

                "count_id": r.count_id,
                "count_name": count_obj.count_name if count_obj else "",
                "conversion_factor": float(count_obj.conversion_factor or 0),

                "spdl_speed": float(r.spdl_speed or 0),
                "tpi": float(r.tpi or 0),
                "std_hank": float(r.std_hank or 0),

                "stop_min": float(r.stop_min or 0),
                "run_hours": float(r.run_hours or 0),
                "worked_spindles": float(r.worked_spindles or 0),

                "act_hank": float(r.act_hank or 0),
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

        df = pd.DataFrame(rows)

    # -------------------------------------------------------
    # NO SAVED RECORD → BUILD NEW BLANK ROWS
    # -------------------------------------------------------
    else:
        st.info("Creating fresh entry sheet...")

        rows = []
        for m in machines:
            count_obj = session.query(CountMaster).filter(
                CountMaster.id == m.allocated_count_id
            ).first()

            rows.append({
                "machine_id": m.id,
                "machine_name": m.machine_name,

                "count_id": count_obj.id if count_obj else None,
                "count_name": count_obj.count_name if count_obj else "",
                "conversion_factor": float(count_obj.conversion_factor or 0) if count_obj else 0,

                "spdl_speed": float(m.spdl_speed or 0),
                "tpi": float(m.tpi or 0),
                "std_hank": float(m.std_hank or 0),

                "stop_min": 0.0,
                "run_hours": 0.0,
                "worked_spindles": 0.0,

                "act_hank": 0.0,
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

        df = pd.DataFrame(rows)

    # -------------------------------------------------------
    # READ-ONLY COLUMNS
    # -------------------------------------------------------
    readonly_cols = [
        "machine_id", "machine_name",
        "count_id", "count_name",
        "spdl_speed", "tpi", "std_hank",
        "conversion_factor",
        "worked_spindles", "target_kgs",
        "actual_prdn", "waste_percent",
        "efficiency", "oee"
    ]

    edited_df = st.data_editor(
        df,
        disabled=readonly_cols,
        use_container_width=True
    )

    # -------------------------------------------------------
    # LIVE CALCULATIONS
    # -------------------------------------------------------
    for idx, r in edited_df.iterrows():
        # WORKED SPINDLES
        m = session.query(Machine).filter_by(id=r["machine_id"]).first()
        spindles = m.spindles if m else 0

        worked = calc_worked_spindles(spindles, r["stop_min"])
        edited_df.at[idx, "worked_spindles"] = worked

        # ACTUAL PRODUCTION
        actual = calc_actual_prdn(r["prod_kgs"], r["pne_bondas"])
        edited_df.at[idx, "actual_prdn"] = actual

        # WASTE %
        waste_pct = calc_waste_percent(r["waste"], r["prod_kgs"])
        edited_df.at[idx, "waste_percent"] = waste_pct

        # EFFICIENCY
        eff = calc_efficiency(r["act_hank"], r["std_hank"])
        edited_df.at[idx, "efficiency"] = eff

        # OEE
        oee_val = calc_oee(eff, r["run_hours"], r["stop_min"])
        edited_df.at[idx, "oee"] = oee_val

        # TARGET KGS
        target = calc_target_kgs(
            r["std_hank"],
            worked,
            r["run_hours"],
            r["conversion_factor"]
        )
        edited_df.at[idx, "target_kgs"] = target

    # -------------------------------------------------------
    # SAVE BUTTON
    # -------------------------------------------------------
    if st.button("💾 Save Daily Production"):
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        for _, r in edited_df.iterrows():
            entry = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                count_id=r["count_id"],

                spdl_speed=r["spdl_speed"],
                tpi=r["tpi"],
                std_hank=r["std_hank"],
                conversion_factor=r["conversion_factor"],

                stop_min=r["stop_min"],
                run_hours=r["run_hours"],
                worked_spindles=r["worked_spindles"],

                act_hank=r["act_hank"],
                target_kgs=r["target_kgs"],

                prod_kgs=r["prod_kgs"],
                pne_bondas=r["pne_bondas"],
                actual_prdn=r["actual_prdn"],

                waste=r["waste"],
                waste_percent=r["waste_percent"],

                efficiency=r["efficiency"],
                oee=r["oee"],

                remarks=r["remarks"],
            )

            session.add(entry)

        session.commit()
        st.success("✅ Daily Production Saved Successfully!")

import streamlit as st
import pandas as pd
from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    Employee, CountMaster, DailyProduction
)

from utils.calc_engine import (
    safe_float,
    calc_worked_spindles,
    calc_actual_production,
    calc_conversion_factor,
    calc_target_kgs,
    calc_waste_percent,
    calc_efficiency,
    calc_oee,
)

# ---------------------------------------------------------
# DAILY ENTRY PAGE (EXCEL STYLE)
# ---------------------------------------------------------
def daily_entry_page():
    st.title("📘 DAILY PRODUCTION ENTRY (Excel Style)")

    session = next(get_session())

    # ---------------------------------------------------------
    # HEADER FILTERS
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # LOAD MACHINE LIST (NO INITIAL DATA)
    # ---------------------------------------------------------
    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name.asc()).all()

    if not machines:
        st.warning("No machines found for this Mill + Department.")
        return

    # ---------------------------------------------------------
    # CHECK IF DATA ALREADY SAVED FOR THIS DATE
    # ---------------------------------------------------------
    saved_rows = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id
    ).all()

    # ---------------------------------------------------------
    # IF SAVED → USE EXISTING DATA
    # ---------------------------------------------------------
    if saved_rows:
        st.success("Loaded saved data.")

        df_rows = []

        for r in saved_rows:
            count_record = session.query(CountMaster).filter_by(id=r.count_id).first()

            df_rows.append({
                "RF.NO": r.machine.machine_name,
                "COUNT": count_record.count_name if count_record else "",
                "Spdl_Speed": float(r.spdl_speed or 0),
                "TPI": float(r.tpi or 0),
                "STD_Hank": float(r.std_hank or 0),

                "ACT_Hank": float(r.act_hank or 0),
                "Stop_Min": float(r.stop_min or 0),

                "WORKED_SPINDLES": float(r.worked_spindles or 0),

                "TARGET_KGS": float(r.target_kgs or 0),

                "Prodn_KGS": float(r.prod_kgs or 0),
                "Pne_Bondas": float(r.pne_bondas or 0),

                "WASTE_%": float(r.waste_percent or 0),
                "Actual_Prdn": float(r.actual_prdn or 0),
            })

        df = pd.DataFrame(df_rows)

    else:
        # ---------------------------------------------------------
        # NO SAVED DATA → GENERATE BLANK SHEET WITH CONSTANTS
        # ---------------------------------------------------------
        df_rows = []

        for m in machines:

            count_obj = session.query(CountMaster).filter(
                CountMaster.id == m.allocated_count_id
            ).first()

            conversion_factor = safe_float(count_obj.conversion_factor) if count_obj else 0

            df_rows.append({
                "RF.NO": m.machine_name,
                "COUNT": count_obj.count_name if count_obj else "",
                "Spdl_Speed": float(m.spdl_speed or 0),
                "TPI": float(m.tpi or 0),
                "STD_Hank": float(m.std_hank or 0),

                "ACT_Hank": 0.0,
                "Stop_Min": 0.0,

                "WORKED_SPINDLES": 0.0,

                "TARGET_KGS": 0.0,

                "Prodn_KGS": 0.0,
                "Pne_Bondas": 0.0,

                "WASTE_%": 0.0,
                "Actual_Prdn": 0.0,
            })

        df = pd.DataFrame(df_rows)

    # ---------------------------------------------------------
    # SET COLUMN EDIT RULES
    # ---------------------------------------------------------
    readonly_cols = [
        "RF.NO", "COUNT", "Spdl_Speed", "TPI", "STD_Hank",
        "WORKED_SPINDLES", "TARGET_KGS",
        "WASTE_%", "Actual_Prdn"
    ]

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        disabled=readonly_cols
    )

    # ---------------------------------------------------------
    # APPLY CALCULATIONS
    # ---------------------------------------------------------
    for idx, row in edited_df.iterrows():

        machine = machines[idx]
        count_obj = session.query(CountMaster).filter_by(id=machine.allocated_count_id).first()
        conv_factor = safe_float(count_obj.conversion_factor) if count_obj else 0
        spindles = safe_float(machine.spindles)

        # WORKED SPINDLES
        ws = calc_worked_spindles(spindles, row["Stop_Min"])
        edited_df.at[idx, "WORKED_SPINDLES"] = ws

        # TARGET KGS
        target = calc_target_kgs(
            std_hank=row["STD_Hank"],
            worked_spindles=ws,
            conversion_factor=conv_factor,
            run_hours=8  # fixed shift
        )
        edited_df.at[idx, "TARGET_KGS"] = target

        # ACTUAL PRODN = prod - pne
        act_prdn = calc_actual_production(row["Prodn_KGS"], row["Pne_Bondas"])
        edited_df.at[idx, "Actual_Prdn"] = act_prdn

        # WASTE %
        waste_pct = calc_waste_percent(row["Pne_Bondas"], row["Prodn_KGS"])
        edited_df.at[idx, "WASTE_%"] = waste_pct

    # ---------------------------------------------------------
    # SAVE BUTTON
    # ---------------------------------------------------------
    if st.button("💾 Save Production Records"):
        # Remove old
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        # Save new entries
        for idx, row in edited_df.iterrows():
            machine = machines[idx]
            count_obj = session.query(CountMaster).filter_by(id=machine.allocated_count_id).first()

            new = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,

                machine_id=machine.id,
                count_id=machine.allocated_count_id,

                spdl_speed=row["Spdl_Speed"],
                tpi=row["TPI"],
                std_hank=row["STD_Hank"],
                conversion_factor=count_obj.conversion_factor if count_obj else 0,

                act_hank=row["ACT_Hank"],
                stop_min=row["Stop_Min"],
                worked_spindles=row["WORKED_SPINDLES"],

                prod_kgs=row["Prodn_KGS"],
                pne_bondas=row["Pne_Bondas"],
                waste=row["Pne_Bondas"],
                waste_percent=row["WASTE_%"],

                target_kgs=row["TARGET_KGS"],
                actual_prdn=row["Actual_Prdn"],
                run_hours=8,  # default

                efficiency=0,
                oee=0,
            )

            session.add(new)

        session.commit()
        st.success("✅ Production Saved Successfully!")
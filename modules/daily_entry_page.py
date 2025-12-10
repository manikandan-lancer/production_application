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
    calc_actual_production,
    calc_waste_percent,
    calc_efficiency,
    calc_oee,
    calc_target_kgs
)


# -------------------------------------------------------
# DAILY ENTRY PAGE
# -------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session: Session = next(get_session())

    # -------------------------------------------------------
    # FILTER PANEL
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
    # LOAD MACHINES FOR SELECTED MILL/DEPARTMENT
    # -------------------------------------------------------
    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name.asc()).all()

    if not machines:
        st.error("⚠️ No machines found for the selected Mill & Department.")
        return

    # -------------------------------------------------------
    # LOAD SAVED DATA (IF EXISTS)
    # -------------------------------------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id
    ).all()

    # -------------------------------------------------------
    # BUILD TABLE — EXISTING SAVED DATA
    # -------------------------------------------------------
    if saved:
        st.success("Loaded saved entries for the selected filters.")

        df = pd.DataFrame([
            {
                "machine_id": r.machine_id,
                "Machine": r.machine.machine_name,

                "count_id": r.count_id,
                "Count": r.count.count_name if r.count else "",

                "Spindles": r.machine.spindles,
                "Spdl_Speed": float(r.spdl_speed or 0),
                "TPI": float(r.tpi or 0),
                "STD_Hank": float(r.std_hank or 0),

                "ACT_Hank": float(r.act_hank or 0),
                "Stop_Min": float(r.stop_min or 0),

                "Worked_Spindles": float(r.worked_spindles or 0),

                "Prod_Kgs": float(r.prod_kgs or 0),
                "Pne_Bondas": float(r.pne_bondas or 0),
                "Waste": float(r.waste or 0),

                "Actual_Prdn": float(r.actual_prdn or 0),
                "Waste_%": float(r.waste_percent or 0),
                "Efficiency": float(r.efficiency or 0),
                "OEE": float(r.oee or 0),

                "Run_Hours": float(r.run_hours or 0),
                "Target_Kgs": float(r.target_kgs or 0),

                "Remarks": r.remarks or "",
            }
            for r in saved
        ])

    # -------------------------------------------------------
    # BUILD NEW TABLE — FRESH ENTRY
    # -------------------------------------------------------
    else:
        st.info("Creating a fresh entry sheet for selected filters.")

        rows = []
        for m in machines:

            count = session.query(CountMaster).filter_by(id=m.allocated_count_id).first()
            conversion_factor = safe_float(count.conversion_factor) if count else 0.0

            rows.append({
                "machine_id": m.id,
                "Machine": m.machine_name,

                "count_id": count.id if count else None,
                "Count": count.count_name if count else "",

                "Spindles": float(m.spindles or 0),
                "Spdl_Speed": float(m.spdl_speed or 0),
                "TPI": float(m.tpi or 0),
                "STD_Hank": float(m.std_hank or 0),

                "ACT_Hank": 0.0,
                "Stop_Min": 0.0,

                "Worked_Spindles": 0.0,

                "Prod_Kgs": 0.0,
                "Pne_Bondas": 0.0,
                "Waste": 0.0,

                "Actual_Prdn": 0.0,
                "Waste_%": 0.0,
                "Efficiency": 0.0,
                "OEE": 0.0,

                "Run_Hours": 0.0,
                "Target_Kgs": 0.0,

                "Remarks": "",
            })

        df = pd.DataFrame(rows)

    # -------------------------------------------------------
    # REAL-TIME CALCULATIONS
    # -------------------------------------------------------
    for idx, r in df.iterrows():

        sp = safe_float(r["Spindles"])
        stop = safe_float(r["Stop_Min"])

        # Worked Spindles
        df.at[idx, "Worked_Spindles"] = calc_worked_spindles(sp, stop)

        # Actual Production
        df.at[idx, "Actual_Prdn"] = calc_actual_production(
            r["Prod_Kgs"], r["Pne_Bondas"]
        )

        # Waste %
        df.at[idx, "Waste_%"] = calc_waste_percent(
            r["Waste"], r["Prod_Kgs"]
        )

        # Efficiency
        df.at[idx, "Efficiency"] = calc_efficiency(
            r["ACT_Hank"], r["STD_Hank"]
        )

        # OEE
        df.at[idx, "OEE"] = calc_oee(
            df.at[idx, "Efficiency"], r["Run_Hours"], r["Stop_Min"]
        )

        # Target Kgs
        count_obj = session.query(CountMaster).filter_by(id=r["count_id"]).first()
        conv = safe_float(count_obj.conversion_factor) if count_obj else 0

        df.at[idx, "Target_Kgs"] = calc_target_kgs(
            r["STD_Hank"], df.at[idx, "Worked_Spindles"], r["Run_Hours"], conv
        )

    # -------------------------------------------------------
    # DISPLAY TABLE
    # -------------------------------------------------------
    st.subheader("📋 Production Entry")

    readonly = [
        "Machine", "Count", "Spindles", "Spdl_Speed", "TPI",
        "STD_Hank", "Worked_Spindles", "Actual_Prdn", "Waste_%",
        "Efficiency", "OEE", "Target_Kgs"
    ]

    edited_df = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        disabled=readonly
    )

    # -------------------------------------------------------
    # SAVE DATA
    # -------------------------------------------------------
    if st.button("💾 Save Production Entry"):

        # Clear previous records for same filter
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

                spdl_speed=safe_float(r["Spdl_Speed"]),
                tpi=safe_float(r["TPI"]),
                std_hank=safe_float(r["STD_Hank"]),
                spindles=safe_float(r["Spindles"]),

                act_hank=safe_float(r["ACT_Hank"]),
                stop_min=safe_float(r["Stop_Min"]),
                worked_spindles=safe_float(r["Worked_Spindles"]),

                prod_kgs=safe_float(r["Prod_Kgs"]),
                pne_bondas=safe_float(r["Pne_Bondas"]),
                waste=safe_float(r["Waste"]),

                actual_prdn=safe_float(r["Actual_Prdn"]),
                waste_percent=safe_float(r["Waste_%"]),
                efficiency=safe_float(r["Efficiency"]),
                oee=safe_float(r["OEE"]),

                run_hours=safe_float(r["Run_Hours"]),
                target_kgs=safe_float(r["Target_Kgs"]),

                remarks=r["Remarks"]
            )

            session.add(entry)

        session.commit()
        st.success("✅ Daily Production Saved Successfully!")
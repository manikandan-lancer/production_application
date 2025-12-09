import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine, Employee,
    CountMaster, DailyProduction
)

from utils.calc_engine import (
    calc_std_hank,
    calc_conversion_factor,
    calc_actual_production,
    calc_efficiency,
    calc_oee,
    calc_waste_percent,
    calc_target_kgs,
    calc_worked_spindles
)


# -------------------------------------------------------
# DAILY ENTRY PAGE
# -------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session: Session = next(get_session())

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
    # LOAD MACHINES FOR SELECTION
    # -------------------------------------------------------
    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name.asc()).all()

    if not machines:
        st.error("No machines found for selected Mill & Department.")
        return

    # Always fresh data — No old rows should be loaded
    st.info("Fresh entry sheet generated. No stored values are preloaded.")

    # -------------------------------------------------------
    # BUILD INITIAL DATAFRAME
    # -------------------------------------------------------
    rows = []
    for m in machines:
        count_obj = session.query(CountMaster).filter(
            CountMaster.id == m.allocated_count_id
        ).first()

        cf = count_obj.conversion_factor if count_obj else 0

        rows.append({
            "machine_id": m.id,
            "machine_name": m.machine_name,

            "count_id": count_obj.id if count_obj else None,
            "count_name": count_obj.count_name if count_obj else "",

            "spindles": m.spindles,
            "spdl_speed": float(m.spdl_speed or 0),
            "tpi": float(m.tpi or 0),
            "std_hank": float(m.std_hank or 0),

            "conv_factor": float(cf or 0),

            "employee_no": "",
            "employee_name": "",

            "act_hank": 0.0,
            "stop_min": 0.0,
            "run_hours": 0.0,

            "worked_spindles": 0.0,
            "target_kgs": 0.0,

            "prod_kgs": 0.0,
            "pne_bondas": 0.0,

            "actual_prdn": 0.0,
            "waste": 0.0,
            "waste_percent": 0.0,

            "efficiency": 0.0,
            "oee": 0.0,
            "remarks": ""
        })

    df = pd.DataFrame(rows)

    # -------------------------------------------------------
    # DISABLED COLUMNS
    # -------------------------------------------------------
    readonly = [
        "machine_id", "machine_name",
        "count_id", "count_name",
        "spindles", "spdl_speed", "tpi",
        "std_hank", "conv_factor",
        "employee_name",
        "worked_spindles",
        "target_kgs",
        "actual_prdn",
        "efficiency",
        "oee",
        "waste_percent"
    ]

    edited_df = st.data_editor(
        df,
        disabled=readonly,
        use_container_width=True,
        column_config={
            "count_name": st.column_config.TextColumn(disabled=True)
        }
    )

    # -------------------------------------------------------
    # LIVE CALCULATIONS ROW-BY-ROW
    # -------------------------------------------------------
    for idx, r in edited_df.iterrows():

        # Employee Auto-fill
        if r["employee_no"]:
            emp = session.query(Employee).filter(
                Employee.employee_no == str(r["employee_no"]).strip()
            ).first()
            if emp:
                edited_df.at[idx, "employee_name"] = emp.employee_name

        # Worked Spindles
        edited_df.at[idx, "worked_spindles"] = calc_worked_spindles(
            r["spindles"], r["stop_min"]
        )

        # Actual Production
        edited_df.at[idx, "actual_prdn"] = calc_actual_production(
            r["prod_kgs"], r["pne_bondas"]
        )

        # Waste %
        edited_df.at[idx, "waste_percent"] = calc_waste_percent(
            r["waste"], r["prod_kgs"]
        )

        # Efficiency
        edited_df.at[idx, "efficiency"] = calc_efficiency(
            r["act_hank"], r["std_hank"]
        )

        # OEE
        edited_df.at[idx, "oee"] = calc_oee(
            edited_df.at[idx, "efficiency"],
            r["run_hours"],
            r["stop_min"]
        )

        # Target Kgs
        edited_df.at[idx, "target_kgs"] = calc_target_kgs(
            r["std_hank"],
            edited_df.at[idx, "worked_spindles"],
            r["run_hours"],
            r["conv_factor"]
        )

    # -------------------------------------------------------
    # SAVE TO DATABASE
    # -------------------------------------------------------
    if st.button("💾 Save Daily Production"):

        # delete old records for the date-shift selection
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        # insert new
        for _, r in edited_df.iterrows():

            emp = None
            if r["employee_no"]:
                emp = session.query(Employee).filter(
                    Employee.employee_no == str(r["employee_no"])
                ).first()

            entry = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                employee_id=emp.id if emp else None,
                count_id=r["count_id"],

                worked_spindles=r["worked_spindles"],
                spdl_speed=r["spdl_speed"],
                tpi=r["tpi"],
                std_hank=r["std_hank"],

                act_hank=r["act_hank"],
                stop_min=r["stop_min"],
                run_hours=r["run_hours"],
                target_kgs=r["target_kgs"],

                prod_kgs=r["prod_kgs"],
                pne_bondas=r["pne_bondas"],
                actual_prdn=r["actual_prdn"],
                waste=r["waste"],
                efficiency=r["efficiency"],
                oee=r["oee"],
                remarks=r["remarks"]
            )

            session.add(entry)

        session.commit()
        st.success("✅ Daily Production Saved Successfully!")
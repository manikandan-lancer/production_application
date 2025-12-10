import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine, Employee,
    CountMaster, DailyProduction
)

from utils.calc_engine import (
    calc_worked_spindles,
    calc_actual_production,
    calc_efficiency,
    calc_oee,
    calc_target_kgs,
    calc_waste_percent,
    safe
)


# -------------------------------------------------------
# DAILY ENTRY PAGE
# -------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session: Session = next(get_session())

    # -------------------------------------------------------
    # TOP FILTERS
    # -------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        date = st.date_input("Date")

    with col2:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    with col3:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    with col4:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_id = st.selectbox("Shift", shift_map.keys(), format_func=lambda x: shift_map[x])

    st.divider()

    # -------------------------------------------------------
    # LOAD MACHINE LIST
    # -------------------------------------------------------
    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name.asc()).all()

    if not machines:
        st.error("No machines found for this Mill + Department")
        return

    # -------------------------------------------------------
    # CHECK IF DATA EXISTS
    # -------------------------------------------------------
    saved = session.query(DailyProduction).filter_by(
        date=date,
        mill_id=mill_id,
        department_id=dept_id,
        shift_id=shift_id
    ).all()

    # -------------------------------------------------------
    # LOAD SAVED DATA
    # -------------------------------------------------------
    if saved:
        st.success("Loaded existing saved records.")

        df = pd.DataFrame([
            {
                "machine_id": r.machine_id,
                "machine": r.machine.machine_name,

                "count_id": r.count_id,
                "count": r.count.count_name if r.count else "",

                "employee_no": r.employee.employee_no if r.employee else "",
                "employee_name": r.employee.employee_name if r.employee else "",

                "spdl_speed": float(r.spdl_speed or 0),
                "tpi": float(r.tpi or 0),
                "std_hank": float(r.std_hank or 0),

                "stop_min": float(r.stop_min or 0),
                "spindles": float(r.machine.spindles or 0),

                "worked_spindles": float(r.worked_spindles or 0),

                "prod_kgs": float(r.prod_kgs or 0),
                "pne_bondas": float(r.pne_bondas or 0),
                "actual_prdn": float(r.actual_prdn or 0),
                "waste": float(r.waste or 0),
                "waste_percent": float(r.waste_percent or 0),

                "run_hours": float(r.run_hours or 0),
                "act_hank": float(r.act_hank or 0),

                "target_kgs": float(r.target_kgs or 0),
                "efficiency": float(r.efficiency or 0),
                "oee": float(r.oee or 0),

                "remarks": r.remarks or ""
            }
            for r in saved
        ])

    # -------------------------------------------------------
    # GENERATE NEW RECORDS
    # -------------------------------------------------------
    else:
        st.info("Generating fresh entry sheet...")

        rows = []
        for m in machines:
            count_obj = session.query(CountMaster).filter_by(id=m.allocated_count_id).first()

            rows.append({
                "machine_id": m.id,
                "machine": m.machine_name,

                "count_id": count_obj.id if count_obj else None,
                "count": count_obj.count_name if count_obj else "",

                "employee_no": "",
                "employee_name": "",

                "spdl_speed": float(m.spdl_speed or 0),
                "tpi": float(m.tpi or 0),
                "std_hank": float(m.std_hank or 0),

                "stop_min": 0.0,
                "spindles": float(m.spindles or 0),

                "worked_spindles": 0.0,

                "prod_kgs": 0.0,
                "pne_bondas": 0.0,
                "actual_prdn": 0.0,
                "waste": 0.0,
                "waste_percent": 0.0,

                "run_hours": 8.0,   # default shift hours
                "act_hank": 0.0,

                "target_kgs": 0.0,
                "efficiency": 0.0,
                "oee": 0.0,

                "remarks": ""
            })

        df = pd.DataFrame(rows)

    # -------------------------------------------------------
    # AUTO-FILL EMPLOYEE NAME
    # -------------------------------------------------------
    for idx, row in df.iterrows():
        if str(row["employee_no"]).strip():
            emp = session.query(Employee).filter_by(employee_no=row["employee_no"]).first()
            if emp:
                df.at[idx, "employee_name"] = emp.employee_name

    # -------------------------------------------------------
    # READ-ONLY FIELDS
    # -------------------------------------------------------
    readonly = [
        "machine_id", "machine",
        "count_id", "count",
        "employee_name",
        "spdl_speed", "tpi", "std_hank",
        "worked_spindles",
        "actual_prdn", "waste_percent",
        "target_kgs", "efficiency", "oee"
    ]

    edited_df = st.data_editor(
        df,
        disabled=readonly,
        use_container_width=True
    )

    # -------------------------------------------------------
    # LIVE CALCULATIONS LOOP
    # -------------------------------------------------------
    for idx, row in edited_df.iterrows():

        sp = safe(row["spindles"])
        stop = safe(row["stop_min"])
        run_hours = safe(row["run_hours"])
        act_hank = safe(row["act_hank"])

        # LOOKUP conversion factor
        count_obj = session.query(CountMaster).filter_by(id=row["count_id"]).first()
        conversion_factor = safe(count_obj.conversion_factor) if count_obj else 0

        # Worked Spindles
        ws = calc_worked_spindles(sp, stop)
        edited_df.at[idx, "worked_spindles"] = ws

        # Actual Production
        actual = calc_actual_production(row["prod_kgs"], row["pne_bondas"])
        edited_df.at[idx, "actual_prdn"] = actual

        # Target Kgs
        target = calc_target_kgs(row["std_hank"], ws, run_hours, conversion_factor)
        edited_df.at[idx, "target_kgs"] = target

        # Waste %
        waste_percent = calc_waste_percent(row["waste"], row["prod_kgs"])
        edited_df.at[idx, "waste_percent"] = waste_percent

        # Efficiency
        eff = calc_efficiency(act_hank, row["std_hank"])
        edited_df.at[idx, "efficiency"] = eff

        # OEE
        oee_val = calc_oee(eff, run_hours, stop)
        edited_df.at[idx, "oee"] = oee_val

    # -------------------------------------------------------
    # SAVE BUTTON
    # -------------------------------------------------------
    if st.button("💾 Save Daily Production"):

        # Remove any old saved rows
        session.query(DailyProduction).filter_by(
            date=date,
            mill_id=mill_id,
            department_id=dept_id,
            shift_id=shift_id
        ).delete()
        session.commit()

        # INSERT NEW ROWS
        for _, r in edited_df.iterrows():

            emp = None
            if r["employee_no"]:
                emp = session.query(Employee).filter_by(employee_no=r["employee_no"]).first()

            new_entry = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                employee_id=emp.id if emp else None,
                count_id=r["count_id"],

                worked_spindles=safe(r["worked_spindles"]),
                spdl_speed=safe(r["spdl_speed"]),
                tpi=safe(r["tpi"]),
                std_hank=safe(r["std_hank"]),
                act_hank=safe(r["act_hank"]),

                stop_min=safe(r["stop_min"]),
                run_hours=safe(r["run_hours"]),

                target_kgs=safe(r["target_kgs"]),
                prod_kgs=safe(r["prod_kgs"]),
                pne_bondas=safe(r["pne_bondas"]),
                actual_prdn=safe(r["actual_prdn"]),

                waste=safe(r["waste"]),
                waste_percent=safe(r["waste_percent"]),

                efficiency=safe(r["efficiency"]),
                oee=safe(r["oee"]),

                remarks=r["remarks"]
            )

            session.add(new_entry)

        session.commit()
        st.success("✅ Daily Production Saved Successfully!")
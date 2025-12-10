import streamlit as st
import pandas as pd

from database.connection import get_session
from database.models import (
    Mill,
    Department,
    Shift,
    Machine,
    Employee,
    CountMaster,
    DailyProduction,
)

from utils.calc_engine import (
    safe_float,
    calc_std_hank,
    calc_conversion_factor,
    calc_worked_spindles,
    calc_target_kgs,
    calc_actual_production,
    calc_waste_percent,
    calc_efficiency,
    calc_oee,
)



# -------------------------------------------------------
# DAILY ENTRY PAGE
# -------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session = next(get_session())

    # -------------------------------------------------------
    # HEADER FILTERS
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
    # LOAD MACHINE LIST FOR MILL + DEPARTMENT
    # -------------------------------------------------------
    machines = (
        session.query(Machine)
        .filter(
            Machine.mill_id == mill_id,
            Machine.department_id == dept_id,
        )
        .order_by(Machine.machine_name.asc())
        .all()
    )

    if not machines:
        st.error("No machines found for selected Mill & Department.")
        return

    # -------------------------------------------------------
    # CHECK IF SAVED ENTRIES EXIST
    # -------------------------------------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id,
    ).all()

    # -------------------------------------------------------
    # BUILD INPUT TABLE
    # -------------------------------------------------------
    if saved:
        st.success("Loaded saved daily records.")

        df = pd.DataFrame(
            [
                {
                    "machine_id": r.machine_id,
                    "machine": r.machine.machine_name,
                    "count_id": r.count_id,
                    "count": r.count.count_name if r.count else "",
                    "employee_no": r.employee.employee_no if r.employee else "",
                    "employee_name": r.employee.employee_name if r.employee else "",
                    "spdl_speed": r.spdl_speed,
                    "tpi": r.tpi,
                    "std_hank": r.std_hank,
                    "conversion_factor": r.conversion_factor,
                    "stop_min": r.stop_min,
                    "worked_spindles": r.worked_spindles,
                    "run_hours": r.run_hours,
                    "act_hank": r.act_hank,
                    "prod_kgs": r.prod_kgs,
                    "pne_bondas": r.pne_bondas,
                    "actual_prdn": r.actual_prdn,
                    "waste": r.waste,
                    "waste_percent": r.waste_percent,
                    "efficiency": r.efficiency,
                    "oee": r.oee,
                    "remarks": r.remarks,
                }
                for r in saved
            ]
        )

    else:
        st.info("Creating fresh daily entry sheet...")

        rows = []
        for m in machines:

            # Fetch allocated count
            count = session.query(CountMaster).filter_by(id=m.allocated_count_id).first()

            conversion_factor = count.conversion_factor if count else 0.0
            std_hank = calc_std_hank(m.spdl_speed, m.tpi, m.efficiency)

            rows.append(
                {
                    "machine_id": m.id,
                    "machine": m.machine_name,
                    "count_id": count.id if count else None,
                    "count": count.count_name if count else "",
                    "employee_no": "",
                    "employee_name": "",
                    "spdl_speed": m.spdl_speed,
                    "tpi": m.tpi,
                    "std_hank": std_hank,
                    "conversion_factor": conversion_factor,
                    "stop_min": 0,
                    "worked_spindles": 0,
                    "run_hours": m.run_hours or 8,
                    "act_hank": 0,
                    "prod_kgs": 0,
                    "pne_bondas": 0,
                    "actual_prdn": 0,
                    "waste": 0,
                    "waste_percent": 0,
                    "efficiency": 0,
                    "oee": 0,
                    "remarks": "",
                }
            )

        df = pd.DataFrame(rows)

    # -------------------------------------------------------
    # POPULATE EMPLOYEE NAME WHEN NUMBER ENTERED
    # -------------------------------------------------------
    for i, row in df.iterrows():
        emp_no = str(row["employee_no"]).strip()
        if emp_no:
            emp = session.query(Employee).filter_by(employee_no=emp_no).first()
            if emp:
                df.loc[i, "employee_name"] = emp.employee_name

    # -------------------------------------------------------
    # DISABLE SYSTEM CALCULATED FIELDS
    # -------------------------------------------------------
    readonly = [
        "machine",
        "count",
        "employee_name",
        "worked_spindles",
        "std_hank",
        "conversion_factor",
        "actual_prdn",
        "waste_percent",
        "efficiency",
        "oee",
    ]

    edited_df = st.data_editor(df, disabled=readonly, use_container_width=True)

    # -------------------------------------------------------
    # LIVE CALCULATIONS PER ROW
    # -------------------------------------------------------
    for idx, r in edited_df.iterrows():

        speed = safe_float(r["spdl_speed"])
        tpi = safe_float(r["tpi"])
        eff = safe_float(r.get("efficiency_base", 0))

        run_hours = safe_float(r["run_hours"])
        stop_min = safe_float(r["stop_min"])
        act_hank = safe_float(r["act_hank"])
        prod_kgs = safe_float(r["prod_kgs"])
        pne = safe_float(r["pne_bondas"])
        waste = safe_float(r["waste"])

        spindles = (
            session.query(Machine)
            .filter_by(id=r["machine_id"])
            .first()
            .spindles
        )

        conv_factor = safe_float(r["conversion_factor"])
        std_hank = safe_float(r["std_hank"])

        # ---- Calculations ----
        worked = calc_worked_spindles(spindles, stop_min)
        edited_df.at[idx, "worked_spindles"] = worked

        target = calc_target_kgs(std_hank, worked, run_hours, conv_factor)
        edited_df.at[idx, "target_kgs"] = target

        actual_prdn = calc_actual_production(prod_kgs, pne)
        edited_df.at[idx, "actual_prdn"] = actual_prdn

        waste_pct = calc_waste_percent(waste, prod_kgs)
        edited_df.at[idx, "waste_percent"] = waste_pct

        efficiency = calc_efficiency(act_hank, std_hank)
        edited_df.at[idx, "efficiency"] = efficiency

        oee_val = calc_oee(efficiency, run_hours, stop_min)
        edited_df.at[idx, "oee"] = oee_val

    # -------------------------------------------------------
    # SAVE BUTTON
    # -------------------------------------------------------
    if st.button("💾 Save Production"):

        # Remove previous entries for this date + mill + dept + shift
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id,
        ).delete()

        session.commit()

        # Insert new rows
        for _, r in edited_df.iterrows():

            emp = None
            if r["employee_no"]:
                emp = session.query(Employee).filter_by(employee_no=r["employee_no"]).first()

            entry = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                employee_id=emp.id if emp else None,
                count_id=r["count_id"],
                spdl_speed=safe_float(r["spdl_speed"]),
                tpi=safe_float(r["tpi"]),
                std_hank=safe_float(r["std_hank"]),
                conversion_factor=safe_float(r["conversion_factor"]),
                stop_min=safe_float(r["stop_min"]),
                worked_spindles=safe_float(r["worked_spindles"]),
                run_hours=safe_float(r["run_hours"]),
                act_hank=safe_float(r["act_hank"]),
                target_kgs=safe_float(r.get("target_kgs", 0)),
                prod_kgs=safe_float(r["prod_kgs"]),
                pne_bondas=safe_float(r["pne_bondas"]),
                actual_prdn=safe_float(r["actual_prdn"]),
                waste=safe_float(r["waste"]),
                waste_percent=safe_float(r["waste_percent"]),
                efficiency=safe_float(r["efficiency"]),
                oee=safe_float(r["oee"]),
                remarks=r["remarks"],
            )

            session.add(entry)

        session.commit()
        st.success("✅ Production Saved Successfully!")
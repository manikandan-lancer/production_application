import streamlit as st
import pandas as pd
from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine, Employee,
    CountMaster, DailyProduction
)
from utils.calc_engine import (
    calc_worked_spindles, calc_actual_production, calc_waste_percent,
    calc_efficiency, calc_oee, calc_target_kgs
)


# -------------------------------------------------------
# DAILY ENTRY PAGE
# -------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session = next(get_session())

    # -------------------------------------------------------
    # SELECTION PANEL
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
    # LOAD MACHINE LIST
    # -------------------------------------------------------
    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name.asc()).all()

    if not machines:
        st.error("No machines found for selected Mill + Department")
        return

    # -------------------------------------------------------
    # CHECK IF SAVED DATA EXISTS
    # -------------------------------------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id
    ).all()

    # -------------------------------------------------------
    # LOAD SAVED ENTRIES
    # -------------------------------------------------------
    if saved:
        st.success("Loaded saved records.")

        df = pd.DataFrame([
            {
                "machine_id": r.machine_id,
                "machine_name": r.machine.machine_name,

                # COUNT
                "count_id": r.count_id,
                "count_name": r.count.count_name if r.count else "",
                "conversion_factor": float(r.count.conversion_factor if r.count else 0),

                # Employee
                "employee_no": r.employee.employee_no if r.employee else "",
                "employee_name": r.employee.employee_name if r.employee else "",

                # From Machine Master (constant)
                "spindles": float(r.machine.spindles or 0),
                "spdl_speed": float(r.spdl_speed or 0),
                "tpi": float(r.tpi or 0),
                "std_hank": float(r.std_hank or 0),

                # Inputs
                "act_hank": float(r.act_hank or 0),
                "stop_min": float(r.stop_min or 0),
                "run_hours": float(r.run_hours or 0),

                # Computed
                "worked_spindles": float(r.worked_spindles or 0),
                "target_kgs": float(r.target_kgs or 0),

                # Production Data
                "prod_kgs": float(r.prod_kgs or 0),
                "pne_bondas": float(r.pne_bondas or 0),
                "actual_prdn": float(r.actual_prdn or 0),
                "waste": float(r.waste or 0),
                "waste_percent": calc_waste_percent(r.waste, r.prod_kgs),

                # Results
                "efficiency": float(r.efficiency or 0),
                "oee": float(r.oee or 0),

                "remarks": r.remarks or "",
            }
            for r in saved
        ])

    # -------------------------------------------------------
    # CREATE NEW ENTRY SHEET
    # -------------------------------------------------------
    else:
        st.info("Generating new entry sheet...")

        rows = []
        for m in machines:
            count_obj = session.query(CountMaster).filter(
                CountMaster.id == m.allocated_count_id
            ).first()

            rows.append({
                "machine_id": m.id,
                "machine_name": m.machine_name,

                # Count
                "count_id": count_obj.id if count_obj else None,
                "count_name": count_obj.count_name if count_obj else "",
                "conversion_factor": float(count_obj.conversion_factor if count_obj else 0),

                # Employee
                "employee_no": "",
                "employee_name": "",

                # Machine constants
                "spindles": float(m.spindles or 0),
                "spdl_speed": float(m.spdl_speed or 0),
                "tpi": float(m.tpi or 0),
                "std_hank": float(m.std_hank or 0),

                # Inputs
                "act_hank": 0.0,
                "stop_min": 0.0,
                "run_hours": 0.0,

                # Computed
                "worked_spindles": 0.0,
                "target_kgs": 0.0,

                # Production
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
    # AUTO-FILL EMPLOYEE NAME BASED ON NUMBER
    # -------------------------------------------------------
    for idx, row in df.iterrows():
        emp_no = str(row["employee_no"]).strip()
        if emp_no:
            emp = session.query(Employee).filter(Employee.employee_no == emp_no).first()
            if emp:
                df.at[idx, "employee_name"] = emp.employee_name

    # -------------------------------------------------------
    # READ-ONLY COLUMNS
    # -------------------------------------------------------
    readonly_cols = [
        "machine_id", "machine_name",
        "count_id", "count_name",
        "spindles", "spdl_speed", "tpi", "std_hank",
        "conversion_factor",
        "worked_spindles", "target_kgs",
        "actual_prdn", "waste_percent",
        "efficiency", "oee",
        "employee_name"
    ]

    # -------------------------------------------------------
    # SHOW EDITOR
    # -------------------------------------------------------
    edited_df = st.data_editor(
        df,
        disabled=readonly_cols,
        use_container_width=True,
    )

    # -------------------------------------------------------
    # CALCULATIONS LOOP
    # -------------------------------------------------------
    for idx, r in edited_df.iterrows():
        spindles = r["spindles"]
        stop_min = r["stop_min"]
        run_hours = r["run_hours"]
        act_hank = r["act_hank"]
        std_hank = r["std_hank"]
        prod_kgs = r["prod_kgs"]
        pne_bondas = r["pne_bondas"]
        waste = r["waste"]
        cf = r["conversion_factor"]

        # WORKED SPINDLES
        worked = calc_worked_spindles(spindles, stop_min)
        edited_df.at[idx, "worked_spindles"] = worked

        # ACTUAL PRODUCTION
        actual = calc_actual_production(prod_kgs, pne_bondas)
        edited_df.at[idx, "actual_prdn"] = actual

        # WASTE %
        edited_df.at[idx, "waste_percent"] = calc_waste_percent(waste, prod_kgs)

        # EFFICIENCY
        eff = calc_efficiency(act_hank, std_hank)
        edited_df.at[idx, "efficiency"] = eff

        # OEE
        edited_df.at[idx, "oee"] = calc_oee(eff, run_hours, stop_min)

        # TARGET KGS
        target = calc_target_kgs(std_hank, worked, run_hours, cf)
        edited_df.at[idx, "target_kgs"] = target

    # -------------------------------------------------------
    # SAVE BUTTON
    # -------------------------------------------------------
    if st.button("💾 Save Daily Production"):

        # DELETE OLD ENTRIES
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        # INSERT NEW ENTRIES
        for _, r in edited_df.iterrows():

            emp_obj = None
            if r["employee_no"]:
                emp_obj = session.query(Employee).filter(
                    Employee.employee_no == r["employee_no"]
                ).first()

            entry = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],

                employee_id=emp_obj.id if emp_obj else None,
                count_id=r["count_id"],

                worked_spindles=r["worked_spindles"],
                spdl_speed=r["spdl_speed"],
                tpi=r["tpi"],
                std_hank=r["std_hank"],
                act_hank=r["act_hank"],
                stop_min=r["stop_min"],
                target_kgs=r["target_kgs"],

                prod_kgs=r["prod_kgs"],
                pne_bondas=r["pne_bondas"],
                actual_prdn=r["actual_prdn"],
                waste=r["waste"],
                run_hours=r["run_hours"],

                efficiency=r["efficiency"],
                oee=r["oee"],

                remarks=r["remarks"],
            )

            session.add(entry)

        session.commit()
        st.success("✅ Daily Production Saved Successfully!")
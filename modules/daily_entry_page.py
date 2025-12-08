import streamlit as st
import pandas as pd
from database.connection import SessionLocal
from database.models import (
    Mill, Department, Shift, Machine, Employee,
    CountMaster, DailyProduction
)

# -------------------------------------------------------
# DAILY ENTRY PAGE
# -------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session = SessionLocal()

    # -------------------------------------------------------
    # SELECTION PANEL
    # -------------------------------------------------------
    colA, colB, colC, colD = st.columns(4)

    with colA:
        date = st.date_input("Date")

    with colB:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox(
            "Mill",
            mill_map.keys(),
            format_func=lambda x: mill_map[x]
        )

    with colC:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_id = st.selectbox(
            "Department",
            dept_map.keys(),
            format_func=lambda x: dept_map[x]
        )

    with colD:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_id = st.selectbox(
            "Shift",
            shift_map.keys(),
            format_func=lambda x: shift_map[x]
        )

    st.divider()

    # -------------------------------------------------------
    # LOAD MACHINE LIST FOR THIS MILL + DEPARTMENT
    # -------------------------------------------------------
    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name.asc()).all()

    if not machines:
        st.error("No machines found for selected Mill + Department")
        return

    # -------------------------------------------------------
    # CHECK EXISTING SAVED RECORDS
    # -------------------------------------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id
    ).all()

    if saved:
        st.success("Loaded saved records.")
        df = pd.DataFrame([
            {
                "machine_id": r.machine_id,
                "machine_name": r.machine.machine_name,
                "count_name": r.count.count_name if r.count else "",
                "employee_no": r.employee.employee_no if r.employee else "",
                "employee_name": r.employee.employee_name if r.employee else "",
                "worked_spindles": r.worked_spindles,
                "spdl_speed": r.spdl_speed,
                "tpi": r.tpi,
                "std_hank": r.std_hank,
                "act_hank": r.act_hank,
                "stop_min": r.stop_min,
                "target_kgs": r.target_kgs,
                "prod_kgs": r.prod_kgs,
                "pne_bondas": r.pne_bondas,
                "actual_prdn": r.actual_prdn,
                "waste": r.waste,
                "run_hours": r.run_hours,
                "remarks": r.remarks,
                "efficiency": r.efficiency,
                "oee": r.oee,
                "count_id": r.count_id
            }
            for r in saved
        ])

    else:
        st.info("Generating new entry sheet...")

        rows = []
        for m in machines:

            allocated_count = session.query(CountMaster).filter(
                CountMaster.id == m.allocated_count_id
            ).first()

            rows.append({
                "machine_id": m.id,
                "machine_name": m.machine_name,
                "count_id": allocated_count.id if allocated_count else None,
                "count_name": allocated_count.count_name if allocated_count else "",
                "employee_no": "",
                "employee_name": "",
                "worked_spindles": 0,
                "spdl_speed": 0,
                "tpi": 0,
                "std_hank": 0,
                "act_hank": 0,
                "stop_min": 0,
                "target_kgs": 0,
                "prod_kgs": 0,
                "pne_bondas": 0,
                "actual_prdn": 0,
                "waste": 0,
                "run_hours": 0,
                "remarks": "",
                "efficiency": 0,
                "oee": 0
            })

        df = pd.DataFrame(rows)

    # -------------------------------------------------------
    # AUTO-FILL EMPLOYEE NAME BASED ON employee_no
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
        "machine_id", "machine_name", "count_id", "count_name",
        "employee_name", "actual_prdn", "efficiency", "oee"
    ]

    # -------------------------------------------------------
    # SHOW EDITOR
    # -------------------------------------------------------
    edited_df = st.data_editor(
        df,
        disabled=readonly_cols,
        use_container_width=True
    )

    # -------------------------------------------------------
    # CALCULATIONS
    # -------------------------------------------------------
    for idx, r in edited_df.iterrows():

        # actual_prdn = prod_kgs - pne_bondas
        actual_prdn = (r["prod_kgs"] or 0) - (r["pne_bondas"] or 0)
        edited_df.at[idx, "actual_prdn"] = actual_prdn

        # efficiency placeholder
        edited_df.at[idx, "efficiency"] = 0

        # oee placeholder
        edited_df.at[idx, "oee"] = 0

    # -------------------------------------------------------
    # SAVE BUTTON
    # -------------------------------------------------------
    if st.button("💾 Save Daily Production"):
        # Remove old saved rows
        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()
        session.commit()

        # Insert new rows
        for _, r in edited_df.iterrows():
            entry = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                employee_id=session.query(Employee)
                    .filter(Employee.employee_no == r["employee_no"]).first().id
                    if r["employee_no"] else None,
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
                remarks=r["remarks"],
                efficiency=r["efficiency"],
                oee=r["oee"]
            )
            session.add(entry)

        session.commit()
        st.success("✅ Daily Production Saved Successfully!")
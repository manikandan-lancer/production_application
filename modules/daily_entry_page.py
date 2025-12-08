import streamlit as st
import pandas as pd
from datetime import date
from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine, Employee,
    CountMaster, DailyProduction
)


def daily_entry_page():

    st.title("🧾 Daily Production Entry")

    session = get_session()

    # ----------------------------------------------------------------------
    # LOAD DROPDOWN MASTER DATA
    # ----------------------------------------------------------------------
    mills = session.query(Mill).all()
    departments = session.query(Department).all()
    shifts = session.query(Shift).all()
    employees = session.query(Employee).all()
    counts = session.query(CountMaster).all()

    # ----------------------------------------------------------------------
    # USER FILTERS
    # ----------------------------------------------------------------------
    st.sidebar.header("Filters")

    selected_date = st.sidebar.date_input("Select Date", date.today())

    selected_mill = st.sidebar.selectbox(
        "Select Mill", mills, format_func=lambda x: x.mill_name
    )

    selected_department = st.sidebar.selectbox(
        "Select Department", departments, format_func=lambda x: x.department_name
    )

    selected_shift = st.sidebar.selectbox(
        "Select Shift", shifts, format_func=lambda x: x.shift_name
    )

    selected_mill_id = selected_mill.id
    selected_department_id = selected_department.id
    selected_shift_id = selected_shift.id

    # ----------------------------------------------------------------------
    # LOAD MACHINES FOR SELECTED MILL + DEPARTMENT
    # ----------------------------------------------------------------------
    machines = (
        session.query(Machine)
        .filter_by(mill_id=selected_mill_id, department_id=selected_department_id)
        .order_by(Machine.id)
        .all()
    )

    if not machines:
        st.warning("⚠ No machines found for this Mill + Department.")
        return

    # ----------------------------------------------------------------------
    # CHECK IF RECORDS ALREADY EXIST FOR THIS DATE + MILL + DEPT + SHIFT
    # ----------------------------------------------------------------------
    existing_records = (
        session.query(DailyProduction)
        .filter_by(
            date=selected_date,
            mill_id=selected_mill_id,
            department_id=selected_department_id,
            shift_id=selected_shift_id,
        )
        .order_by(DailyProduction.machine_id)
        .all()
    )

    # ----------------------------------------------------------------------
    # BUILD NEW OR EXISTING ENTRY TABLE
    # ----------------------------------------------------------------------
    rows = []

    if existing_records:
        st.info("📌 Records already exist — loaded for editing.")

        for rec in existing_records:
            rows.append(
                {
                    "machine_id": rec.machine_id,
                    "machine_name": rec.machine.machine_name,
                    "employee_id": rec.employee_id,
                    "employee_name": rec.employee.employee_name if rec.employee else "",
                    "count_id": rec.count_id,
                    "count_name": rec.count.count_name if rec.count else "",

                    "worked_spindles": rec.worked_spindles or 0,
                    "spdl_speed": rec.spdl_speed or 0,
                    "tpi": rec.tpi or 0,
                    "std_hank": rec.std_hank or 0,
                    "act_hank": rec.act_hank or 0,
                    "stop_min": rec.stop_min or 0,
                    "target_kgs": rec.target_kgs or 0,
                    "prod_kgs": rec.prod_kgs or 0,
                    "pne_bondas": rec.pne_bondas or 0,
                    "actual_prdn": rec.actual_prdn or 0,
                    "waste": rec.waste or 0,
                    "run_hours": rec.run_hours or 0,
                    "remarks": rec.remarks or "",
                }
            )

    else:
        st.info("🆕 No saved records — generating new entry form.")

        for m in machines:
            rows.append(
                {
                    "machine_id": m.id,
                    "machine_name": m.machine_name,

                    "employee_id": None,
                    "employee_name": "",

                    "count_id": m.allocated_count_id,
                    "count_name": (
                        m.allocated_count.count_name if m.allocated_count else ""
                    ),

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
                }
            )

    # ----------------------------------------------------------------------
    # CREATE DATAFRAME
    # ----------------------------------------------------------------------
    df = pd.DataFrame(rows)

    st.write("### ✏ Enter Production Details")
    edited_df = st.data_editor(
        df,
        key="daily_entry_editor",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "employee_id": st.column_config.NumberColumn("Employee ID"),
            "worked_spindles": st.column_config.NumberColumn("Worked Spindles"),
            "spdl_speed": st.column_config.NumberColumn("Spdl Speed"),
            "tpi": st.column_config.NumberColumn("TPI"),
            "std_hank": st.column_config.NumberColumn("STD Hank"),
            "act_hank": st.column_config.NumberColumn("ACT Hank"),
            "stop_min": st.column_config.NumberColumn("Stop Min"),
            "target_kgs": st.column_config.NumberColumn("Target Kgs"),
            "prod_kgs": st.column_config.NumberColumn("Prod Kgs"),
            "pne_bondas": st.column_config.NumberColumn("Pne Bondas"),
            "actual_prdn": st.column_config.NumberColumn("Actual Prdn"),
            "waste": st.column_config.NumberColumn("Waste"),
            "run_hours": st.column_config.NumberColumn("Run Hours"),
            "remarks": st.column_config.TextColumn("Remarks"),
        },
    )

    # ----------------------------------------------------------------------
    # SAVE BUTTON
    # ----------------------------------------------------------------------
    if st.button("💾 Save Production Data"):

        # Remove existing old records (overwrite mode)
        session.query(DailyProduction).filter_by(
            date=selected_date,
            mill_id=selected_mill_id,
            department_id=selected_department_id,
            shift_id=selected_shift_id,
        ).delete()

        # Insert updated values
        for _, row in edited_df.iterrows():

            rec = DailyProduction(
                date=selected_date,
                mill_id=selected_mill_id,
                department_id=selected_department_id,
                shift_id=selected_shift_id,
                machine_id=int(row["machine_id"]),
                employee_id=row["employee_id"],
                count_id=row["count_id"],

                worked_spindles=row["worked_spindles"],
                spdl_speed=row["spdl_speed"],
                tpi=row["tpi"],
                std_hank=row["std_hank"],
                act_hank=row["act_hank"],
                stop_min=row["stop_min"],
                target_kgs=row["target_kgs"],
                prod_kgs=row["prod_kgs"],
                pne_bondas=row["pne_bondas"],
                actual_prdn=row["actual_prdn"],
                waste=row["waste"],
                run_hours=row["run_hours"],
                remarks=row["remarks"],
            )

            session.add(rec)

        session.commit()
        st.success("✅ Daily production saved successfully!")
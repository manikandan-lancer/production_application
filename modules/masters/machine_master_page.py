import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import Mill, Department, Machine
from utils.calc_engine import (
    safe_float,
    calc_std_hank,
)


# -------------------------------------------------------
# MACHINE MASTER PAGE
# -------------------------------------------------------
def machine_master_page():
    st.title("🛠 MACHINE MASTER — Machine Constants")

    session: Session = next(get_session())

    st.info("""
    ✔ Define machines & constants  
    ✔ STD Hank auto-calculates  
    ✔ Changes reflect instantly in Daily Entry & Dashboard  
    """)

    # -------------------------------------------------------
    # LOAD MASTER DATA
    # -------------------------------------------------------
    mills = session.query(Mill).order_by(Mill.mill_name.asc()).all()
    departments = session.query(Department).order_by(Department.department_name).all()

    mill_map = {m.id: m.mill_name for m in mills}
    dept_map = {d.id: d.department_name for d in departments}

    # -------------------------------------------------------
    # ADD NEW MACHINE
    # -------------------------------------------------------
    st.subheader("➕ Add New Machine")

    with st.form("add_machine_form"):

        col1, col2 = st.columns(2)

        with col1:
            mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
            dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])
            machine_name = st.text_input("Machine Name (e.g., A01, B10)")

        with col2:
            spindles = st.number_input("Total Spindles", min_value=0, step=1)
            spdl_speed = st.number_input("Speed (Spindle RPM)", min_value=0.0, step=0.01)
            tpi = st.number_input("TPI", min_value=0.0, step=0.01)
            efficiency = st.number_input("Efficiency (%)", min_value=0.0, step=0.01)

        # LIVE STD HANK PREVIEW
        std_hank_preview = calc_std_hank(spdl_speed, tpi, efficiency)
        st.write(f"📘 **STD Hank Preview:** `{std_hank_preview}`")

        submit_new = st.form_submit_button("💾 Save Machine")

        if submit_new:

            # VALIDATIONS
            if machine_name.strip() == "":
                st.error("Machine Name cannot be empty.")
                return

            # Prevent duplicate A01/B05 etc inside same mill+department
            existing = (
                session.query(Machine)
                .filter(
                    Machine.mill_id == mill_id,
                    Machine.department_id == dept_id,
                    Machine.machine_name == machine_name.strip()
                )
                .first()
            )

            if existing:
                st.error(f"❌ Machine '{machine_name}' already exists under this Mill + Department.")
                return

            new_machine = Machine(
                mill_id=mill_id,
                department_id=dept_id,
                machine_name=machine_name.strip(),
                spindles=spindles,
                spdl_speed=spdl_speed,
                tpi=tpi,
                efficiency=efficiency,
                std_hank=std_hank_preview,
            )

            session.add(new_machine)
            session.commit()

            st.success("✅ Machine Added Successfully!")

    st.divider()

    # -------------------------------------------------------
    # EXISTING MACHINES
    # -------------------------------------------------------
    st.subheader("📄 Existing Machines")

    machines = (
        session.query(Machine)
        .order_by(Machine.mill_id, Machine.department_id, Machine.machine_name)
        .all()
    )

    if not machines:
        st.warning("No machine records found.")
        return

    df = pd.DataFrame([
        {
            "ID": m.id,
            "Mill": m.mill.mill_name,
            "Department": m.department.department_name,
            "Machine": m.machine_name,
            "Spindles": m.spindles,
            "Speed (RPM)": float(m.spdl_speed or 0),
            "TPI": float(m.tpi or 0),
            "Efficiency (%)": float(m.efficiency or 0),
            "STD Hank": float(m.std_hank or 0),
        }
        for m in machines
    ])

    # Editable table (constants only)
    edited = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ID": st.column_config.TextColumn(disabled=True),
            "Mill": st.column_config.TextColumn(disabled=True),
            "Department": st.column_config.TextColumn(disabled=True),
            "Machine": st.column_config.TextColumn(disabled=True),
            "STD Hank": st.column_config.NumberColumn(disabled=True),
        }
    )

    # -------------------------------------------------------
    # SAVE EDITS
    # -------------------------------------------------------
    if st.button("💾 Update Machines"):

        for _, row in edited.iterrows():

            machine = session.query(Machine).filter_by(id=row["ID"]).first()
            if not machine:
                continue

            # Update constants
            machine.spindles = safe_float(row["Spindles"])
            machine.spdl_speed = safe_float(row["Speed (RPM)"])
            machine.tpi = safe_float(row["TPI"])
            machine.efficiency = safe_float(row["Efficiency (%)"])

            # Recalculate STD HANK
            machine.std_hank = calc_std_hank(
                machine.spdl_speed,
                machine.tpi,
                machine.efficiency
            )

        session.commit()

        st.success("✅ Machine Master Updated Successfully!")
        st.info("Daily Entry + Dashboard will now reflect updated machine constants.")
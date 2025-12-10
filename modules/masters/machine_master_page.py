import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import Mill, Department, Machine, CountMaster
from utils.calc_engine import (
    calc_std_hank,
    safe
)


# -------------------------------------------------------
# MACHINE MASTER PAGE
# -------------------------------------------------------
def machine_master_page():
    st.title("🛠️ Machine Master")

    session: Session = next(get_session())

    st.info("Manage machines. STD Hank auto-calculates whenever Speed, TPI, or Efficiency changes.")

    # -------------------------------------------------------
    # LOAD DROPDOWNS
    # -------------------------------------------------------
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}

    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}

    # -------------------------------------------------------
    # ADD MACHINE FORM
    # -------------------------------------------------------
    st.subheader("➕ Add New Machine")

    with st.form("add_machine_form"):
        col1, col2 = st.columns(2)

        # LEFT SIDE
        with col1:
            mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
            dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])
            machine_name = st.text_input("Machine Name (Ex: A01, B05)")

            allocated_count_id = st.selectbox(
                "Allocated Count",
                [None] + list(count_map.keys()),
                format_func=lambda x: "" if x is None else count_map[x]
            )

        # RIGHT SIDE
        with col2:
            spindles = st.number_input("Spindles", step=1, min_value=0)
            spdl_speed = st.number_input("Speed (RPM)", step=0.01, min_value=0.0)
            tpi = st.number_input("TPI", step=0.01, min_value=0.0)
            efficiency = st.number_input("Efficiency (%)", step=0.01, min_value=0.0)

        # LIVE STD HANK preview
        std_hank_value = calc_std_hank(spdl_speed, tpi, efficiency)
        st.write(f"📘 **STD Hank (Auto):** `{std_hank_value}`")

        submitted = st.form_submit_button("💾 Save Machine")

        if submitted:
            if not machine_name.strip():
                st.error("Machine name cannot be empty.")
            else:
                new_machine = Machine(
                    mill_id=mill_id,
                    department_id=dept_id,
                    machine_name=machine_name,
                    spindles=spindles,
                    spdl_speed=spdl_speed,
                    tpi=tpi,
                    efficiency=efficiency,
                    std_hank=std_hank_value,
                    allocated_count_id=allocated_count_id
                )

                session.add(new_machine)
                session.commit()
                st.success("✅ Machine Added Successfully!")

    st.divider()

    # -------------------------------------------------------
    # EXISTING MACHINE LIST
    # -------------------------------------------------------
    st.subheader("📄 Machine List")

    machine_list = session.query(Machine).order_by(Machine.mill_id, Machine.machine_name).all()

    if not machine_list:
        st.warning("No machines found.")
        return

    df = pd.DataFrame([
        {
            "ID": m.id,
            "Mill": m.mill.mill_name,
            "Department": m.department.department_name,
            "Machine Name": m.machine_name,
            "Count": m.allocated_count.count_name if m.allocated_count else "",
            "Spindles": m.spindles,
            "Speed": float(m.spdl_speed or 0),
            "TPI": float(m.tpi or 0),
            "Efficiency (%)": float(m.efficiency or 0),
            "STD Hank": float(m.std_hank or 0),
        }
        for m in machine_list
    ])

    st.dataframe(df, use_container_width=True)

    st.divider()

    # -------------------------------------------------------
    # EDIT MACHINE DETAILS
    # -------------------------------------------------------
    st.subheader("✏️ Edit Machines")

    edited_df = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ID": st.column_config.NumberColumn(disabled=True),
            "Mill": st.column_config.TextColumn(disabled=True),
            "Department": st.column_config.TextColumn(disabled=True),
            "Machine Name": st.column_config.TextColumn(disabled=True),
            "STD Hank": st.column_config.NumberColumn(disabled=True),
        }
    )

    if st.button("💾 Save Updates"):

        for _, row in edited_df.iterrows():
            machine = session.query(Machine).filter_by(id=row["ID"]).first()

            if machine:
                # Editable fields
                machine.spindles = safe(row["Spindles"])
                machine.spdl_speed = safe(row["Speed"])
                machine.tpi = safe(row["TPI"])
                machine.efficiency = safe(row["Efficiency (%)"])

                # Recalculate STD HANK
                machine.std_hank = calc_std_hank(
                    machine.spdl_speed,
                    machine.tpi,
                    machine.efficiency
                )

        session.commit()
        st.success("✅ Machine Records Updated Successfully!")

        st.info("Daily Entry Page & Dashboard will now show updated STD Hank, Speed & TPI live.")
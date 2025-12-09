import streamlit as st
import pandas as pd
from database.connection import get_session
from database.models import Mill, Department, CountMaster, Machine


# -------------------------------------------------------
# MACHINE MASTER PAGE
# -------------------------------------------------------
def machine_master_page():

    session = next(get_session())

    st.header("⚙️ Machine Master")

    # ------------------------------
    # Dropdowns for Mill & Department
    # ------------------------------
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    mill_id = st.selectbox(
        "Mill",
        mill_map.keys(),
        format_func=lambda x: mill_map[x]
    )

    departments = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in departments}

    dept_id = st.selectbox(
        "Department",
        dept_map.keys(),
        format_func=lambda x: dept_map[x]
    )

    # ------------------------------
    # Machine name
    # ------------------------------
    machine_name = st.text_input("Machine Name (A01, B05, ...)", "")

    # ------------------------------
    # Spindles
    # ------------------------------
    spindles = st.number_input("Spindles", min_value=0, value=0)

    # ------------------------------
    # Spindle Speed (NEW FIELD)
    # ------------------------------
    spdl_speed = st.number_input("Spindle Speed (RPM)", min_value=0.0, value=0.0, step=0.01)

    # ------------------------------
    # TPI (NEW FIELD)
    # ------------------------------
    tpi = st.number_input("TPI (Twist Per Inch)", min_value=0.0, value=0.0, step=0.01)

    # ------------------------------
    # Allocated Count
    # ------------------------------
    counts = session.query(CountMaster).filter(CountMaster.mill_id == mill_id).all()
    count_map = {c.id: c.count_name for c in counts}

    count_id = st.selectbox(
        "Allocated Count",
        [None] + list(count_map.keys()),
        format_func=lambda x: "None" if x is None else count_map[x]
    )

    # ------------------------------
    # SAVE MACHINE
    # ------------------------------
    if st.button("Save Machine"):

        if not machine_name:
            st.error("Machine name cannot be empty.")
            return

        existing = session.query(Machine).filter_by(machine_name=machine_name).first()

        if existing:
            # UPDATE
            existing.mill_id = mill_id
            existing.department_id = dept_id
            existing.spindles = spindles
            existing.spdl_speed = spdl_speed
            existing.tpi = tpi
            existing.allocated_count_id = count_id

            session.commit()
            st.success(f"Updated Machine {machine_name}")
        else:
            # INSERT
            m = Machine(
                machine_name=machine_name,
                mill_id=mill_id,
                department_id=dept_id,
                spindles=spindles,
                spdl_speed=spdl_speed,
                tpi=tpi,
                allocated_count_id=count_id
            )
            session.add(m)
            session.commit()
            st.success(f"Added Machine {machine_name}")

    st.markdown("---")

    # -------------------------------------------------------
    # TABLE VIEW OF MACHINES
    # -------------------------------------------------------
    st.subheader("📄 Machine List")

    machines = session.query(Machine).filter(
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name.asc()).all()

    table = []

    for m in machines:
        table.append({
            "Machine": m.machine_name,
            "Spindles": m.spindles,
            "Spindle Speed": float(m.spdl_speed or 0),
            "TPI": float(m.tpi or 0),
            "Count": m.allocated_count.count_name if m.allocated_count else ""
        })

    df = pd.DataFrame(table)

    st.dataframe(df, use_container_width=True)

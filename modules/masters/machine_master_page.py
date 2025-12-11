import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import Mill, Department, Machine, CountMaster
from utils.calc_engine import safe_float, calc_std_hank


# -------------------------------------------------------
# MACHINE MASTER PAGE (UPDATED)
# -------------------------------------------------------
def machine_master_page():
    st.title("🛠 Machine Master")

    session: Session = next(get_session())

    st.info("""
    **Define machine constants for each Mill & Department.**  
    - Spdl Speed, TPI, Spindles are fixed constants  
    - Efficiency is NOT entered here anymore  
    - STD Hank auto-calculates using:
        SpdlSpeed / TPI × 0.01587394 × (StdHankEfficiency_from_CountMaster / 100)
    """)

    # -------------------------------------------------------
    # LOAD MILLS & DEPARTMENTS
    # -------------------------------------------------------
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}

    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}

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
            spindles = st.number_input("Spindles", min_value=0, step=1)
            spdl_speed = st.number_input("Spindle Speed", min_value=0.0, step=0.01)
            tpi = st.number_input("TPI", min_value=0.0, step=0.01)
            allocated_count_id = st.selectbox(
                "Allocated Count",
                [None] + list(count_map.keys()),
                format_func=lambda x: "" if x is None else count_map[x],
            )

        # PREVIEW STD HANK
        std_eff = 0
        if allocated_count_id:
            c = session.query(CountMaster).filter_by(id=allocated_count_id).first()
            std_eff = safe_float(c.std_hank_efficiency)

        std_hank_preview = calc_std_hank(spdl_speed, tpi, std_eff)
        st.write(f"📘 **STD Hank Preview:** `{std_hank_preview}`")

        submitted = st.form_submit_button("💾 Save Machine")

        if submitted:
            if not machine_name.strip():
                st.error("Machine name cannot be empty.")
                return

            new_machine = Machine(
                mill_id=mill_id,
                department_id=dept_id,
                machine_name=machine_name.strip(),
                spindles=spindles,
                spdl_speed=spdl_speed,
                tpi=tpi,
                allocated_count_id=allocated_count_id,
                std_hank=std_hank_preview,
            )
            session.add(new_machine)
            session.commit()

            st.success("✔ Machine Added Successfully")

    st.divider()

    # -------------------------------------------------------
    # EXISTING MACHINE TABLE (Excel-like Editable Grid)
    # -------------------------------------------------------
    st.subheader("📄 Existing Machines")

    machines = (
        session.query(Machine)
        .order_by(Machine.mill_id, Machine.department_id, Machine.machine_name)
        .all()
    )

    if not machines:
        st.warning("No machines added yet.")
        return

    df = []
    for m in machines:
        c = session.query(CountMaster).filter_by(id=m.allocated_count_id).first()

        df.append({
            "ID": m.id,
            "Mill": m.mill.mill_name,
            "Department": m.department.department_name,
            "Machine Name": m.machine_name,
            "Spindles": m.spindles,
            "Spindle Speed": float(m.spdl_speed or 0),
            "TPI": float(m.tpi or 0),
            "Allocated Count": c.id if c else None,
            "Allocated Count Name": c.count_name if c else "",
            "Std Hank": float(m.std_hank or 0),
        })

    df = pd.DataFrame(df)

    editor = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ID": st.column_config.NumberColumn(disabled=True),
            "Mill": st.column_config.TextColumn(disabled=True),
            "Department": st.column_config.TextColumn(disabled=True),
            "Allocated Count Name": st.column_config.TextColumn(disabled=True),
            "Std Hank": st.column_config.NumberColumn(disabled=True),
        }
    )

    # -------------------------------------------------------
    # SAVE EDITS BACK INTO DB
    # -------------------------------------------------------
    if st.button("💾 Save Updates"):

        for _, row in editor.iterrows():
            m = session.query(Machine).filter_by(id=row["ID"]).first()
            if not m:
                continue

            m.spindles = safe_float(row["Spindles"])
            m.spdl_speed = safe_float(row["Spindle Speed"])
            m.tpi = safe_float(row["TPI"])
            m.allocated_count_id = row["Allocated Count"]

            # RECALCULATE STD HANK
            c = session.query(CountMaster).filter_by(id=row["Allocated Count"]).first()
            std_eff = safe_float(c.std_hank_efficiency) if c else 0

            m.std_hank = calc_std_hank(m.spdl_speed, m.tpi, std_eff)

        session.commit()
        st.success("✔ Machine Master Updated Successfully")

        st.info("Daily Entry will now use updated Machine Master values.")
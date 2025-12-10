import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import Mill, Department, CountMaster, Machine
from utils.calc_engine import calc_std_hank, safe_float


# -------------------------------------------------------
# MACHINE MASTER PAGE
# -------------------------------------------------------
def machine_master_page():
    st.title("🛠️ Machine Master")

    session: Session = next(get_session())

    st.info(
        "Define machines and their constant parameters. "
        "STD Hank updates automatically based on Speed, TPI & Efficiency. "
        "Changes here instantly reflect in Daily Entry & Dashboard."
    )

    # -------------------------------------------------------
    # LOAD MILLS & DEPARTMENTS
    # -------------------------------------------------------
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    departments = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in departments}

    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}

    # -------------------------------------------------------
    # ADD NEW MACHINE
    # -------------------------------------------------------
    st.subheader("➕ Add New Machine")

    with st.form("add_machine_form"):
        colA, colB = st.columns(2)

        with colA:
            mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
            department_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])
            machine_name = st.text_input("Machine Name (Ex: A01, B10)")

        with colB:
            spindles = st.number_input("Spindles", min_value=0, step=1)
            count_id = st.selectbox(
                "Allocated Count",
                [None] + list(count_map.keys()),
                format_func=lambda x: "" if x is None else count_map[x]
            )

            spdl_speed = st.number_input("Spindle Speed", min_value=0.0, step=0.01)
            tpi = st.number_input("TPI", min_value=0.0, step=0.01)
            efficiency = st.number_input("Efficiency (%)", min_value=0.0, step=0.01)

        # AUTO CALCULATE STD HANK
        std_hank_preview = calc_std_hank(spdl_speed, tpi, efficiency)
        st.write(f"📘 **STD Hank Preview:** `{std_hank_preview}`")

        submit = st.form_submit_button("💾 Save Machine")

        if submit:
            if machine_name.strip() == "":
                st.error("Machine name cannot be empty.")
            else:
                machine = Machine(
                    mill_id=mill_id,
                    department_id=department_id,
                    allocated_count_id=count_id,
                    machine_name=machine_name,
                    spindles=spindles,
                    spdl_speed=spdl_speed,
                    tpi=tpi,
                    efficiency=efficiency,
                    std_hank=std_hank_preview,
                )
                session.add(machine)
                session.commit()
                st.success("✅ Machine Added Successfully!")

    st.divider()

    # -------------------------------------------------------
    # LIST MACHINES
    # -------------------------------------------------------
    st.subheader("📄 Existing Machines")

    machines = session.query(Machine).order_by(Machine.id.asc()).all()

    if not machines:
        st.warning("No machines configured yet.")
        return

    df = pd.DataFrame([
        {
            "ID": m.id,
            "Mill": m.mill.mill_name,
            "Department": m.department.department_name,
            "Machine": m.machine_name,
            "Spindles": m.spindles,
            "Allocated Count": count_map.get(m.allocated_count_id, ""),
            "Spdl_Speed": float(m.spdl_speed or 0),
            "TPI": float(m.tpi or 0),
            "Efficiency (%)": float(m.efficiency or 0),
            "STD_Hank": float(m.std_hank or 0),
        }
        for m in machines
    ])

    edited_df = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ID": st.column_config.NumberColumn(disabled=True),
            "Mill": st.column_config.TextColumn(disabled=True),
            "Department": st.column_config.TextColumn(disabled=True),
            "Allocated Count": st.column_config.TextColumn(disabled=True),
            "STD_Hank": st.column_config.NumberColumn(disabled=True),
        }
    )

    # -------------------------------------------------------
    # SAVE UPDATES
    # -------------------------------------------------------
    if st.button("💾 Update Machine Records"):

        for _, row in edited_df.iterrows():

            m = session.query(Machine).filter_by(id=row["ID"]).first()
            if m:
                m.spindles = safe_float(row["Spindles"])
                m.spdl_speed = safe_float(row["Spdl_Speed"])
                m.tpi = safe_float(row["TPI"])
                m.efficiency = safe_float(row["Efficiency (%)"])

                # Auto-update STD HANK
                m.std_hank = calc_std_hank(
                    m.spdl_speed,
                    m.tpi,
                    m.efficiency
                )

        session.commit()
        st.success("✅ Machine Records Updated Successfully!")
        st.info("Daily Entry will automatically pick up the updated values.")
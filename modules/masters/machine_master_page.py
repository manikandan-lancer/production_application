import streamlit as st
import pandas as pd
from database.connection import get_session
from database.models import Mill, Department, Machine
from sqlalchemy.orm import Session
from modules.calc_engine import calc_std_hank


def machine_master_page():
    st.header("🛠 Machine Master")

    session: Session = next(get_session())

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}

    # -----------------------------------
    # ADD MACHINE
    # -----------------------------------
    with st.form("machine_form"):
        st.subheader("➕ Add Machine")

        colA, colB = st.columns(2)

        with colA:
            mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
            dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])
            machine_name = st.text_input("Machine Name")

        with colB:
            spindles = st.number_input("Spindles", step=1)
            spdl_speed = st.number_input("Speed", step=1.0)
            tpi = st.number_input("TPI", step=0.01)
            efficiency = st.number_input("Efficiency (%)", step=0.01)

        std_hank = calc_std_hank(spdl_speed, tpi, efficiency)
        st.write(f"📘 STD Hank: **{std_hank}**")

        if st.form_submit_button("💾 Save Machine"):
            m = Machine(
                mill_id=mill_id,
                department_id=dept_id,
                machine_name=machine_name,
                spindles=spindles,
                spdl_speed=spdl_speed,
                tpi=tpi,
                efficiency=efficiency,
                std_hank=std_hank
            )
            session.add(m)
            session.commit()
            st.success("✔ Machine Added")

    st.divider()
    st.subheader("📄 Machine List")

    machines = session.query(Machine).all()

    df = pd.DataFrame([
        {
            "id": m.id,
            "Machine": m.machine_name,
            "Mill": mill_map[m.mill_id],
            "Dept": dept_map[m.department_id],
            "Spindles": m.spindles,
            "Speed": float(m.spdl_speed or 0),
            "TPI": float(m.tpi or 0),
            "Efficiency": float(m.efficiency or 0),
            "STD Hank": float(m.std_hank or 0),
        }
        for m in machines
    ])

    edited = st.data_editor(df, use_container_width=True, hide_index=True)

    if st.button("💾 Update Machines"):
        for _, row in edited.iterrows():
            m = session.query(Machine).filter_by(id=row["id"]).first()

            m.spindles = row["Spindles"]
            m.spdl_speed = row["Speed"]
            m.tpi = row["TPI"]
            m.efficiency = row["Efficiency"]
            m.std_hank = calc_std_hank(row["Speed"], row["TPI"], row["Efficiency"])

        session.commit()
        st.success("✔ Updated Machines")
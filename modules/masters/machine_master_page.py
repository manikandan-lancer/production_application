import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import exists

from database.connection import get_session
from database.models import DailyProduction, Mill, Department, Machine, CountMaster
from utils.calc_engine import safe_float, calc_std_hank


# -------------------------------------------------------
# RESET CALLBACK
# -------------------------------------------------------
def reset_machine_form():
    st.session_state.mm_name = ""
    st.session_state.mm_spindles = 0
    st.session_state.mm_speed = 0.0
    st.session_state.mm_tpi = 0.0
    st.session_state.mm_count = None


# -------------------------------------------------------
# MACHINE MASTER PAGE
# -------------------------------------------------------
def machine_master_page():

    # ---------- COMPACT UI ----------
    st.markdown("""
    <style>
    .block-container { padding-top: 0.6rem; padding-bottom: 0.3rem; }
    h1, h2, h3 { margin: 0.4rem 0; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🛠 Machine Master")

    session: Session = next(get_session())

    # ---------- LOAD MASTERS ----------
    mills = session.query(Mill).all()
    depts = session.query(Department).all()
    counts = session.query(CountMaster).all()

    mill_map = {m.id: m.mill_name for m in mills}
    dept_map = {d.id: d.department_name for d in depts}
    count_map = {c.id: c.count_name for c in counts}

    # -------------------------------------------------------
    # 🔍 CONTEXT FILTER (IMPORTANT FIX)
    # -------------------------------------------------------
    st.subheader("🔍 Select Context")

    f1, f2 = st.columns(2)

    with f1:
        filter_mill_id = st.selectbox(
            "Mill",
            mill_map.keys(),
            format_func=lambda x: mill_map[x],
            key="mm_mill_filter"
        )

    with f2:
        filter_dept_id = st.selectbox(
            "Department",
            dept_map.keys(),
            format_func=lambda x: dept_map[x],
            key="mm_dept_filter"
        )

    st.divider()

    # -------------------------------------------------------
    # ADD MACHINE FORM
    # -------------------------------------------------------
    st.subheader("➕ Add New Machine")

    with st.form("machine_add_form"):

        c1, c2 = st.columns(2)

        with c1:
            st.text_input("Mill", mill_map[filter_mill_id], disabled=True)
            st.text_input("Department", dept_map[filter_dept_id], disabled=True)
            machine_name = st.text_input("Machine Name", key="mm_name")

        with c2:
            spindles = st.number_input("No. of Spindles", min_value=0, step=1, key="mm_spindles")
            spdl_speed = st.number_input("Spindle Speed", min_value=0.0, step=1.0, key="mm_speed")
            tpi = st.number_input("TPI", min_value=0.0, step=0.01, key="mm_tpi")
            allocated_count_id = st.selectbox(
                "Allocated Count",
                [None] + list(count_map.keys()),
                format_func=lambda x: "" if x is None else count_map[x],
                key="mm_count"
            )

        std_eff = safe_float(
            session.get(CountMaster, allocated_count_id).std_hank_eff
        ) if allocated_count_id else 0

        st.caption(f"📘 STD Hank Preview: {calc_std_hank(spdl_speed, tpi, std_eff)}")

        b1, b2 = st.columns(2)
        save = b1.form_submit_button("💾 Save")
        b2.form_submit_button("🔄 Reset", on_click=reset_machine_form)

    # ---------- SAVE ----------
    if save:
        name_clean = machine_name.strip().upper()

        if not name_clean:
            st.error("Machine Name cannot be empty.")
            return

        exists_machine = session.query(Machine).filter(
            Machine.machine_name == name_clean,
            Machine.mill_id == filter_mill_id,
            Machine.department_id == filter_dept_id,
            Machine.is_active == True
        ).first()

        if exists_machine:
            st.error("❌ Duplicate machine for same mill & department.")
            return

        session.add(Machine(
            mill_id=filter_mill_id,
            department_id=filter_dept_id,
            machine_name=name_clean,
            spindles=spindles,
            spdl_speed=spdl_speed,
            tpi=tpi,
            allocated_count_id=allocated_count_id,
            is_active=True
        ))
        session.commit()
        st.success("✔ Machine Added Successfully")
        reset_machine_form()
        st.rerun()

    # -------------------------------------------------------
    # EXISTING MACHINES
    # -------------------------------------------------------
    st.divider()
    st.subheader("📄 Existing Machines")

    machines = (
        session.query(Machine)
        .filter(
            Machine.is_active == True,
            Machine.mill_id == filter_mill_id,
            Machine.department_id == filter_dept_id
        )
        .order_by(Machine.machine_name)
        .all()
    )

    rows = []
    for m in machines:
        c = session.get(CountMaster, m.allocated_count_id)
        used = session.query(exists().where(DailyProduction.machine_id == m.id)).scalar()

        rows.append({
            "ID": m.id,
            "Machine Name": m.machine_name,
            "Spindles": m.spindles,
            "Allocated Count": m.allocated_count_id,
            "Speed": float(m.spdl_speed or 0),
            "TPI": float(m.tpi or 0),
            "STD Hank": calc_std_hank(
                m.spdl_speed,
                m.tpi,
                safe_float(c.std_hank_eff) if c else 0
            ),
            "Status": "🔒 Used" if used else "🟢 Free",
            "Delete": False,
        })

    editor = st.data_editor(
        pd.DataFrame(rows),
        use_container_width=True,
        height=520,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn(disabled=True),
            "Machine Name": st.column_config.TextColumn(),
            "Allocated Count": st.column_config.SelectboxColumn(
                options=list(count_map.keys()),
                format_func=lambda x: count_map.get(x, "")
            ),
            "STD Hank": st.column_config.NumberColumn(disabled=True),
            "Status": st.column_config.TextColumn(disabled=True),
            "Delete": st.column_config.CheckboxColumn(
                help="Only 🟢 Free machines can be deleted"
            ),
        }
    )

    # -------------------------------------------------------
    # UPDATE / DELETE
    # -------------------------------------------------------
    if st.button("💾 Update Machine Records"):
        for _, r in editor.iterrows():
            m = session.get(Machine, r["ID"])
            if not m:
                continue

            if r["Delete"] and r["Status"] == "🟢 Free":
                m.is_active = False
            else:
                m.machine_name = r["Machine Name"].strip().upper()
                m.spindles = safe_float(r["Spindles"])
                m.spdl_speed = safe_float(r["Speed"])
                m.tpi = safe_float(r["TPI"])
                m.allocated_count_id = r["Allocated Count"]

        session.commit()
        st.success("✔ Machine Master Updated")
        st.info("Daily Entry & Dashboard updated automatically.")
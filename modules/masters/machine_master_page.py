import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import Mill, Department, Machine, CountMaster
from utils.calc_engine import safe_float, calc_std_hank


# -------------------------------------------------------
# MACHINE MASTER PAGE (FINAL UPDATED VERSION)
# -------------------------------------------------------
def machine_master_page():
    st.title("🛠 Machine Master")

    session: Session = next(get_session())

    st.info("""
    Define **Machine Constants** for each Mill & Department.

    **Rules:**
    - Spindles, Speed, TPI are fixed master values.
    - Efficiency is no longer entered here.
    - **STD Hank auto-calculates using Count Master:**

      `STD = (Speed / TPI) × 0.01587394 × (Std Hank Efficiency / 100)`
    """)

    # -------------------------------------------------------
    # LOAD MASTERS
    # -------------------------------------------------------
    mills = session.query(Mill).all()
    depts = session.query(Department).all()
    counts = session.query(CountMaster).all()

    mill_map = {m.id: m.mill_name for m in mills}
    dept_map = {d.id: d.department_name for d in depts}
    count_map = {c.id: c.count_name for c in counts}

    # -------------------------------------------------------
    # ADD NEW MACHINE
    # -------------------------------------------------------
    st.subheader("➕ Add New Machine")

    with st.form("machine_add_form"):
        c1, c2 = st.columns(2)

        with c1:
            mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
            dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])
            machine_name = st.text_input("Machine Name (e.g., A01, B05)")

        with c2:
            spindles = st.number_input("No. of Spindles", min_value=0, step=1)
            spdl_speed = st.number_input("Spindle Speed", min_value=0.0, step=1.0)
            tpi = st.number_input("TPI", min_value=0.0, step=0.01)

            allocated_count_id = st.selectbox(
                "Allocated Count",
                [None] + list(count_map.keys()),
                format_func=lambda x: "" if x is None else count_map[x],
            )

        # ---- STD HANK PREVIEW ----
        std_eff = 0
        if allocated_count_id:
            cobj = session.query(CountMaster).filter_by(id=allocated_count_id).first()
            std_eff = safe_float(cobj.std_hank_eff)

        std_preview = calc_std_hank(spdl_speed, tpi, std_eff)
        st.write(f"📘 **STD Hank Preview:** `{std_preview}`")

        submit = st.form_submit_button("💾 Save Machine")

        if submit:
            if not machine_name.strip():
                st.error("Machine Name cannot be empty.")
                return

            new_m = Machine(
                mill_id=mill_id,
                department_id=dept_id,
                machine_name=machine_name.strip(),
                spindles=spindles,
                spdl_speed=spdl_speed,
                tpi=tpi,
                allocated_count_id=allocated_count_id,
            )

            # STD Hank is stored at daily entry time; we DO NOT store it in Machine table now.
            session.add(new_m)
            session.commit()

            st.success("✔ Machine Added Successfully")

    st.divider()

    # -------------------------------------------------------
    # EXISTING MACHINE GRID
    # -------------------------------------------------------
    st.subheader("📄 Existing Machines")

    machines = (
        session.query(Machine)
        .order_by(Machine.mill_id, Machine.department_id, Machine.machine_name)
        .all()
    )

    if not machines:
        st.warning("No machines found.")
        return

    rows = []

    for m in machines:
        c = session.query(CountMaster).filter_by(id=m.allocated_count_id).first()
        std_eff = safe_float(c.std_hank_eff) if c else 0

        std_hank_calc = calc_std_hank(
            safe_float(m.spdl_speed),
            safe_float(m.tpi),
            std_eff,
        )

        rows.append({
            "ID": m.id,
            "Mill": mill_map[m.mill_id],
            "Department": dept_map[m.department_id],
            "Machine Name": m.machine_name,
            "Spindles": m.spindles,
            "Speed": float(m.spdl_speed or 0),
            "TPI": float(m.tpi or 0),
            "Allocated Count": m.allocated_count_id,
            "Count Name": c.count_name if c else "",
            "STD Hank (Auto)": std_hank_calc,
        })

    df = pd.DataFrame(rows)

    editor = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ID": st.column_config.NumberColumn(disabled=True),
            "Mill": st.column_config.TextColumn(disabled=True),
            "Department": st.column_config.TextColumn(disabled=True),
            "Count Name": st.column_config.TextColumn(disabled=True),
            "STD Hank (Auto)": st.column_config.NumberColumn(disabled=True),
        },
    )

    # -------------------------------------------------------
    # SAVE TABLE UPDATES
    # -------------------------------------------------------
    if st.button("💾 Update Machine Records"):

        for _, row in editor.iterrows():
            m = session.query(Machine).filter_by(id=row["ID"]).first()

            if m:
                m.spindles = safe_float(row["Spindles"])
                m.spdl_speed = safe_float(row["Speed"])
                m.tpi = safe_float(row["TPI"])
                m.allocated_count_id = row["Allocated Count"]

        session.commit()
        st.success("✔ Machine Master Updated Successfully")

        st.info("Daily Entry will automatically reflect updated machine constants.")
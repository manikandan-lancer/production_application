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
    - **STD Hank auto-calculates using Count Master efficiency**
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
            machine_name = st.text_input("Machine Name")

        with c2:
            spindles = st.number_input("No. of Spindles", min_value=0, step=1)
            spdl_speed = st.number_input("Spindle Speed", min_value=0.0, step=1.0)
            tpi = st.number_input("TPI", min_value=0.0, step=0.01)

            allocated_count_id = st.selectbox(
                "Allocated Count",
                [None] + list(count_map.keys()),
                format_func=lambda x: "" if x is None else count_map[x],
            )

        std_eff = 0
        if allocated_count_id:
            cobj = session.get(CountMaster, allocated_count_id)
            std_eff = safe_float(cobj.std_hank_eff)

        std_preview = calc_std_hank(spdl_speed, tpi, std_eff)
        st.write(f"📘 **STD Hank Preview:** `{std_preview}`")

        if st.form_submit_button("💾 Save Machine"):
            if not machine_name.strip():
                st.error("Machine Name cannot be empty.")
                return

            session.add(Machine(
                mill_id=mill_id,
                department_id=dept_id,
                machine_name=machine_name.strip(),
                spindles=spindles,
                spdl_speed=spdl_speed,
                tpi=tpi,
                allocated_count_id=allocated_count_id,
            ))
            session.commit()
            st.success("✔ Machine Added Successfully")

    st.divider()

    # -------------------------------------------------------
    # EXISTING MACHINES
    # -------------------------------------------------------
    st.subheader("📄 Existing Machines")

    # ----------------------------------
    # FILTERS (NEW)
    # ----------------------------------
    fcol1, fcol2 = st.columns(2)

    with fcol1:
        filter_mill_id = st.selectbox(
            "Filter by Mill",
            [None] + list(mill_map.keys()),
            format_func=lambda x: "All Mills" if x is None else mill_map[x],
            key="machine_filter_mill"
        )

    with fcol2:
        filter_dept_id = st.selectbox(
            "Filter by Department",
            [None] + list(dept_map.keys()),
            format_func=lambda x: "All Departments" if x is None else dept_map[x],
            key="machine_filter_dept"
        )

    st.divider()

    q = session.query(Machine)

    if filter_mill_id:
        q = q.filter(Machine.mill_id == filter_mill_id)

    if filter_dept_id:
        q = q.filter(Machine.department_id == filter_dept_id)

    machines = (
        q.order_by(
            Machine.mill_id,
            Machine.department_id,
            Machine.machine_name
        ).all()
    )


    rows = []
    for m in machines:
        c = session.get(CountMaster, m.allocated_count_id)
        std_eff = safe_float(c.std_hank_eff) if c else 0

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
            "STD Hank (Auto)": calc_std_hank(m.spdl_speed, m.tpi, std_eff),
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
            "Machine Name": st.column_config.TextColumn(disabled=True),

            # 🔽 THIS IS THE KEY FIX
            "Allocated Count": st.column_config.SelectboxColumn(
                "Allocated Count",
                options=list(count_map.keys()),
                format_func=lambda x: count_map.get(x, ""),
                help="Changing count will use Std Hank Efficiency from Count Master"
            ),

            "Count Name": st.column_config.TextColumn(
                disabled=True,
                help="Derived from Count Master"
            ),

            "STD Hank (Auto)": st.column_config.NumberColumn(
                disabled=True,
                help="Auto-calculated using Speed, TPI & Count efficiency"
            ),
        },
    )

    # -------------------------------------------------------
    # 🔁 LIVE STD HANK RECALC (CRITICAL ADDITION)
    # -------------------------------------------------------
    for i, r in editor.iterrows():
        count_id = r["Allocated Count"]
        count_obj = session.get(CountMaster, count_id) if count_id else None
        std_eff = safe_float(count_obj.std_hank_eff) if count_obj else 0

        editor.at[i, "STD Hank (Auto)"] = calc_std_hank(
            safe_float(r["Speed"]),
            safe_float(r["TPI"]),
            std_eff
        )

    # -------------------------------------------------------
    # SAVE UPDATES
    # -------------------------------------------------------
    if st.button("💾 Update Machine Records"):
        for _, r in editor.iterrows():
            m = session.get(Machine, r["ID"])
            if m:
                m.spindles = safe_float(r["Spindles"])
                m.spdl_speed = safe_float(r["Speed"])
                m.tpi = safe_float(r["TPI"])
                m.allocated_count_id = r["Allocated Count"]

        session.commit()
        st.success("✔ Machine Master Updated Successfully")
        st.info("Daily Entry will reflect updated machine values")
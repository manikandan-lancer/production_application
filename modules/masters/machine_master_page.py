import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import exists

from database.connection import get_session
from database.models import DailyProduction
from database.models import Mill, Department, Machine, CountMaster
from utils.calc_engine import safe_float, calc_std_hank


# -------------------------------------------------------
# MACHINE MASTER PAGE — FINAL
# -------------------------------------------------------
def machine_master_page():

    # ---------- UI COMPACT STYLING ----------
    st.markdown("""
    <style>
    .block-container { padding-top: 0.6rem; padding-bottom: 0.3rem; }
    h1, h2, h3 { margin: 0.4rem 0; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🛠 Machine Master")

    session: Session = next(get_session())

    # -------------------------------------------------------
    # SESSION STATE (RESET SUPPORT)
    # -------------------------------------------------------
    for k, v in {
        "mm_name": "",
        "mm_spindles": 0,
        "mm_speed": 0.0,
        "mm_tpi": 0.0,
    }.items():
        st.session_state.setdefault(k, v)

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
            mill_id = st.selectbox(
                "Mill", mill_map.keys(),
                format_func=lambda x: mill_map[x],
                key="mm_mill"
            )
            dept_id = st.selectbox(
                "Department", dept_map.keys(),
                format_func=lambda x: dept_map[x],
                key="mm_dept"
            )
            machine_name = st.text_input("Machine Name", key="mm_name")

        with c2:
            spindles = st.number_input(
                "No. of Spindles", min_value=0, step=1, key="mm_spindles"
            )
            spdl_speed = st.number_input(
                "Spindle Speed", min_value=0.0, step=1.0, key="mm_speed"
            )
            tpi = st.number_input(
                "TPI", min_value=0.0, step=0.01, key="mm_tpi"
            )
            allocated_count_id = st.selectbox(
                "Allocated Count",
                [None] + list(count_map.keys()),
                format_func=lambda x: "" if x is None else count_map[x],
            )

        # STD HANK PREVIEW
        std_eff = 0
        if allocated_count_id:
            cobj = session.get(CountMaster, allocated_count_id)
            std_eff = safe_float(cobj.std_hank_eff)

        st.write(
            f"📘 **STD Hank Preview:** `{calc_std_hank(spdl_speed, tpi, std_eff)}`"
        )

        colA, colB = st.columns(2)
        save = colA.form_submit_button("💾 Save")
        reset = colB.form_submit_button("🔄 Reset")

    # ---------- RESET ----------
    if reset:
        st.session_state.mm_name = ""
        st.session_state.mm_spindles = 0
        st.session_state.mm_speed = 0.0
        st.session_state.mm_tpi = 0.0
        st.success("Form reset")
        st.rerun()

    # ---------- SAVE ----------
    if save:
        name_clean = machine_name.strip().upper()

        if not name_clean:
            st.error("Machine Name cannot be empty.")
            return

        duplicate = session.query(Machine).filter(
            Machine.machine_name == name_clean,
            Machine.mill_id == mill_id,
            Machine.department_id == dept_id,
            Machine.is_active == True
        ).first()

        if duplicate:
            st.error(
                f"❌ Machine '{name_clean}' already exists in "
                f"{mill_map[mill_id]} / {dept_map[dept_id]}"
            )
            return

        session.add(Machine(
            mill_id=mill_id,
            department_id=dept_id,
            machine_name=name_clean,
            spindles=spindles,
            spdl_speed=spdl_speed,
            tpi=tpi,
            allocated_count_id=allocated_count_id,
            is_active=True
        ))
        session.commit()
        st.success("✔ Machine Added Successfully")
        st.rerun()

    st.divider()

    # -------------------------------------------------------
    # EXISTING MACHINES
    # -------------------------------------------------------
    st.subheader("📄 Existing Machines")

    f1, f2 = st.columns(2)

    with f1:
        filter_mill_id = st.selectbox(
            "Mill",
            [None] + list(mill_map.keys()),
            format_func=lambda x: "All Mills" if x is None else mill_map[x]
        )

    with f2:
        filter_dept_id = st.selectbox(
            "Department",
            [None] + list(dept_map.keys()),
            format_func=lambda x: "All Departments" if x is None else dept_map[x]
        )

    q = session.query(Machine).filter(Machine.is_active == True)

    if filter_mill_id:
        q = q.filter(Machine.mill_id == filter_mill_id)
    if filter_dept_id:
        q = q.filter(Machine.department_id == filter_dept_id)

    machines = q.order_by(
        Machine.mill_id,
        Machine.department_id,
        Machine.machine_name
    ).all()

    rows = []
    for m in machines:
        c = session.get(CountMaster, m.allocated_count_id)
        std_eff = safe_float(c.std_hank_eff) if c else 0

        used = session.query(
            exists().where(DailyProduction.machine_id == m.id)
        ).scalar()

        rows.append({
            "ID": m.id,
            "Mill": mill_map[m.mill_id],
            "Department": dept_map[m.department_id],
            "Machine Name": m.machine_name,
            "Spindles": m.spindles,
            "Allocated Count": m.allocated_count_id,
            "Speed": float(m.spdl_speed or 0),
            "TPI": float(m.tpi or 0),
            "STD Hank": calc_std_hank(m.spdl_speed, m.tpi, std_eff),
            "Status": "🔒 Used" if used else "🟢 Free",
            "Delete": False,
        })

    df = pd.DataFrame(rows)

    editor = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        height=520,
        column_config={
            "ID": st.column_config.NumberColumn(disabled=True),
            "Mill": st.column_config.TextColumn(disabled=True),
            "Department": st.column_config.TextColumn(disabled=True),
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
        },
    )

    # -------------------------------------------------------
    # SAVE UPDATES
    # -------------------------------------------------------
    if st.button("💾 Update Machine Records"):
        blocked, deleted, updated = [], [], 0

        for _, r in editor.iterrows():
            m = session.get(Machine, r["ID"])
            if not m:
                continue

            if r["Delete"]:
                used = session.query(DailyProduction).filter(
                    DailyProduction.machine_id == m.id
                ).first()

                if used:
                    blocked.append(m.machine_name)
                else:
                    m.is_active = False
                    deleted.append(m.machine_name)
                continue

            m.machine_name = r["Machine Name"].strip().upper()
            m.spindles = safe_float(r["Spindles"])
            m.spdl_speed = safe_float(r["Speed"])
            m.tpi = safe_float(r["TPI"])
            m.allocated_count_id = r["Allocated Count"]
            updated += 1

        session.commit()

        if deleted:
            st.success(f"🗑️ Deleted: {', '.join(deleted)}")
        if blocked:
            st.warning("⚠ In use: " + ", ".join(blocked))
        if updated:
            st.success(f"✔ Updated {updated} machine(s)")
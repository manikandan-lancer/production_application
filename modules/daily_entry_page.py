import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    CountMaster, DailyProduction
)

from utils.calc_engine import (
    safe_float,
    calc_std_hank,
    calc_worked_spindles,
    calc_target_kgs,
    calc_actual_prdn,
    calc_waste_percent,
    calc_prod_kgs,
    calc_std_gps,
    calc_actual_gps,
    calc_diff_gps,
    calc_total_loss,
    calc_40s_conv_gps
)

# ----------------------------------------------------------
# DAILY ENTRY PAGE
# ----------------------------------------------------------
def daily_entry_page():

    st.markdown("""
    <style>
    .block-container { padding-top: 0.6rem; padding-bottom: 0.3rem; }

    /* Sticky header */
    div[data-testid="stDataEditor"] thead th {
        position: sticky;
        top: 0;
        background: #f9fafb;
        z-index: 4;
    }

    /* ✅ Freeze FIRST column (Machine Name) */
    div[data-testid="stDataEditor"] tbody tr td:first-of-type,
    div[data-testid="stDataEditor"] thead tr th:first-of-type {
        position: sticky;
        left: 0;
        background: white;
        z-index: 3;
        font-weight: 600;
        border-right: 1px solid #e5e7eb;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📘 Daily Production Entry")
    session: Session = next(get_session())

    # ---------------- FILTERS ----------------
    c1, c2, c3, c4 = st.columns(4)
    date = c1.date_input("Date")

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = c2.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = c3.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = c4.selectbox("Shift", shift_map.keys(), format_func=lambda x: shift_map[x])

    # ---------------- DUPLICATE CHECK ----------------
    existing = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id
    ).first()

    # ---------------- LOAD MACHINES ----------------
    machines = session.query(Machine).filter(
        Machine.is_active == True,
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name).all()

    if not machines:
        st.warning("No machines found.")
        return

    rows = []

    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id,
    ).all()

    if saved:
        for r in saved:
            machine = session.get(Machine, r.machine_id)
            count = session.get(CountMaster, r.count_id)

            rows.append({
                "machine_id": r.machine_id,
                "machine_name": machine.machine_name if machine else "",
                "spindles": r.spindles,
                "count_id": r.count_id,
                "count_name": count.count_name if count else "",
                "speed": r.spdl_speed,
                "tpi": r.tpi,
                "std_hank": r.std_hank,
                "conversion_factor": r.conversion_factor,
                "act_hank": r.act_hank,
                "pne_bondas": r.pne_bondas,
                "worked_spindles": r.worked_spindles,
                "target_kgs": r.target_kgs,
                "prod_kgs": r.prod_kgs,
                "actual_prdn": r.actual_prdn,
                "waste_percent": r.waste_percent,
                "std_gps": r.std_gps,
                "actual_gps": r.actual_gps,
                "diff_gps": r.diff_gps,
                "woh": r.woh,
                "mw": r.mw,
                "clg_lc": r.clg_lc,
                "er": r.er,
                "la_pf": r.la_pf,
                "bss": r.bss,
                "lap": r.lap,
                "dd": r.dd,
                "total_loss": r.total_loss,
                "stop_min": r.stop_min,
                "remarks": r.remarks or ""
            })
    else:
        for m in machines:
            cnt = session.get(CountMaster, m.allocated_count_id)
            std_eff = safe_float(cnt.std_hank_eff) if cnt else 0
            std_hank = calc_std_hank(m.spdl_speed, m.tpi, std_eff)

            target = calc_target_kgs(
                safe_float(cnt.conversion_factor if cnt else 0),
                m.spindles,
                std_hank
            )

            rows.append({
                "machine_id": m.id,
                "machine_name": m.machine_name,
                "spindles": m.spindles,
                "count_id": m.allocated_count_id,
                "count_name": cnt.count_name if cnt else "",
                "speed": m.spdl_speed,
                "tpi": m.tpi,
                "std_hank": std_hank,
                "conversion_factor": safe_float(cnt.conversion_factor) if cnt else 0,
                "act_hank": 0.0,
                "pne_bondas": 0.0,
                "worked_spindles": m.spindles,
                "target_kgs": target,
                "prod_kgs": 0.0,
                "actual_prdn": 0.0,
                "waste_percent": 0.0,
                "std_gps": 0.0,
                "actual_gps": 0.0,
                "diff_gps": 0.0,
                "woh": 0.0,
                "mw": 0.0,
                "clg_lc": 0.0,
                "er": 0.0,
                "la_pf": 0.0,
                "bss": 0.0,
                "lap": 0.0,
                "dd": 0.0,
                "total_loss": 0.0,
                "stop_min": 0.0,
                "remarks": ""
            })

    df = pd.DataFrame(rows)
    df = df.set_index("machine_name")

    edited = st.data_editor(
        df,
        disabled=[
            "machine_name","count_name","speed","tpi","spindles","std_hank","worked_spindles",
            "target_kgs","actual_prdn","waste_percent",
            "std_gps","actual_gps","diff_gps","total_loss","stop_min"
        ],
        column_order=[c for c in df.columns if c not in ["count_id","conversion_factor"]],
        use_container_width=True,
        height=650
    )

    # ---------------- LIVE CALCULATIONS (UNCHANGED) ----------------
    for i, r in edited.iterrows():
        total_loss = calc_total_loss(
            r["woh"], r["mw"], r["clg_lc"], r["er"],
            r["la_pf"], r["bss"], r["lap"], r["dd"]
        )

        edited.at[i, "total_loss"] = total_loss
        edited.at[i, "stop_min"] = total_loss

        worked = calc_worked_spindles(r["spindles"], total_loss)
        prod = calc_prod_kgs(r["conversion_factor"], r["spindles"], r["act_hank"])
        actual = calc_actual_prdn(prod, r["pne_bondas"])

        edited.at[i, "worked_spindles"] = worked
        edited.at[i, "prod_kgs"] = prod
        edited.at[i, "actual_prdn"] = actual
        edited.at[i, "waste_percent"] = calc_waste_percent(r["pne_bondas"], prod)

        std_gps = calc_std_gps(r["target_kgs"], r["spindles"])
        actual_gps = calc_actual_gps(actual, worked)

        count_obj = session.get(CountMaster, r["count_id"]) if r["count_id"] else None
        conv_40s = calc_40s_conv_gps(
            safe_float(count_obj.conv_40s_factor) if count_obj else 0,
            actual_gps
        )

        edited.at[i, "std_gps"] = std_gps
        edited.at[i, "actual_gps"] = actual_gps
        edited.at[i, "diff_gps"] = calc_diff_gps(std_gps, actual_gps)
        edited.at[i, "conv_40s_gps"] = conv_40s

    # ---------------- SAVE ----------------
    if st.button("💾 Save Daily Production"):

        # ❗ Prevent duplicate entry
        exists_entry = session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).first()

        if exists_entry:
            st.error("❌ Data already exists for this Date / Mill / Department / Shift")
            return

        for _, r in edited.iterrows():
            session.add(
                DailyProduction(
                    date=date,
                    mill_id=mill_id,
                    department_id=dept_id,
                    shift_id=shift_id,

                    machine_id=r["machine_id"],
                    count_id=r["count_id"],

                    spindles=r["spindles"],
                    spdl_speed=r["speed"],
                    tpi=r["tpi"],
                    std_hank=r["std_hank"],
                    conversion_factor=r["conversion_factor"],

                    act_hank=r["act_hank"],
                    pne_bondas=r["pne_bondas"],

                    worked_spindles=r["worked_spindles"],
                    target_kgs=r["target_kgs"],
                    prod_kgs=r["prod_kgs"],
                    actual_prdn=r["actual_prdn"],
                    waste_percent=r["waste_percent"],

                    std_gps=r["std_gps"],
                    actual_gps=r["actual_gps"],
                    diff_gps=r["diff_gps"],
                    conv_40s_gps=r.get("conv_40s_gps", 0),

                    woh=r["woh"],
                    mw=r["mw"],
                    clg_lc=r["clg_lc"],
                    er=r["er"],
                    la_pf=r["la_pf"],
                    bss=r["bss"],
                    lap=r["lap"],
                    dd=r["dd"],

                    total_loss=r["total_loss"],
                    stop_min=r["stop_min"],
                    remarks=r["remarks"]
                )
            )

        session.commit()
        st.success("✅ Daily Production Saved Successfully")

        # reset table to master-derived values
        st.rerun()

    st.divider() 
    
    st.subheader("📌 Shift Production Summary") 
    c1, c2, c3 = st.columns(3) 
    with c1: 
        st.metric("🎯 Total Target Kgs", round(edited["target_kgs"].sum(), 2)) 
        st.metric("⚙️ Total Production Kgs", round(edited["prod_kgs"].sum(), 2)) 

    with c2: 
        st.metric("📦 Actual Production", round(edited["actual_prdn"].sum(), 2)) 
        st.metric("🧵 Total Pne Bondas", round(edited["pne_bondas"].sum(), 2)) 
    
    with c3: 
        st.metric("⏱️ Total Stop Minutes", round(edited["stop_min"].sum(), 2)) 
        st.metric("♻️ Avg Waste %", round( edited["waste_percent"].mean(), 2 ))
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
# SAFE VALUE
# ----------------------------------------------------------
def nz(v):
    return 0 if v is None or pd.isna(v) else v


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

    /* Freeze Machine Name */
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

    # ---------------- LOAD MACHINES ----------------
    machines = session.query(Machine).filter(
        Machine.is_active == True,
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name).all()

    if not machines:
        st.warning("No machines found.")
        return

    # ---------------- LOAD EXISTING ----------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id,
    ).all()

    rows = []

    if saved:
        for r in saved:
            m = session.get(Machine, r.machine_id)
            c = session.get(CountMaster, r.count_id)

            rows.append({
                "machine_id": r.machine_id,
                "machine_name": m.machine_name,
                "spindles": r.spindles,
                "count_id": r.count_id,
                "count_name": c.count_name if c else "",
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

    df = pd.DataFrame(rows).set_index("machine_name")
    HIDDEN_COLS = ["machine_id", "count_id", "conversion_factor"]

    edited = st.data_editor(
        df,
        disabled=[
            "count_name","speed","tpi","spindles","std_hank",
            "target_kgs","std_gps","actual_gps","diff_gps",
            "worked_spindles","prod_kgs","actual_prdn",
            "waste_percent","total_loss","stop_min"
        ],
        column_order=[c for c in df.columns if c not in HIDDEN_COLS],
        use_container_width=True,
        height=650
    )

    # ---------------- LIVE CALCULATIONS ----------------
    for i, r in edited.iterrows():

        total_loss = calc_total_loss(
            r["woh"], r["mw"], r["clg_lc"], r["er"],
            r["la_pf"], r["bss"], r["lap"], r["dd"]
        )

        worked = calc_worked_spindles(r["spindles"], total_loss)
        prod = calc_prod_kgs(r["conversion_factor"], r["spindles"], r["act_hank"])
        actual = calc_actual_prdn(prod, r["pne_bondas"])

        std_gps = (
            (nz(r["target_kgs"]) / nz(r["spindles"])) * 1000
            if nz(r["spindles"]) > 0
            else 0
        )
        actual_gps = calc_actual_gps(actual, worked)
        diff = calc_diff_gps(std_gps, actual_gps)

        count_obj = session.get(CountMaster, r["count_id"]) if r["count_id"] else None
        conv_40s = calc_40s_conv_gps(
            safe_float(count_obj.conv_40s_factor) if count_obj else 0,
            actual_gps
        )

        edited.at[i, "total_loss"] = total_loss
        edited.at[i, "stop_min"] = total_loss
        edited.at[i, "worked_spindles"] = worked
        edited.at[i, "prod_kgs"] = prod
        edited.at[i, "actual_prdn"] = actual
        edited.at[i, "waste_percent"] = calc_waste_percent(r["pne_bondas"], prod)
        edited.at[i, "std_gps"] = std_gps
        edited.at[i, "actual_gps"] = actual_gps
        edited.at[i, "diff_gps"] = diff
        edited.at[i, "conv_40s_gps"] = conv_40s

    # ---------------- SAVE (OVERWRITE SHIFT) ----------------
    if st.button("💾 Save Daily Production"):

        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()

        for _, r in edited.iterrows():
            session.add(DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,
                machine_id=r["machine_id"],
                count_id=r["count_id"],
                spindles=nz(r["spindles"]),
                spdl_speed=nz(r["speed"]),
                tpi=nz(r["tpi"]),
                std_hank=nz(r["std_hank"]),
                conversion_factor=nz(r["conversion_factor"]),
                act_hank=nz(r["act_hank"]),
                pne_bondas=nz(r["pne_bondas"]),
                worked_spindles=nz(r["worked_spindles"]),
                target_kgs=nz(r["target_kgs"]),
                prod_kgs=nz(r["prod_kgs"]),
                actual_prdn=nz(r["actual_prdn"]),
                waste_percent=nz(r["waste_percent"]),
                std_gps=nz(r["std_gps"]),
                actual_gps=nz(r["actual_gps"]),
                diff_gps=nz(r["diff_gps"]),
                conv_40s_gps=nz(r.get("conv_40s_gps", 0)),
                woh=nz(r["woh"]),
                mw=nz(r["mw"]),
                clg_lc=nz(r["clg_lc"]),
                er=nz(r["er"]),
                la_pf=nz(r["la_pf"]),
                bss=nz(r["bss"]),
                lap=nz(r["lap"]),
                dd=nz(r["dd"]),
                total_loss=nz(r["total_loss"]),
                stop_min=nz(r["stop_min"]),
                remarks=r["remarks"]
            ))

        session.commit()

        # ✅ RESET ENTRY FIELDS AFTER SAVE
                # ✅ RESET ENTRY + CALCULATED FIELDS AFTER SAVE
        RESET_COLS = [
            # Entry fields
            "act_hank", "pne_bondas", "remarks",

            # Production outputs
            "prod_kgs", "actual_prdn", "waste_percent",

            # GPS
            "std_gps", "actual_gps", "diff_gps",

            # Loss & stops
            "woh", "mw", "clg_lc", "er", "la_pf",
            "bss", "lap", "dd", "total_loss", "stop_min",
        ]

        for col in RESET_COLS:
            if col in edited.columns:
                edited[col] = 0

        st.success("✅ Daily Production Saved Successfully")
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
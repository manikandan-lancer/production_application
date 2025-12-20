import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    CountMaster, DailyProduction
)

from utils.calc_engine import *


def nz(v):
    return 0 if v is None or pd.isna(v) else v


def daily_entry_page():

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

    # ---------------- MACHINES ----------------
    machines = session.query(Machine).filter(
        Machine.is_active == True,
        Machine.mill_id == mill_id,
        Machine.department_id == dept_id
    ).order_by(Machine.machine_name).all()

    if not machines:
        st.warning("No machines found.")
        return

    # ---------------- LOAD SAVED ----------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id
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
                "conversion_factor": r.conversion_factor,

                "act_hank": r.act_hank,
                "pne_bondas": r.pne_bondas,

                "woh": r.woh, "mw": r.mw, "clg_lc": r.clg_lc,
                "er": r.er, "la_pf": r.la_pf, "bss": r.bss,
                "lap": r.lap, "dd": r.dd,

                "remarks": r.remarks or ""
            })

    else:
        for m in machines:
            cnt = session.get(CountMaster, m.allocated_count_id)
            std_hank = calc_std_hank(m.spdl_speed, m.tpi, cnt.std_hank_eff if cnt else 0)
            target = calc_target_kgs(cnt.conversion_factor if cnt else 0, m.spindles, std_hank)

            rows.append({
                "machine_id": m.id,
                "machine_name": m.machine_name,
                "spindles": m.spindles,
                "count_id": m.allocated_count_id,
                "count_name": cnt.count_name if cnt else "",
                "speed": m.spdl_speed,
                "tpi": m.tpi,
                "conversion_factor": cnt.conversion_factor if cnt else 0,

                "act_hank": 0.0,
                "pne_bondas": 0.0,

                "woh": 0.0, "mw": 0.0, "clg_lc": 0.0,
                "er": 0.0, "la_pf": 0.0, "bss": 0.0,
                "lap": 0.0, "dd": 0.0,

                "remarks": ""
            })

    input_df = pd.DataFrame(rows).set_index("machine_name")

    edited = st.data_editor(
        input_df,
        disabled=[
            "count_name", "speed", "tpi", "spindles"
        ],
        use_container_width=True,
        height=650
    )

    # ---------------- CALCULATIONS ----------------
    calc_df = edited.copy()

    for i, r in calc_df.iterrows():
        total_loss = calc_total_loss(
            r["woh"], r["mw"], r["clg_lc"], r["er"],
            r["la_pf"], r["bss"], r["lap"], r["dd"]
        )

        worked = calc_worked_spindles(r["spindles"], total_loss)
        prod = calc_prod_kgs(r["conversion_factor"], r["spindles"], r["act_hank"])
        actual = calc_actual_prdn(prod, r["pne_bondas"])

        std_hank = calc_std_hank(r["speed"], r["tpi"], 100)
        target = calc_target_kgs(r["conversion_factor"], r["spindles"], std_hank)

        std_gps = calc_std_gps(target, r["spindles"])
        actual_gps = calc_actual_gps(actual, worked)

        cnt = session.get(CountMaster, r["count_id"])
        conv_40s = calc_40s_conv_gps(cnt.conv_40s_factor if cnt else 0, actual_gps)

        calc_df.at[i, "worked_spindles"] = worked
        calc_df.at[i, "prod_kgs"] = prod
        calc_df.at[i, "actual_prdn"] = actual
        calc_df.at[i, "waste_percent"] = calc_waste_percent(r["pne_bondas"], prod)
        calc_df.at[i, "target_kgs"] = target
        calc_df.at[i, "std_gps"] = std_gps
        calc_df.at[i, "actual_gps"] = actual_gps
        calc_df.at[i, "diff_gps"] = actual_gps - std_gps
        calc_df.at[i, "conv_40s_gps"] = conv_40s
        calc_df.at[i, "total_loss"] = total_loss
        calc_df.at[i, "stop_min"] = total_loss

    # ---------------- SAVE ----------------
    if st.button("💾 Save Daily Production"):

        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id
        ).delete()

        for _, r in calc_df.iterrows():
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
                conv_40s_gps=nz(r["conv_40s_gps"]),
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

        # 🔥 HARD RESET
        for k in list(st.session_state.keys()):
            if k.startswith("data_editor"):
                del st.session_state[k]

        st.success("✅ Daily Production Saved Successfully")
        st.rerun()

    # ---------------- SUMMARY ----------------
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
        st.metric("♻️ Avg Waste %", round(edited["waste_percent"].mean(), 2))
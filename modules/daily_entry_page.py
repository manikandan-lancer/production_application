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
    calc_40s_conv_gps,
    calc_total_loss
)


# ----------------------------------------------------------
# DAILY ENTRY PAGE — FINAL (GPS + 40s CONV + LIVE CALCS)
# ----------------------------------------------------------
def daily_entry_page():
    st.title("📘 Daily Production Entry")

    session: Session = next(get_session())

    # ------------------------------------------------------
    # FILTER PANEL
    # ------------------------------------------------------
    colA, colB, colC, colD = st.columns(4)

    with colA:
        date = st.date_input("Date")

    with colB:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox("Mill", mill_map.keys(),
                               format_func=lambda x: mill_map[x])

    with colC:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_id = st.selectbox("Department", dept_map.keys(),
                               format_func=lambda x: dept_map[x])

    with colD:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_id = st.selectbox("Shift", shift_map.keys(),
                                format_func=lambda x: shift_map[x])

    st.divider()

    # ------------------------------------------------------
    # LOAD MACHINES
    # ------------------------------------------------------
    machines = (
        session.query(Machine)
        .filter(
            Machine.mill_id == mill_id,
            Machine.department_id == dept_id
        )
        .order_by(Machine.machine_name)
        .all()
    )

    if not machines:
        st.warning("No machines found.")
        return

    # ------------------------------------------------------
    # LOAD SAVED DATA
    # ------------------------------------------------------
    saved = session.query(DailyProduction).filter(
        DailyProduction.date == date,
        DailyProduction.mill_id == mill_id,
        DailyProduction.department_id == dept_id,
        DailyProduction.shift_id == shift_id,
    ).all()

    rows = []

    if saved:
        for r in saved:
            machine = session.query(Machine).get(r.machine_id)
            count = session.query(CountMaster).get(r.count_id)

            rows.append({
                "machine_id": r.machine_id,
                "machine_name": machine.machine_name if machine else "",

                "spindles": r.spindles,
                "speed": r.spdl_speed,
                "tpi": r.tpi,
                "std_hank": r.std_hank,

                "count_id": r.count_id,
                "count_name": count.count_name if count else "",
                "conversion_factor": r.conversion_factor,
                "conv_40s_factor": safe_float(count.conv_40s_factor) if count else 0,

                "act_hank": r.act_hank,
                "stop_min": r.stop_min,
                "prod_kgs": r.prod_kgs,
                "pne_bondas": r.pne_bondas,

                "worked_spindles": r.worked_spindles,
                "target_kgs": r.target_kgs,
                "actual_prdn": r.actual_prdn,
                "waste_percent": r.waste_percent,

                "std_gps": r.std_gps,
                "actual_gps": r.actual_gps,
                "diff_gps": r.diff_gps,
                "conv_40s_gps": r.conv_40s_gps,

                "woh": r.woh,
                "mw": r.mw,
                "clg_lc": r.clg_lc,
                "er": r.er,
                "la_pf": r.la_pf,
                "bss": r.bss,
                "lap": r.lap,
                "dd": r.dd,
                "total_loss": r.total_loss,

                "remarks": r.remarks or "",
            })

    else:
        for m in machines:
            cnt = session.query(CountMaster).get(m.allocated_count_id)

            std_eff = safe_float(cnt.std_hank_eff) if cnt else 0
            conv = safe_float(cnt.conversion_factor) if cnt else 0
            conv40 = safe_float(cnt.conv_40s_factor) if cnt else 0

            std_hank = calc_std_hank(m.spdl_speed, m.tpi, std_eff)

            rows.append({
                "machine_id": m.id,
                "machine_name": m.machine_name,

                "spindles": m.spindles,
                "speed": m.spdl_speed,
                "tpi": m.tpi,
                "std_hank": std_hank,

                "count_id": m.allocated_count_id,
                "count_name": cnt.count_name if cnt else "",
                "conversion_factor": conv,
                "conv_40s_factor": conv40,

                "act_hank": 0.0,
                "stop_min": 0.0,
                "prod_kgs": 0.0,
                "pne_bondas": 0.0,

                "worked_spindles": 0.0,
                "target_kgs": 0.0,
                "actual_prdn": 0.0,
                "waste_percent": 0.0,

                "std_gps": 0.0,
                "actual_gps": 0.0,
                "diff_gps": 0.0,
                "conv_40s_gps": 0.0,

                "woh": 0.0,
                "mw": 0.0,
                "clg_lc": 0.0,
                "er": 0.0,
                "la_pf": 0.0,
                "bss": 0.0,
                "lap": 0.0,
                "dd": 0.0,
                "total_loss": 0.0,

                "remarks": "",
            })

    df = pd.DataFrame(rows)

    # ------------------------------------------------------
    # DATA EDITOR (2 DECIMAL DISPLAY ONLY)
    # ------------------------------------------------------
    readonly = [
        "machine_name", "spindles", "speed", "tpi",
        "std_hank", "count_name", "conversion_factor",
        "worked_spindles", "target_kgs",
        "actual_prdn", "waste_percent",
        "std_gps", "actual_gps", "diff_gps", "conv_40s_gps",
        "total_loss"
    ]

    edited = st.data_editor(
        df,
        disabled=readonly,
        use_container_width=True,
        column_config={
            col: st.column_config.NumberColumn(format="%.2f")
            for col in df.columns
            if df[col].dtype != object
        }
    )

    # ------------------------------------------------------
    # LIVE EXCEL-STYLE CALCULATIONS
    # ------------------------------------------------------
    for i, r in edited.iterrows():

        worked = calc_worked_spindles(r["spindles"], r["stop_min"])
        edited.at[i, "worked_spindles"] = worked

        target = calc_target_kgs(r["conversion_factor"], r["spindles"], r["std_hank"])
        edited.at[i, "target_kgs"] = target

        prod = calc_prod_kgs(r["conversion_factor"], r["spindles"], r["act_hank"])
        edited.at[i, "prod_kgs"] = prod

        actual = calc_actual_prdn(prod, r["pne_bondas"])
        edited.at[i, "actual_prdn"] = actual

        waste = calc_waste_percent(r["pne_bondas"], prod)
        edited.at[i, "waste_percent"] = waste

        std_gps = calc_std_gps(target, r["spindles"])
        actual_gps = calc_actual_gps(actual, worked)

        edited.at[i, "std_gps"] = std_gps
        edited.at[i, "actual_gps"] = actual_gps
        edited.at[i, "diff_gps"] = calc_diff_gps(std_gps, actual_gps)
        edited.at[i, "conv_40s_gps"] = calc_40s_conv_gps(r["conv_40s_factor"], actual_gps)

        edited.at[i, "total_loss"] = calc_total_loss(
            r["woh"], r["mw"], r["clg_lc"], r["er"],
            r["la_pf"], r["bss"], r["lap"], r["dd"]
        )

    # ------------------------------------------------------
    # SAVE
    # ------------------------------------------------------
    if st.button("💾 Save Daily Production"):

        session.query(DailyProduction).filter(
            DailyProduction.date == date,
            DailyProduction.mill_id == mill_id,
            DailyProduction.department_id == dept_id,
            DailyProduction.shift_id == shift_id,
        ).delete()

        session.commit()

        for _, r in edited.iterrows():
            dp = DailyProduction(
                date=date,
                mill_id=mill_id,
                department_id=dept_id,
                shift_id=shift_id,

                machine_id=r["machine_id"],
                count_id=r["count_id"],

                # machine snapshot
                spindles=r["spindles"],
                spdl_speed=r["speed"],
                tpi=r["tpi"],
                std_hank=r["std_hank"],
                conversion_factor=r["conversion_factor"],

                # user inputs
                act_hank=r["act_hank"],
                stop_min=r["stop_min"],
                prod_kgs=r["prod_kgs"],
                pne_bondas=r["pne_bondas"],

                # calculated values
                worked_spindles=r["worked_spindles"],
                target_kgs=r["target_kgs"],
                actual_prdn=r["actual_prdn"],
                waste_percent=r["waste_percent"],

                std_gps=r["std_gps"],
                actual_gps=r["actual_gps"],
                diff_gps=r["diff_gps"],
                conv_40s_gps=r["conv_40s_gps"],

                woh=r["woh"],
                mw=r["mw"],
                clg_lc=r["clg_lc"],
                er=r["er"],
                la_pf=r["la_pf"],
                bss=r["bss"],
                lap=r["lap"],
                dd=r["dd"],
                total_loss=r["total_loss"],

                remarks=r["remarks"]
            )

            session.add(dp)

        session.commit()
        st.success("✅ Daily Production Saved Successfully")
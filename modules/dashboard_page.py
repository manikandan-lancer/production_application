import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine,
    Employee, CountMaster, DailyProduction
)

def dashboard_page():
    st.markdown("""
    <style>
    .block-container { padding-top: 0.6rem; padding-bottom: 0.4rem; }
    div[data-testid="stDataFrame"] { overflow-x: auto; }
    div[data-testid="stDataFrame"] thead th {
        position: sticky;
        top: 0;
        background: #f9fafb;
        z-index: 5;
    }
    div[data-testid="stDataFrame"] tbody tr td:first-of-type,
    div[data-testid="stDataFrame"] thead tr th:first-of-type {
        position: sticky;
        left: 0;
        background: white;
        z-index: 6;
        font-weight: 600;
        border-right: 1px solid #e5e7eb;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📊 Production Dashboard")

    session: Session = next(get_session())

    # ---------------- FILTER PANEL ----------------
    col1, col2, col3, col4 = st.columns(4)
    date = col1.date_input("Date", key="dashboard_date")

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = col2.selectbox("Mill", [None] + list(mill_map.keys()),
                             format_func=lambda x: "All" if x is None else mill_map[x])

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = col3.selectbox("Department", [None] + list(dept_map.keys()),
                             format_func=lambda x: "All" if x is None else dept_map[x])

    shifts = session.query(Shift).all()
    shift_map = {s.id: s.shift_name for s in shifts}
    shift_id = col4.selectbox("Shift", [None] + list(shift_map.keys()),
                              format_func=lambda x: "All" if x is None else shift_map[x])

    col5, col6 = st.columns(2)
    employees = session.query(Employee).all()
    emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
    emp_id = col5.selectbox("Employee", [None] + list(emp_map.keys()),
                            format_func=lambda x: "All" if x is None else emp_map[x])

    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}
    count_id = col6.selectbox("Count", [None] + list(count_map.keys()),
                              format_func=lambda x: "All" if x is None else count_map[x])

    st.divider()

    # ---------------- QUERY ----------------
    q = session.query(DailyProduction).filter(DailyProduction.date == date)
    if mill_id: q = q.filter(DailyProduction.mill_id == mill_id)
    if dept_id: q = q.filter(DailyProduction.department_id == dept_id)
    if shift_id: q = q.filter(DailyProduction.shift_id == shift_id)
    if emp_id: q = q.filter(DailyProduction.employee_id == emp_id)
    if count_id: q = q.filter(DailyProduction.count_id == count_id)

    rows = q.all()
    if not rows:
        st.warning("No records found.")
        return

    # ---------------- BUILD DATAFRAME ----------------
    data = []

    for r in rows:
        machine = session.get(Machine, r.machine_id)
        count = session.get(CountMaster, r.count_id)
        emp = session.get(Employee, r.employee_id) if r.employee_id else None
        shift = session.get(Shift, r.shift_id)

        std_gps = (r.target_kgs / r.spindles * 1000) if r.spindles else 0
        actual_gps = r.actual_gps or 0
        diff_gps = actual_gps - std_gps

        data.append({
            "Machine": machine.machine_name if machine else "",
            "Date": r.date,
            "Mill": mill_map.get(r.mill_id),
            "Department": dept_map.get(r.department_id),
            "Shift": shift.shift_name if shift else "",

            "Spindles": r.spindles,
            "Count": count.count_name if count else "",
            "Speed": r.spdl_speed,
            "TPI": r.tpi,
            "Std Hank": r.std_hank,

            "Conversion Factor": r.conversion_factor,
            "40s Conv Factor": getattr(count, "conv_40s_factor", 0),

            "Worked Spindles": r.worked_spindles,
            "Target Kgs": r.target_kgs,
            "Actual Hank": r.act_hank,
            "Stop Min": r.stop_min,
            "Prod Kgs": r.prod_kgs,
            "Pne Bondas": r.pne_bondas,
            "Actual Production": r.actual_prdn,
            "Waste %": r.waste_percent,

            "Std GPS": std_gps,
            "Actual GPS": actual_gps,
            "Diff (+/-)": diff_gps,
            "40s Conv GPS": r.conv_40s_gps,

            "W.O.H": r.woh,
            "MW": r.mw,
            "CLG/LC": r.clg_lc,
            "ER": r.er,
            "LA,PF": r.la_pf,
            "BSS": r.bss,
            "LAP": r.lap,
            "DD": r.dd,
            "Total Loss": r.total_loss,

            "Employee": emp.employee_name if emp else "",
            "Remarks": r.remarks or "",
        })

    df = pd.DataFrame(data)
    HIDDEN_COLS = ["Conversion Factor", "40s Conv Factor"]
    numeric_cols = df.select_dtypes(include=["float", "int"]).columns

    st.dataframe(
        df.style.format({col: "{:.2f}" for col in numeric_cols}),
        column_order=[c for c in df.columns if c not in HIDDEN_COLS],
        use_container_width=True,
        height=650
    )

    # ---------------- DELETE ENTRY (DASHBOARD) ----------------
    st.divider()
    st.subheader("🗑️ Delete Production Entry")

    # Init confirmation state
    if "confirm_dashboard_delete" not in st.session_state:
        st.session_state.confirm_dashboard_delete = False

    # Show delete button only if data exists
    if not df.empty:
        if st.button("🗑️ Delete This Selection", type="secondary"):
            st.session_state.confirm_dashboard_delete = True

    # Confirmation block
    if st.session_state.confirm_dashboard_delete:

        st.warning(
            f"""
            ⚠️ **Confirm Deletion**

            You are about to permanently delete production data for:

            - **Date:** {date}
            - **Mill:** {mill_map.get(mill_id) if mill_id else "All"}
            - **Department:** {dept_map.get(dept_id) if dept_id else "All"}
            - **Shift:** {shift_map.get(shift_id) if shift_id else "All"}

            ❗ This action **cannot be undone**.
            """
        )

        c1, c2 = st.columns(2)

        with c1:
            if st.button("❌ Cancel"):
                st.session_state.confirm_dashboard_delete = False
                st.info("Deletion cancelled.")

        with c2:
            if st.button("✅ Yes, Delete Permanently", type="primary"):

                delete_q = session.query(DailyProduction).filter(
                    DailyProduction.date == date
                )

                if mill_id:
                    delete_q = delete_q.filter(DailyProduction.mill_id == mill_id)
                if dept_id:
                    delete_q = delete_q.filter(DailyProduction.department_id == dept_id)
                if shift_id:
                    delete_q = delete_q.filter(DailyProduction.shift_id == shift_id)
                if emp_id:
                    delete_q = delete_q.filter(DailyProduction.employee_id == emp_id)
                if count_id:
                    delete_q = delete_q.filter(DailyProduction.count_id == count_id)

                deleted_rows = delete_q.delete(synchronize_session=False)
                session.commit()

                st.session_state.confirm_dashboard_delete = False

                st.success(f"✅ Deleted {deleted_rows} production record(s) successfully.")
                st.rerun()


    # ---------------- SUMMARY ----------------
    st.divider()
    st.subheader("📌 Production Summary")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("🎯 Total Target Kgs", round(df["Target Kgs"].sum(), 2))
        st.metric("⚙️ Total Prod Kgs", round(df["Prod Kgs"].sum(), 2))

    with c2:
        st.metric("⏱️ Total Stop Min", round(df["Stop Min"].sum(), 2))
        st.metric("🧵 Total Pne Bondas", round(df["Pne Bondas"].sum(), 2))

    with c3:
        st.metric("📦 Actual Production", round(df["Actual Production"].sum(), 2))

    # ---------------- LOSS SUMMARY ----------------
    st.subheader("📉 Loss Summary")

    loss_cols = ["W.O.H", "MW", "CLG/LC", "ER", "LA,PF", "BSS", "LAP", "DD"]

    loss_df = pd.DataFrame(
        [{"Loss Type": col, "Total": round(df[col].sum(), 2)} for col in loss_cols]
    )

    st.dataframe(loss_df, use_container_width=True)

    st.metric("🔻 Total Loss", round(df["Total Loss"].sum(), 2))

    # ---------------- EXPORT ----------------
    st.download_button(
        "⬇ Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        "dashboard_export.csv",
        "text/csv"
    )
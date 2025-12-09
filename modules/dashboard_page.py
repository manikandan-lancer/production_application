import streamlit as st
import pandas as pd
from database.connection import get_session
from database.models import (
    Mill, Department, Shift, Machine, Employee,
    CountMaster, DailyProduction
)

# ----------------------------------------------------------
# FORMULAS
# ----------------------------------------------------------

def calc_efficiency(actual_hank, std_hank):
    """ Efficiency = (ACT_HANK / STD_HANK) * 100 """
    try:
        if not std_hank or std_hank == 0:
            return 0.0
        return round((float(actual_hank) / float(std_hank)) * 100, 2)
    except:
        return 0.0


def calc_oee(efficiency, run_hours, stop_min):
    """ OEE = Availability × Performance(Efficiency) """
    try:
        if not run_hours or run_hours == 0:
            return 0.0
        availability = (run_hours - (stop_min / 60)) / run_hours
        return round(availability * (efficiency / 100) * 100, 2)
    except:
        return 0.0


# ----------------------------------------------------------
# DASHBOARD PAGE
# ----------------------------------------------------------
def dashboard_page():
    st.title("📊 Production Dashboard")

    session = next(get_session())

    # ------------------------------------------------------
    # FILTER PANEL
    # ------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        date = st.date_input("Date")

    with col2:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox(
            "Mill", [None] + list(mill_map.keys()),
            format_func=lambda x: "All" if x is None else mill_map[x]
        )

    with col3:
        depts = session.query(Department).all()
        dept_map = {d.id: d.department_name for d in depts}
        dept_id = st.selectbox(
            "Department", [None] + list(dept_map.keys()),
            format_func=lambda x: "All" if x is None else dept_map[x]
        )

    with col4:
        shifts = session.query(Shift).all()
        shift_map = {s.id: s.shift_name for s in shifts}
        shift_id = st.selectbox(
            "Shift", [None] + list(shift_map.keys()),
            format_func=lambda x: "All" if x is None else shift_map[x]
        )

    col5, col6 = st.columns(2)

    with col5:
        employees = session.query(Employee).all()
        emp_map = {e.id: f"{e.employee_no} - {e.employee_name}" for e in employees}
        emp_id = st.selectbox(
            "Employee", [None] + list(emp_map.keys()),
            format_func=lambda x: "All" if x is None else emp_map[x]
        )

    with col6:
        counts = session.query(CountMaster).all()
        count_map = {c.id: c.count_name for c in counts}
        count_id = st.selectbox(
            "Count", [None] + list(count_map.keys()),
            format_func=lambda x: "All" if x is None else count_map[x]
        )

    st.divider()

    # ------------------------------------------------------
    # BUILD QUERY
    # ------------------------------------------------------
    query = session.query(DailyProduction).filter(DailyProduction.date == date)

    if mill_id:
        query = query.filter(DailyProduction.mill_id == mill_id)
    if dept_id:
        query = query.filter(DailyProduction.department_id == dept_id)
    if shift_id:
        query = query.filter(DailyProduction.shift_id == shift_id)
    if emp_id:
        query = query.filter(DailyProduction.employee_id == emp_id)
    if count_id:
        query = query.filter(DailyProduction.count_id == count_id)

    records = query.all()

    if not records:
        st.warning("No records found for selected filters.")
        return

    # ------------------------------------------------------
    # BUILD TABLE
    # ------------------------------------------------------
    table = []

    for r in records:

        machine = session.query(Machine).filter_by(id=r.machine_id).first()
        count = session.query(CountMaster).filter_by(id=r.count_id).first()
        emp = session.query(Employee).filter_by(id=r.employee_id).first() if r.employee_id else None
        shift = session.query(Shift).filter_by(id=r.shift_id).first()

        # Machine constants
        spdl_speed = float(machine.spdl_speed or 0)
        tpi = float(machine.tpi or 0)
        std_hank = float(machine.std_hank or 0)

        # Count constants
        actual_count = float(count.actual_count or 0) if count else 0
        eff_base = float(count.eff_base or 0) if count else 0
        conv_factor = float(count.conversion_factor or 0) if count else 0

        # Entry values
        actual_hank = float(r.act_hank or 0)
        efficiency = calc_efficiency(actual_hank, std_hank)
        oee = calc_oee(efficiency, float(r.run_hours or 0), float(r.stop_min or 0))

        # Row data
        table.append({
            "Date": r.date,
            "Mill": mill_map.get(r.mill_id, ""),
            "Dept": dept_map.get(r.department_id, ""),
            "Shift": shift.shift_name if shift else "",
            "Machine": machine.machine_name if machine else "",
            "Count": count.count_name if count else "",

            "Spindle Speed": spdl_speed,
            "TPI": tpi,
            "STD Hank": std_hank,
            "ACT Hank": actual_hank,

            "Actual Count": actual_count,
            "Eff Base (%)": eff_base,
            "Conv Factor": conv_factor,

            "Worked Spindles": float(r.worked_spindles or 0),
            "Stop Min": float(r.stop_min or 0),
            "Run Hours": float(r.run_hours or 0),

            "Prod Kgs": float(r.prod_kgs or 0),
            "Pneumafil": float(r.pne_bondas or 0),
            "Actual Production": float(r.actual_prdn or 0),
            "Waste": float(r.waste or 0),

            "Efficiency (%)": efficiency,
            "OEE (%)": oee,

            "Employee": emp.employee_name if emp else "",
            "Remarks": r.remarks or "",
        })

    df = pd.DataFrame(table)

    # ------------------------------------------------------
    # DISPLAY TABLE
    # ------------------------------------------------------
    st.subheader("📄 Production Records")
    st.dataframe(df, use_container_width=True)

    # ------------------------------------------------------
    # SUMMARY CARDS
    # ------------------------------------------------------
    st.subheader("📌 Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Prod (Kgs)", round(df["Prod Kgs"].sum(), 2))
    col2.metric("Actual Production", round(df["Actual Production"].sum(), 2))
    col3.metric("Total Waste", round(df["Waste"].sum(), 2))
    col4.metric("Avg Efficiency %", round(df["Efficiency (%)"].mean(), 2))
    col5.metric("Avg OEE %", round(df["OEE (%)"].mean(), 2))

    # ------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------
    st.subheader("📥 Export")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        data=csv,
        file_name="dashboard_export.csv",
        mime="text/csv"
    )

    excel = df.to_excel("dashboard_export.xlsx", index=False)

    with open("dashboard_export.xlsx", "rb") as f:
        st.download_button(
            "Download Excel",
            data=f,
            file_name="dashboard_export.xlsx",
            mime="application/vnd.ms-excel"
        )
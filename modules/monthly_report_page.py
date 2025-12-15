import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import extract

from database.connection import get_session
from database.models import (
    Mill, Department, Shift, CountMaster, DailyProduction
)


def monthly_report_page():
    st.title("📅 Monthly Production Report")

    session: Session = next(get_session())

    # -------------------------------
    # FILTER PANEL
    # -------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        year = st.selectbox(
            "Year",
            list(range(2020, 2031)),
            index=list(range(2020, 2031)).index(pd.Timestamp.today().year)
        )

    with col2:
        month = st.selectbox(
            "Month",
            list(range(1, 13)),
            format_func=lambda x: pd.to_datetime(str(x), format="%m").strftime("%B")
        )

    with col3:
        mills = session.query(Mill).all()
        mill_map = {m.id: m.mill_name for m in mills}
        mill_id = st.selectbox(
            "Mill",
            [None] + list(mill_map.keys()),
            format_func=lambda x: "All" if x is None else mill_map[x]
        )

    st.divider()

    # -------------------------------
    # BUILD QUERY
    # -------------------------------
    q = session.query(DailyProduction).filter(
        extract("year", DailyProduction.date) == year,
        extract("month", DailyProduction.date) == month
    )

    if mill_id:
        q = q.filter(DailyProduction.mill_id == mill_id)

    rows = q.all()

    if not rows:
        st.warning("No records found for selected month.")
        return

    # -------------------------------
    # BUILD DATAFRAME
    # -------------------------------
    data = []

    for r in rows:
        data.append({
            "Date": r.date,
            "Target Kgs": r.target_kgs,
            "Prod Kgs": r.prod_kgs,
            "Stop Min": r.stop_min,
            "Pne Bondas": r.pne_bondas,
            "Actual Production": r.actual_prdn,

            "W.O.H": r.woh,
            "MW": r.mw,
            "CLG/LC": r.clg_lc,
            "ER": r.er,
            "LA,PF": r.la_pf,
            "BSS": r.bss,
            "LAP": r.lap,
            "DD": r.dd,
            "Total Loss": r.total_loss,
        })

    df = pd.DataFrame(data)

    # -------------------------------
    # MONTHLY SUMMARY
    # -------------------------------
    st.subheader("📌 Monthly Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🎯 Total Target Kgs", round(df["Target Kgs"].sum(), 2))
        st.metric("⚙️ Total Prod Kgs", round(df["Prod Kgs"].sum(), 2))

    with col2:
        st.metric("⏱️ Total Stop Min", round(df["Stop Min"].sum(), 2))
        st.metric("🧵 Total Pne Bondas", round(df["Pne Bondas"].sum(), 2))

    with col3:
        st.metric("📦 Actual Production", round(df["Actual Production"].sum(), 2))

    # -------------------------------
    # MONTHLY LOSS SUMMARY
    # -------------------------------
    st.subheader("📉 Monthly Loss Summary")

    loss_cols = ["W.O.H", "MW", "CLG/LC", "ER", "LA,PF", "BSS", "LAP", "DD"]

    loss_totals = {
        col: round(df[col].sum(), 2)
        for col in loss_cols
    }

    loss_df = pd.DataFrame(
        [{"Loss Type": k, "Total": v} for k, v in loss_totals.items()]
    )

    st.dataframe(loss_df, use_container_width=True)

    st.metric(
        "🔻 Total Monthly Loss",
        round(df["Total Loss"].sum(), 2)
    )

    # -------------------------------
    # EXPORT
    # -------------------------------
    st.download_button(
        "⬇️ Download Monthly Report (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"monthly_report_{year}_{month}.csv",
        mime="text/csv"
    )

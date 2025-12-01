import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Machine, Shift, DailyProduction
from modules.formulas import calc_efficiency

Session = sessionmaker(bind=engine)

def generate_entries(date):
    session = Session()

    machines = session.query(Machine).all()
    shifts = session.query(Shift).all()

    data = []
    for sh in shifts:
        for m in machines:
            data.append({
                "date": date,
                "shift_id": sh.id,
                "machine_id": m.id,
                "actual": 0,
                "scrap": 0,
                "downtime": 0,
                "target": m.target
            })

    return pd.DataFrame(data)


def daily_entry_page():
    st.header("Daily Production Entry")

    date = st.date_input("Select Date")

    if st.button("Generate Records"):
        df = generate_entries(date)
        st.session_state["prod_df"] = df

    if "prod_df" in st.session_state:
        df = st.session_state["prod_df"]
        edited_df = st.data_editor(df)

        if st.button("Save to DB"):
            session = Session()

            for _, row in edited_df.iterrows():
                eff = calc_efficiency(row["actual"], row["target"])

                entry = DailyProduction(
                    date=row["date"],
                    shift_id=row["shift_id"],
                    machine_id=row["machine_id"],
                    actual=row["actual"],
                    scrap=row["scrap"],
                    downtime=row["downtime"],
                    efficiency=eff,
                    oee=0  # Placeholder
                )
                session.add(entry)

            session.commit()
            st.success("Production entries saved!")
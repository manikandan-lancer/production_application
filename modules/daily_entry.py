import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Machine, Shift, DailyProduction

SessionLocal = sessionmaker(bind=engine)

def load_existing_entries(session, date):
    return session.query(DailyProduction).filter(DailyProduction.date == date).all()


def generate_new_entries(session, date):
    machines = session.query(Machine).all()
    shifts = session.query(Shift).all()

    rows = []
    for shift in shifts:
        for machine in machines:
            rows.append({
                "date": date,
                "shift_id": shift.id,
                "machine_id": machine.id,
                "actual": 0,
                "scrap": 0,
                "downtime": 0,
                "efficiency": 0,
                "oee": 0
            })

    return pd.DataFrame(rows)


def daily_entry_page():
    st.title("Daily Production Entry")

    session = SessionLocal()

    date = st.date_input("Select Date")

    # First check if this date already exists in database
    existing = load_existing_entries(session, date)

    if existing:
        st.success(f"Loaded saved records for {date}")

        df = pd.DataFrame([{
            "id": row.id,
            "date": row.date,
            "shift_id": row.shift_id,
            "machine_id": row.machine_id,
            "actual": row.actual,
            "scrap": row.scrap,
            "downtime": row.downtime,
            "efficiency": row.efficiency,
            "oee": row.oee
        } for row in existing])

    else:
        st.info("No records found for this date. Creating new entries.")
        df = generate_new_entries(session, date)

    st.dataframe(df, use_container_width=True)

    if st.button("Save"):
        # Delete previous records for this date (if any)
        session.query(DailyProduction).filter(DailyProduction.date == date).delete()
        session.commit()

        # Insert updated rows
        for _, row in df.iterrows():
            new_row = DailyProduction(
                date=row["date"],
                shift_id=row["shift_id"],
                machine_id=row["machine_id"],
                actual=row["actual"],
                scrap=row["scrap"],
                downtime=row["downtime"],
                efficiency=row.get("efficiency", 0),
                oee=row.get("oee", 0)
            )
            session.add(new_row)

        session.commit()
        st.success("Data saved successfully!")
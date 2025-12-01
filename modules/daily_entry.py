import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Machine, Shift, DailyProduction

SessionLocal = sessionmaker(bind=engine)


# Load saved entries for selected date
def load_existing_entries(session, date):
    return session.query(DailyProduction).filter(DailyProduction.date == date).all()


# Create NEW blank rows only if NO saved data exists
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
                "target": machine.target
            })

    return pd.DataFrame(rows)


def daily_entry_page():
    st.title("Daily Production Entry")

    session = SessionLocal()
    date = st.date_input("Select Date")

    # STEP 1: TRY TO LOAD EXISTING ROWS
    existing_rows = load_existing_entries(session, date)

    if existing_rows:
        # --- FOUND SAVED RECORDS ---
        st.success(f"Loaded saved records for {date}")

        df = pd.DataFrame([
            {
                "id": row.id,
                "date": row.date,
                "shift_id": row.shift_id,
                "machine_id": row.machine_id,
                "actual": row.actual,
                "scrap": row.scrap,
                "downtime": row.downtime,
                "target": session.query(Machine).filter(Machine.id == row.machine_id).first().target
            }
            for row in existing_rows
        ])

    else:
        # --- NO RECORDS FOUND → GENERATE ONLY ONCE ---
        st.info(f"No saved data found for {date}. Generating new empty rows.")
        df = generate_new_entries(session, date)

    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # Save button
    if st.button("Save to DB"):
        # Delete previous records for that date
        session.query(DailyProduction).filter(DailyProduction.date == date).delete()
        session.commit()

        # Insert new ones
        for _, row in edited_df.iterrows():
            new_row = DailyProduction(
                date=row["date"],
                shift_id=row["shift_id"],
                machine_id=row["machine_id"],
                actual=row["actual"],
                scrap=row["scrap"],
                downtime=row["downtime"],
                efficiency=0,
                oee=0
            )
            session.add(new_row)

        session.commit()
        st.success("Saved successfully!")
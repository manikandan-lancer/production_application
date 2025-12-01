import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Machine, Shift, DailyProduction

SessionLocal = sessionmaker(bind=engine)


def daily_entry_page():
    st.title("Daily Production Entry")

    session = SessionLocal()

    # Select date
    date = st.date_input("Select Date")

    # ---- STEP 1: CHECK IF DATA EXISTS FOR DATE ----
    saved_data = session.query(DailyProduction).filter(
        DailyProduction.date == date
    ).all()

    if saved_data:
        st.success(f"Loaded saved data for {date}")

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
            for row in saved_data
        ])

    else:
        st.warning(f"No saved data found for {date}. Generating new rows.")

        machines = session.query(Machine).all()
        shifts = session.query(Shift).all()

        rows = []

        # create one row per machine per shift
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

        df = pd.DataFrame(rows)

    # ---- DISPLAY EDITABLE TABLE ----
    edited_df = st.data_editor(df, use_container_width=True)

    # ---- SAVE BUTTON ----
    if st.button("Save to DB"):
        # Delete old data for that date
        session.query(DailyProduction).filter(
            DailyProduction.date == date
        ).delete()
        session.commit()

        # Insert new data
        for _, row in edited_df.iterrows():
            entry = DailyProduction(
                date=row["date"],
                shift_id=row["shift_id"],
                machine_id=row["machine_id"],
                actual=row["actual"],
                scrap=row["scrap"],
                downtime=row["downtime"],
                efficiency=0,
                oee=0
            )
            session.add(entry)

        session.commit()
        st.success("Data saved successfully!")
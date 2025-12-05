import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Shift

SessionLocal = sessionmaker(bind=engine)


def shift_master_page():
    st.title("Shift Master")

    session = SessionLocal()

    name = st.selectbox("Shift Name", ["Shift 1", "Shift 2", "Shift 3"])
    start = st.time_input("Start Time")
    end = st.time_input("End Time")
    total = st.number_input("Total Hours", min_value=1.0, value=8.0)

    if st.button("Save Shift"):
        obj = Shift(shift_name=name, start_time=start, end_time=end, total_hours=total)
        session.add(obj)
        session.commit()
        st.success("Shift Saved!")

    st.subheader("Existing Shifts")
    shifts = session.query(Shift).all()
    for s in shifts:
        st.write(f"{s.id} — {s.shift_name} | {s.start_time} to {s.end_time} — {s.total_hours} hrs")
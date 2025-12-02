import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Shift

SessionLocal = sessionmaker(bind=engine)

def shift_master_page():
    st.title("Shift Master")

    session = SessionLocal()

    shift_name = st.text_input("Shift Name (A / B / C)")
    start_time = st.time_input("Start Time")
    end_time = st.time_input("End Time")

    if st.button("Add Shift"):
        new_shift = Shift(
            shift_name=shift_name,
            start_time=start_time,
            end_time=end_time
        )
        session.add(new_shift)
        session.commit()
        st.success("Shift Added Successfully!")

    st.subheader("Existing Shifts")
    shifts = session.query(Shift).all()

    if shifts:
        for s in shifts:
            st.write(f"**{s.shift_name}** — {s.start_time} to {s.end_time}")
    else:
        st.info("No shifts found.")
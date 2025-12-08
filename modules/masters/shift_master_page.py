import streamlit as st
from sqlalchemy.orm import sessionmaker
from datetime import time
from database.connection import engine
from database.models import Shift

SessionLocal = sessionmaker(bind=engine)

def shift_master_page():
    st.subheader("⏱ Shift Master")

    session = SessionLocal()

    shifts = session.query(Shift).all()
    st.table({
        "ID": [s.id for s in shifts],
        "Shift": [s.shift_name for s in shifts],
        "Start": [s.start_time for s in shifts],
        "End": [s.end_time for s in shifts]
    })

    name = st.text_input("Shift Name")
    start = st.time_input("Start Time", value=time(6, 0))
    end = st.time_input("End Time", value=time(14, 0))

    if st.button("Save Shift"):
        new_shift = Shift(shift_name=name, start_time=start, end_time=end)
        session.add(new_shift)
        session.commit()
        st.success("Shift Saved!")
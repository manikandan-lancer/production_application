import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Machine, Shift

Session = sessionmaker(bind=engine)

def master_data_page():
    st.header("Master Data Management")
    menu = st.selectbox("Select Master", ["Machines", "Shifts"])

    session = Session()

    if menu == "Machines":
        name = st.text_input("Machine Name")
        product_id = st.number_input("Product ID", step=1)
        cycle_time = st.number_input("Cycle Time")
        target = st.number_input("Target per Shift", step=1)

        if st.button("Save Machine"):
            m = Machine(name=name, product_id=product_id, cycle_time=cycle_time, target=target)
            session.add(m)
            session.commit()
            st.success("Machine saved!")

    elif menu == "Shifts":
        shift_name = st.text_input("Shift Name")
        start = st.time_input("Start Time")
        end = st.time_input("End Time")

        if st.button("Save Shift"):
            s = Shift(shift_name=shift_name, start_time=start, end_time=end)
            session.add(s)
            session.commit()
            st.success("Shift saved!")
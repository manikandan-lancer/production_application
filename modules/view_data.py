import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker

from database.connection import engine
from database.models import Machine, Shift, DailyProduction

SessionLocal = sessionmaker(bind=engine)


def view_data_page():
    st.title("📊 View Stored Data")

    session = SessionLocal()

    option = st.selectbox(
        "Select Table",
        ["Machines", "Shifts", "Daily Production"]
    )

    if option == "Machines":
        data = session.query(Machine).all()

    elif option == "Shifts":
        data = session.query(Shift).all()

    else:
        data = session.query(DailyProduction).all()

    if not data:
        st.warning("No data found in this table.")
        return

    # Convert SQLAlchemy objects → DataFrame
    df = pd.DataFrame([row.__dict__ for row in data])
    df.drop(columns=["_sa_instance_state"], inplace=True)

    st.dataframe(df, use_container_width=True)
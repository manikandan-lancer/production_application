import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import CountMaster

SessionLocal = sessionmaker(bind=engine)


def count_master_page():
    st.header("📦 Count (Product) Master")

    session = SessionLocal()

    count_name = st.text_input("Count Name")
    actual_count = st.number_input("Actual Count", min_value=0.0)
    production_factor = st.number_input("Production Factor", min_value=0.0)

    if st.button("Save Count"):
        new_count = CountMaster(
            count_name=count_name,
            actual_count=actual_count,
            production_factor=production_factor
        )
        session.add(new_count)
        session.commit()
        st.success("Count added successfully!")

    st.subheader("Existing Counts")
    data = session.query(CountMaster).all()
    for row in data:
        st.write(f"{row.id} — {row.count_name} | Count: {row.actual_count} | PF: {row.production_factor}")

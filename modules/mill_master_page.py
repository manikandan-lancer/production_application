import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Mill

SessionLocal = sessionmaker(bind=engine)

def mill_master_page():
    st.title("Mill Master")

    session = SessionLocal()

    mill_name = st.text_input("Enter Mill Name")

    if st.button("Add Mill"):
        if mill_name.strip() == "":
            st.error("Mill name cannot be empty.")
        else:
            mill = Mill(mill_name=mill_name)
            session.add(mill)
            session.commit()
            st.success("Mill Added Successfully")

    st.subheader("Existing Mills")
    mills = session.query(Mill).all()
    for m in mills:
        st.write(f"ID: {m.id} | Name: {m.mill_name}")
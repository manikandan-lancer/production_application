import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Mill

SessionLocal = sessionmaker(bind=engine)

def mill_master_page():
    st.subheader("🏭 Mill Master")

    session = SessionLocal()

    mills = session.query(Mill).all()
    st.table({"ID": [m.id for m in mills], "Mill": [m.mill_name for m in mills]})

    mill_name = st.text_input("Add Mill Name")

    if st.button("Save Mill"):
        if mill_name:
            new_mill = Mill(mill_name=mill_name)
            session.add(new_mill)
            session.commit()
            st.success("Mill Saved!")
import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Department

SessionLocal = sessionmaker(bind=engine)

def department_master_page():
    st.subheader("🏢 Department Master")

    session = SessionLocal()
    depts = session.query(Department).all()
    st.table({"ID": [d.id for d in depts], "Department": [d.department_name for d in depts]})

    dept = st.text_input("Add Department Name")

    if st.button("Save Department"):
        if dept:
            new_dept = Department(department_name=dept)
            session.add(new_dept)
            session.commit()
            st.success("Department Saved!")
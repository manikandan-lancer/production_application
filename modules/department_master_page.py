import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Department

SessionLocal = sessionmaker(bind=engine)

def department_master_page():
    st.title("Department Master")

    session = SessionLocal()

    dept_name = st.text_input("Enter Department Name")

    if st.button("Add Department"):
        dept = Department(department_name=dept_name)
        session.add(dept)
        session.commit()
        st.success("Department Added")

    st.subheader("Departments:")
    departments = session.query(Department).all()
    for d in departments:
        st.write(f"{d.id} — {d.department_name}")

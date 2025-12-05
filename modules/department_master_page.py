import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Department

SessionLocal = sessionmaker(bind=engine)


def department_master_page():
    st.header("🏢 Department Master")

    session = SessionLocal()

    name = st.text_input("Department Name")

    if st.button("Save Department"):
        dept = Department(department_name=name)
        session.add(dept)
        session.commit()
        st.success("Department Saved!")

    st.subheader("Existing Departments")
    depts = session.query(Department).all()
    for d in depts:
        st.write(f"{d.id} — {d.department_name}")
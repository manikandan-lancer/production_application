import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Employee, Mill

SessionLocal = sessionmaker(bind=engine)

def employee_master_page():
    st.subheader("👷 Employee Master")

    session = SessionLocal()

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    emp_no = st.text_input("Employee Number")
    emp_name = st.text_input("Employee Name")
    designation = st.text_input("Designation")
    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    if st.button("Save Employee"):
        emp = Employee(
            employee_no=emp_no,
            employee_name=emp_name,
            designation=designation,
            mill_id=mill_id
        )
        session.add(emp)
        session.commit()
        st.success("Employee Saved!")
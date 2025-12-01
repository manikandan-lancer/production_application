import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Employee, Mill, Department

SessionLocal = sessionmaker(bind=engine)

def employee_master_page():
    st.title("Employee Master")

    session = SessionLocal()

    employee_no = st.text_input("Employee No (TNo)")
    employee_name = st.text_input("Employee Name")

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}
    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    departments = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in departments}
    dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    if st.button("Save Employee"):
        emp = Employee(
            employee_no=employee_no,
            employee_name=employee_name,
            mill_id=mill_id,
            department_id=dept_id
        )
        session.add(emp)
        session.commit()
        st.success("Employee Saved")

    st.subheader("Employees:")
    employees = session.query(Employee).all()
    for e in employees:
        st.write(f"{e.employee_no} — {e.employee_name}")

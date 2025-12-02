import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Employee, Mill, Department

SessionLocal = sessionmaker(bind=engine)

def employee_master_page():
    st.title("Employee Master")

    session = SessionLocal()

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}

    emp_no = st.text_input("Employee No (T.No)")
    emp_name = st.text_input("Employee Name")

    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
    dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    if st.button("Add Employee"):
        if emp_no.strip() == "" or emp_name.strip() == "":
            st.error("Employee No and Name cannot be empty.")
        else:
            emp = Employee(
                employee_no=emp_no,
                employee_name=emp_name,
                mill_id=mill_id,
                department_id=dept_id
            )
            session.add(emp)
            session.commit()
            st.success("Employee Added")

    st.subheader("Existing Employees")
    employees = session.query(Employee).all()

    for e in employees:
        st.write(f"{e.employee_no} — {e.employee_name} | Mill: {e.mill_id} | Dept: {e.department_id}")
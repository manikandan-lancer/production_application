import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Employee, Mill

SessionLocal = sessionmaker(bind=engine)

def employee_master_page():
    st.title("Employee Master")

    session = SessionLocal()

    # Mill list
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    st.subheader("Add Employee")

    emp_no = st.text_input("Employee No (T.No)")
    emp_name = st.text_input("Employee Name")
    designation = st.text_input("Designation (Optional)")

    mill_id = st.selectbox("Select Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    if st.button("Save Employee"):
        if not emp_no.strip() or not emp_name.strip():
            st.error("Employee number and name cannot be empty.")
        else:
            emp = Employee(
                employee_no=emp_no,
                employee_name=emp_name,
                designation=designation,
                mill_id=mill_id
            )
            session.add(emp)
            session.commit()
            st.success("Employee added successfully!")

    st.subheader("Existing Employees")
    employees = session.query(Employee).all()

    for e in employees:
        st.write(
            f"{e.employee_no} — {e.employee_name} | Mill: {mill_map.get(e.mill_id, 'N/A')} | "
            f"Designation: {e.designation or '-'}"
        )
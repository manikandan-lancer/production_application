import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import DailyProduction, Machine, Employee, Shift, Mill, Department

SessionLocal = sessionmaker(bind=engine)

def view_data_page():
    st.title("View Saved Production Data")

    session = SessionLocal()

    data = session.query(DailyProduction).all()

    rows = []
    for d in data:
        machine = session.query(Machine).filter(Machine.id == d.machine_id).first()
        emp = session.query(Employee).filter(Employee.id == d.employee_id).first()
        shift = session.query(Shift).filter(Shift.id == d.shift_id).first()
        mill = session.query(Mill).filter(Mill.id == d.mill_id).first()
        dept = session.query(Department).filter(Department.id == d.department_id).first()

        rows.append({
            "Date": d.date,
            "Mill": mill.mill_name if mill else "",
            "Department": dept.department_name if dept else "",
            "Shift": shift.shift_name if shift else "",
            "Machine": machine.frame_number if machine else "",
            "Employee": emp.employee_name if emp else "",
            "Actual": d.actual,
            "Waste": d.waste,
            "Run Hr": d.run_hr,
            "Prod": d.prod,
            "TS": d.ts,
            "Count": d.count,
            "Remarks": d.remarks,
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

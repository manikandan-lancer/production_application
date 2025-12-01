import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Machine, Mill, Department

SessionLocal = sessionmaker(bind=engine)

def machine_master_page():
    st.title("Machine Master")

    session = SessionLocal()

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    depts = session.query(Department).all()
    dept_map = {d.id: d.dept_name for d in depts}

    mill_id = st.selectbox("Select Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
    dept_id = st.selectbox("Select Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    frame_no = st.text_input("Frame Number")
    product = st.text_input("Product")
    speed = st.number_input("Speed", min_value=0.0)
    tpi = st.number_input("TPI", min_value=0.0)
    hank = st.number_input("STD Hank", min_value=0.0)
    cycle = st.number_input("Cycle Time", min_value=0.0)
    target = st.number_input("Target", min_value=0)

    if st.button("Add Machine"):
        machine = Machine(
            mill_id=mill_id,
            department_id=dept_id,
            frame_number=frame_no,
            product=product,
            speed=speed,
            tpi=tpi,
            std_hank=hank,
            cycle_time=cycle,
            target=target
        )
        session.add(machine)
        session.commit()
        st.success("Machine Added")

    st.subheader("Machines List")
    machines = session.query(Machine).all()

    for m in machines:
        st.write(f"{m.id} | Frame {m.frame_number} | Mill {m.mill_id} | Dept {m.department_id}")

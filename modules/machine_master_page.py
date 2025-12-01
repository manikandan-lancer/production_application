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
    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}
    dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])

    frame_number = st.text_input("Frame Number")
    product = st.text_input("Product")
    speed = st.number_input("Speed", min_value=0)
    tpi = st.number_input("TPI", min_value=0)
    std_hank = st.number_input("Std Hank", min_value=0.0)
    target = st.number_input("Target", min_value=0)

    if st.button("Save Machine"):
        machine = Machine(
            mill_id=mill_id,
            department_id=dept_id,
            frame_number=frame_number,
            product=product,
            speed=speed,
            tpi=tpi,
            std_hank=std_hank,
            target=target
        )
        session.add(machine)
        session.commit()
        st.success("Machine Saved")

    st.subheader("Machines:")
    machines = session.query(Machine).all()
    for m in machines:
        st.write(f"{m.frame_number} — {m.product}")

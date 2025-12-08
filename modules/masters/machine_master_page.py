import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Machine, Mill, Department, CountMaster

SessionLocal = sessionmaker(bind=engine)

def machine_master_page():
    st.subheader("⚙️ Machine Master")

    session = SessionLocal()

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    depts = session.query(Department).all()
    dept_map = {d.id: d.department_name for d in depts}

    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}

    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
    dept_id = st.selectbox("Department", dept_map.keys(), format_func=lambda x: dept_map[x])
    machine_name = st.text_input("Machine Name (A01, B05...)")
    spindles = st.number_input("Spindles", min_value=0)
    count_id = st.selectbox("Allocated Count", [None] + list(count_map.keys()),
                            format_func=lambda x: count_map[x] if x else "None")

    if st.button("Save Machine"):
        m = Machine(
            mill_id=mill_id,
            department_id=dept_id,
            machine_name=machine_name,
            spindles=spindles,
            allocated_count_id=count_id
        )
        session.add(m)
        session.commit()
        st.success("Machine Saved!")
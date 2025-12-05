import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Machine, Mill, CountMaster

SessionLocal = sessionmaker(bind=engine)


def machine_master_page():
    st.header("🛠 Machine Master")

    session = SessionLocal()

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    frame_no = st.text_input("Frame No")
    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
    spindles = st.number_input("Spindles", min_value=0)
    allocated_count = st.number_input("Allocated Count", min_value=0)
    speed = st.number_input("Speed", min_value=0.0)
    hank = st.number_input("Hank", min_value=0.0)
    tpi = st.number_input("TPI", min_value=0.0)

    if st.button("Save Machine"):
        m = Machine(
            frame_no=frame_no,
            mill_id=mill_id,
            spindles=spindles,
            allocated_count=allocated_count,
            speed=speed,
            hank=hank,
            tpi=tpi
        )
        session.add(m)
        session.commit()
        st.success("Machine Saved Successfully!")

    st.subheader("Existing Machines")
    machines = session.query(Machine).all()

    for m in machines:
        st.write(f"{m.id} — Frame {m.frame_no} | Mill {m.mill_id}")
import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Machine, Mill, CountMaster

SessionLocal = sessionmaker(bind=engine)

def machine_master_page():
    st.title("Machine Master")

    session = SessionLocal()

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    counts = session.query(CountMaster).all()
    count_map = {c.id: c.count_name for c in counts}

    st.subheader("Add Machine")

    frame_no = st.text_input("Frame No")
    spindles = st.number_input("Spindles", min_value=0)
    speed = st.number_input("Speed")
    hank = st.number_input("Hank")
    tpi = st.number_input("TPI")

    mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
    count_id = st.selectbox("Allocated Count", count_map.keys(), format_func=lambda x: count_map[x])

    if st.button("Save Machine"):
        if not frame_no:
            st.error("Frame number is required.")
        else:
            machine = Machine(
                frame_no=frame_no,
                mill_id=mill_id,                 # ✔ FIXED
                allocated_count_id=count_id,     # ✔ FIXED
                spindles=spindles,
                speed=speed,
                hank=hank,
                tpi=tpi
            )
            session.add(machine)
            session.commit()
            st.success("Machine added successfully!")

    st.subheader("Existing Machines")

    machines = session.query(Machine).all()

    for m in machines:
        st.write(
            f"Frame {m.frame_no} | Mill: {mill_map.get(m.mill_id)} | "
            f"Count: {count_map.get(m.allocated_count_id)} | Spindles: {m.spindles}"
        )
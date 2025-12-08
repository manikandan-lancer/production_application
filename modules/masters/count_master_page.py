import streamlit as st
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import CountMaster, Mill

SessionLocal = sessionmaker(bind=engine)

def count_master_page():
    st.subheader("📦 Count / Product Master")

    session = SessionLocal()

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    selected_mill = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])

    count_name = st.text_input("Count / Product Name")

    if st.button("Save Count"):
        new_count = CountMaster(mill_id=selected_mill, count_name=count_name)
        session.add(new_count)
        session.commit()
        st.success("Count Saved!")

    counts = session.query(CountMaster).all()
    st.table({
        "ID": [c.id for c in counts],
        "Mill": [mill_map[c.mill_id] for c in counts],
        "Count": [c.count_name for c in counts]
    })
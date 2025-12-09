import streamlit as st
from database.connection import get_session
from database.models import CountMaster, Mill
from sqlalchemy.orm import Session


def count_master_page():

    session: Session = next(get_session())

    st.subheader("📦 Count Master")

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    colA, colB = st.columns(2)
    with colA:
        mill_id = st.selectbox(
            "Select Mill",
            mill_map.keys(),
            format_func=lambda x: mill_map[x]
        )

    with colB:
        count_name = st.text_input("Count Name (Ex: 60PSF)")

    col1, col2, col3 = st.columns(3)

    with col1:
        actual_count = st.number_input("Actual Count", min_value=0.0, step=0.01)

    with col2:
        conversion_factor = st.number_input("Conversion Factor", min_value=0.0, step=0.0001)

    with col3:
        efficiency_base = st.number_input("Efficiency Base", min_value=0.0, step=0.01)

    if st.button("💾 Save Count"):
        if count_name.strip() == "":
            st.error("Count Name is required!")
            return

        count_obj = CountMaster(
            mill_id=mill_id,
            count_name=count_name.strip(),
            actual_count=actual_count,
            conversion_factor=conversion_factor,
            efficiency_base=efficiency_base
        )

        session.add(count_obj)
        session.commit()
        st.success("✅ Count Saved Successfully!")

    st.divider()

    st.subheader("📋 Existing Counts")

    all_counts = session.query(CountMaster).order_by(CountMaster.id.asc()).all()

    st.dataframe([
        {
            "Mill": mill_map[c.mill_id],
            "Count Name": c.count_name,
            "Actual Count": float(c.actual_count or 0),
            "Conversion Factor": float(c.conversion_factor or 0),
            "Efficiency Base": float(c.efficiency_base or 0)
        }
        for c in all_counts
    ], use_container_width=True)

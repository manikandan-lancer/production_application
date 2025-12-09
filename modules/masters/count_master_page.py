import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import Mill, CountMaster
from utils.calc_engine import calc_conversion_factor


def count_master_page():
    st.header("🧵 Count Master (Product Setup)")
    st.info("Setup actual count, efficiency base, and conversion factor.")

    session: Session = next(get_session())

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    # ---------------------------------------
    # ADD NEW COUNT
    # ---------------------------------------
    with st.form("add_count"):
        st.subheader("➕ Add Count")

        col1, col2 = st.columns(2)
        with col1:
            mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
            count_name = st.text_input("Count Name")

        with col2:
            actual_count = st.number_input("Actual Count", step=0.01)
            efficiency_base = st.number_input("Efficiency Base (%)", step=0.01)

        preview_factor = calc_conversion_factor(actual_count, efficiency_base)
        st.write(f"📘 Conversion Factor: **{preview_factor}**")

        submit = st.form_submit_button("💾 Save")

        if submit:
            c = CountMaster(
                mill_id=mill_id,
                count_name=count_name,
                actual_count=actual_count,
                efficiency_base=efficiency_base,
                conversion_factor=preview_factor
            )
            session.add(c)
            session.commit()
            st.success("✔ Count Added")

    st.divider()
    st.subheader("📄 Existing Counts")

    # LOAD LIST
    counts = session.query(CountMaster).order_by(CountMaster.mill_id.asc()).all()

    df = pd.DataFrame([
        {
            "id": c.id,
            "Mill": mill_map[c.mill_id],
            "Count": c.count_name,
            "Actual Count": float(c.actual_count or 0),
            "Efficiency Base": float(c.efficiency_base or 0),
            "Conversion Factor": float(c.conversion_factor or 0),
        }
        for c in counts
    ])

    edited = st.data_editor(df, use_container_width=True, hide_index=True)

    # SAVE UPDATE
    if st.button("💾 Update Counts"):
        for _, row in edited.iterrows():
            c = session.query(CountMaster).filter_by(id=row["id"]).first()

            c.actual_count = row["Actual Count"]
            c.efficiency_base = row["Efficiency Base"]
            c.conversion_factor = calc_conversion_factor(
                row["Actual Count"], row["Efficiency Base"]
            )

        session.commit()
        st.success("✔ Updated successfully")
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import Mill, CountMaster
from utils.calc_engine import (
    calc_conversion_factor,
    safe
)


# -------------------------------------------------------
# COUNT MASTER PAGE
# -------------------------------------------------------
def count_master_page():
    st.title("🧵 Count Master")

    session: Session = next(get_session())

    st.info("Add/Edit product counts. Conversion Factor auto-calculates based on Actual Count + Efficiency Base.")

    # -------------------------------------------------------
    # LOAD MILLS
    # -------------------------------------------------------
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    # -------------------------------------------------------
    # ADD NEW COUNT
    # -------------------------------------------------------
    st.subheader("➕ Add New Count")

    with st.form("add_new_count"):
        col1, col2 = st.columns(2)

        with col1:
            mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
            count_name = st.text_input("Count Name (e.g., 60PSF, 40PC)")

        with col2:
            actual_count = st.number_input("Actual Count", min_value=0.0, step=0.01)
            efficiency_base = st.number_input("Efficiency Base (%)", min_value=0.0, step=0.01)

        # LIVE PREVIEW
        conv_prev = calc_conversion_factor(actual_count, efficiency_base)
        st.write(f"📘 **Conversion Factor Preview:** `{conv_prev}`")

        submit = st.form_submit_button("💾 Save Count")

        if submit:
            if count_name.strip() == "":
                st.error("Count name cannot be empty.")
            else:
                new_count = CountMaster(
                    mill_id=mill_id,
                    count_name=count_name,
                    actual_count=actual_count,
                    efficiency_base=efficiency_base,
                    conversion_factor=conv_prev,
                )
                session.add(new_count)
                session.commit()

                st.success("✅ Count Added Successfully!")

    st.divider()

    # -------------------------------------------------------
    # EXISTING COUNTS TABLE
    # -------------------------------------------------------
    st.subheader("📄 Existing Counts")

    counts = session.query(CountMaster).order_by(CountMaster.mill_id, CountMaster.count_name).all()

    if not counts:
        st.warning("No count records found.")
        return

    df = pd.DataFrame([
        {
            "ID": c.id,
            "Mill": c.mill.mill_name,
            "Count Name": c.count_name,
            "Actual Count": float(c.actual_count or 0),
            "Efficiency Base (%)": float(c.efficiency_base or 0),
            "Conversion Factor": float(c.conversion_factor or 0),
        }
        for c in counts
    ])

    edited_df = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Conversion Factor": st.column_config.NumberColumn(disabled=True),
            "ID": st.column_config.NumberColumn(disabled=True),
            "Mill": st.column_config.TextColumn(disabled=True),
        }
    )

    # -------------------------------------------------------
    # SAVE CHANGES
    # -------------------------------------------------------
    if st.button("💾 Update Count Records"):

        for _, row in edited_df.iterrows():

            c = session.query(CountMaster).filter_by(id=row["ID"]).first()
            if c:

                c.actual_count = safe(row["Actual Count"])
                c.efficiency_base = safe(row["Efficiency Base (%)"])
                c.conversion_factor = calc_conversion_factor(
                    c.actual_count,
                    c.efficiency_base
                )

        session.commit()
        st.success("✅ Count Master Updated Successfully!")

        st.info("All dependent modules (Machine Master, Daily Entry, Dashboard) will now reflect these changes automatically.")
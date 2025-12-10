import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import Mill, CountMaster
from utils.calc_engine import (
    safe,
    calc_conversion_factor
)


# -------------------------------------------------------
# COUNT MASTER PAGE
# -------------------------------------------------------
def count_master_page():
    st.title("🧵 Count Master")

    session: Session = next(get_session())

    st.info(
        "Manage all yarn counts. "
        "Conversion Factor updates automatically when Actual Count or Efficiency Base changes."
    )

    # -------------------------------------------------------
    # Load mills
    # -------------------------------------------------------
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    # -------------------------------------------------------
    # Add New Count
    # -------------------------------------------------------
    st.subheader("➕ Add New Count")

    with st.form("add_count_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            mill_id = st.selectbox(
                "Mill",
                mill_map.keys(),
                format_func=lambda x: mill_map[x]
            )
            count_name = st.text_input(
                "Count Name (ex: 60PSF, 40PC, etc.)",
                placeholder="Enter Count Name"
            )

        with col2:
            actual_count = st.number_input("Actual Count", min_value=0.0, step=0.01)
            efficiency_base = st.number_input("Efficiency Base (%)", min_value=0.0, step=0.01)

        # Live conversion factor preview
        preview_cf = calc_conversion_factor(actual_count, efficiency_base)
        st.write(f"📘 **Conversion Factor:** `{preview_cf}`")

        submitted = st.form_submit_button("💾 Save Count")

        if submitted:
            if count_name.strip() == "":
                st.error("Count name cannot be empty.")
            else:
                # Check if count name already exists under same mill
                existing = (
                    session.query(CountMaster)
                    .filter(
                        CountMaster.mill_id == mill_id,
                        CountMaster.count_name == count_name.strip()
                    )
                    .first()
                )

                if existing:
                    st.error("This count already exists for the selected mill.")
                else:
                    new_count = CountMaster(
                        mill_id=mill_id,
                        count_name=count_name.strip(),
                        actual_count=actual_count,
                        efficiency_base=efficiency_base,
                        conversion_factor=preview_cf
                    )
                    session.add(new_count)
                    session.commit()
                    st.success("✅ Count added successfully!")

    st.divider()
    st.subheader("📄 Existing Counts")

    # -------------------------------------------------------
    # Load table data
    # -------------------------------------------------------
    counts = session.query(CountMaster).order_by(
        CountMaster.mill_id.asc(), CountMaster.count_name.asc()
    ).all()

    if not counts:
        st.warning("No count records found. Please add counts.")
        return

    df = pd.DataFrame([
        {
            "ID": c.id,
            "Mill": mill_map[c.mill_id],
            "Count Name": c.count_name,
            "Actual Count": float(c.actual_count or 0),
            "Efficiency Base (%)": float(c.efficiency_base or 0),
            "Conversion Factor": float(c.conversion_factor or 0),
        }
        for c in counts
    ])

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn(disabled=True),
            "Mill": st.column_config.TextColumn(disabled=True),
            "Count Name": st.column_config.TextColumn(disabled=True),
            "Conversion Factor": st.column_config.NumberColumn(disabled=True),
        }
    )

    st.markdown("### 💾 Save Updates to Existing Counts")

    if st.button("Update Count Records"):
        for _, row in edited_df.iterrows():
            record = session.query(CountMaster).filter_by(id=row["ID"]).first()
            if record:
                record.actual_count = safe(row["Actual Count"])
                record.efficiency_base = safe(row["Efficiency Base (%)"])
                record.conversion_factor = calc_conversion_factor(
                    record.actual_count,
                    record.efficiency_base
                )

        session.commit()
        st.success("✅ Counts updated successfully!")

        st.info("All related modules (Machine Master, Daily Entry, Dashboard) will reflect updated Conversion Factors.")
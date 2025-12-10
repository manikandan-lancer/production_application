import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import Mill, CountMaster
from utils.calc_engine import (
    safe_float,
    calc_conversion_factor
)


# -------------------------------------------------------
# COUNT MASTER PAGE
# -------------------------------------------------------
def count_master_page():
    st.title("🧵 COUNT MASTER — Product Definitions")

    session: Session = next(get_session())

    st.info("""
    ✔ Add/Edit Counts  
    ✔ Conversion factor updates automatically  
    ✔ Changes reflect immediately in Daily Entry & Dashboard  
    """)

    # -------------------------------------------------------
    # LOAD MILLS
    # -------------------------------------------------------
    mills = session.query(Mill).order_by(Mill.mill_name.asc()).all()
    mill_map = {m.id: m.mill_name for m in mills}

    # -------------------------------------------------------
    # ADD NEW COUNT
    # -------------------------------------------------------
    st.subheader("➕ Add New Count")

    with st.form("add_new_count"):
        col1, col2 = st.columns(2)

        with col1:
            mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
            count_name = st.text_input("Count Name (Example: 40PSF, 60CW)")

        with col2:
            actual_count = st.number_input("Actual Count", min_value=0.00, step=0.01)
            efficiency_base = st.number_input("Efficiency Base (%)", min_value=0.00, step=0.01)

        conv_preview = calc_conversion_factor(actual_count, efficiency_base)
        st.write(f"📘 **Conversion Factor:** `{conv_preview}`")

        submitted = st.form_submit_button("💾 Save")

        if submitted:
            if count_name.strip() == "":
                st.error("Count Name cannot be empty.")
                return

            # DUPLICATE CHECK
            existing = (
                session.query(CountMaster)
                .filter(
                    CountMaster.mill_id == mill_id,
                    CountMaster.count_name == count_name,
                )
                .first()
            )

            if existing:
                st.error(f"❌ Count '{count_name}' already exists in {mill_map[mill_id]}")
                return

            new_count = CountMaster(
                mill_id=mill_id,
                count_name=count_name.strip(),
                actual_count=safe_float(actual_count),
                efficiency_base=safe_float(efficiency_base),
                conversion_factor=conv_preview,
            )
            session.add(new_count)
            session.commit()

            st.success("✅ Count Added Successfully!")

    st.divider()

    # -------------------------------------------------------
    # EXISTING COUNT TABLE
    # -------------------------------------------------------
    st.subheader("📄 Existing Count Records")

    counts = (
        session.query(CountMaster)
        .order_by(CountMaster.mill_id, CountMaster.count_name)
        .all()
    )

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

    edited = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ID": st.column_config.TextColumn(disabled=True),
            "Mill": st.column_config.TextColumn(disabled=True),
            "Conversion Factor": st.column_config.NumberColumn(disabled=True),
        }
    )

    # -------------------------------------------------------
    # SAVE EDITS
    # -------------------------------------------------------
    if st.button("💾 Update Records"):

        for _, row in edited.iterrows():

            c = session.query(CountMaster).filter_by(id=row["ID"]).first()
            if not c:
                continue

            # Check duplicate Count Name (only if name changed)
            new_name = row["Count Name"].strip()
            if new_name != c.count_name:
                dup = (
                    session.query(CountMaster)
                    .filter(
                        CountMaster.mill_id == c.mill_id,
                        CountMaster.count_name == new_name,
                        CountMaster.id != c.id
                    )
                    .first()
                )
                if dup:
                    st.error(
                        f"❌ Cannot rename to '{new_name}'. "
                        f"It already exists in {c.mill.mill_name}."
                    )
                    return

            # Apply updates
            c.count_name = new_name
            c.actual_count = safe_float(row["Actual Count"])
            c.efficiency_base = safe_float(row["Efficiency Base (%)"])

            # Recalculate conversion factor
            c.conversion_factor = calc_conversion_factor(
                c.actual_count,
                c.efficiency_base
            )

        session.commit()
        st.success("✅ Count Master Updated Successfully!")

        st.info("All changes now reflect automatically in Daily Entry & Dashboard.")
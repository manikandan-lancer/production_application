import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import Mill, CountMaster
from utils.calc_engine import (
    safe_float,
    calc_conversion_factor,
)


# -------------------------------------------------------
# COUNT MASTER PAGE (UPDATED DESIGN)
# -------------------------------------------------------
def count_master_page():
    st.title("🧵 Count Master")

    session: Session = next(get_session())

    st.info("""
    **This table defines the spinning constants for each Count per Mill.**  
    These values update Machine Master and Daily Entry automatically.
    """)

    # -------------------------------------------------------
    # LOAD MILLS
    # -------------------------------------------------------
    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    # -------------------------------------------------------
    # ADD / UPDATE COUNT VALUES
    # -------------------------------------------------------
    st.subheader("➕ Add or Update Count")

    with st.form("count_master_form"):
        col1, col2 = st.columns(2)

        with col1:
            mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
            count_name = st.text_input("Count Name (Ex: 40s, 60s, 44s Compact)")

        with col2:
            actual_count = st.number_input("Actual Count", min_value=0.0, step=0.01)
            spinning_eff = st.number_input("Spinning Count Efficiency (%)", min_value=0.0, step=0.01)
            std_hank_eff = st.number_input("Std Hank Efficiency (%)", min_value=0.0, step=0.01)

        # LIVE CALC PREVIEW
        preview_cf = calc_conversion_factor(actual_count, spinning_eff)
        st.write(f"📘 **Conversion Factor Preview:** `{preview_cf}`")

        submit = st.form_submit_button("💾 Save / Update Count")

        if submit:
            if not count_name.strip():
                st.error("Count name cannot be empty.")
                return

            # CHECK IF COUNT ALREADY EXISTS (By name + mill)
            existing = (
                session.query(CountMaster)
                .filter(
                    CountMaster.mill_id == mill_id,
                    CountMaster.count_name == count_name.strip(),
                )
                .first()
            )

            if existing:
                # UPDATE existing count
                existing.actual_count = actual_count
                existing.spinning_efficiency = spinning_eff
                existing.std_hank_efficiency = std_hank_eff
                existing.conversion_factor = preview_cf

                st.success("✔ Existing Count Updated Successfully")
            else:
                # CREATE new count
                new_count = CountMaster(
                    mill_id=mill_id,
                    count_name=count_name.strip(),
                    actual_count=actual_count,
                    spinning_count_eff=spinning_eff, 
                    std_hank_efficiency=std_hank_eff,
                    conversion_factor=preview_cf,
                )
                session.add(new_count)
                st.success("✔ New Count Added Successfully")

            session.commit()

    st.divider()

    # -------------------------------------------------------
    # DISPLAY EXISTING COUNTS
    # -------------------------------------------------------
    st.subheader("📄 Existing Counts")

    counts = session.query(CountMaster).order_by(
        CountMaster.mill_id, CountMaster.count_name
    ).all()

    if not counts:
        st.warning("No count records found.")
        return

    df = pd.DataFrame([
        {
            "ID": c.id,
            "Mill": c.mill.mill_name,
            "Count Name": c.count_name,
            "Actual Count": float(c.actual_count or 0),
            "Spinning Count Efficiency (%)": float(c.spinning_efficiency or 0),
            "Std Hank Efficiency (%)": float(c.std_hank_efficiency or 0),
            "Conversion Factor": float(c.conversion_factor or 0),
        }
        for c in counts
    ])

    editor = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ID": st.column_config.NumberColumn(disabled=True),
            "Mill": st.column_config.TextColumn(disabled=True),
            "Conversion Factor": st.column_config.NumberColumn(disabled=True),
        }
    )

    # -------------------------------------------------------
    # SAVE UPDATES
    # -------------------------------------------------------
    if st.button("💾 Update Count Records"):

        for _, row in editor.iterrows():
            c = session.query(CountMaster).filter_by(id=row["ID"]).first()
            if c:
                c.actual_count = safe_float(row["Actual Count"])
                c.spinning_efficiency = safe_float(row["Spinning Count Efficiency (%)"])
                c.std_hank_efficiency = safe_float(row["Std Hank Efficiency (%)"])
                c.conversion_factor = calc_conversion_factor(
                    c.actual_count,
                    c.spinning_efficiency,
                )

        session.commit()
        st.success("✔ Count Master Updated")

        st.info("Machine Master & Daily Entry automatically reflect updated values.")
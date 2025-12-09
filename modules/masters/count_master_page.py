import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.connection import get_session
from database.models import Mill, CountMaster
from utils.calc_engine import calc_conversion_factor


# -------------------------------------------------------
# COUNT MASTER PAGE
# -------------------------------------------------------
def count_master_page():
    st.title("🧵 Count Master")

    session: Session = next(get_session())

    mills = session.query(Mill).all()
    mill_map = {m.id: m.mill_name for m in mills}

    st.info("""
    • Add counts for each mill  
    • Enter **Actual Count** and **Efficiency Base**  
    • System will auto-calculate **Conversion Factor**  
    • These values are used live in Daily Entry & Dashboard  
    """)

    # -------------------------------------------------------
    # ADD NEW COUNT
    # -------------------------------------------------------
    st.subheader("➕ Add New Count")

    with st.form("add_count_form"):
        col1, col2 = st.columns(2)

        with col1:
            mill_id = st.selectbox("Mill", mill_map.keys(), format_func=lambda x: mill_map[x])
            count_name = st.text_input("Count Name (Ex: 60PSF, 40PC, 63PSFL)")

        with col2:
            actual_count = st.number_input("Actual Count", min_value=0.0, step=0.01)
            efficiency_base = st.number_input("Efficiency Base (%)", min_value=0.0, step=0.01)

        # LIVE CALCULATION DISPLAY
        conv_factor = calc_conversion_factor(actual_count, efficiency_base)
        st.write(f"📘 **Calculated Conversion Factor:** `{conv_factor}`")

        submitted = st.form_submit_button("💾 Save Count")

        if submitted:
            if not count_name.strip():
                st.error("❌ Count name cannot be empty.")
            else:
                new_obj = CountMaster(
                    mill_id=mill_id,
                    count_name=count_name.strip(),
                    actual_count=actual_count,
                    efficiency_base=efficiency_base,
                    conversion_factor=conv_factor
                )
                session.add(new_obj)
                session.commit()
                st.success("✅ Count saved successfully!")

    st.divider()

    # -------------------------------------------------------
    # LOAD EXISTING COUNTS
    # -------------------------------------------------------
    st.subheader("📄 Existing Counts")

    counts = (
        session.query(CountMaster)
        .order_by(CountMaster.mill_id.asc(), CountMaster.count_name.asc())
        .all()
    )

    if not counts:
        st.warning("No count records found.")
        return

    # Build DataFrame
    df = pd.DataFrame([
        {
            "id": c.id,
            "mill": c.mill.mill_name,
            "count_name": c.count_name,
            "actual_count": float(c.actual_count or 0),
            "efficiency_base": float(c.efficiency_base or 0),
            "conversion_factor": float(c.conversion_factor or 0)
        }
        for c in counts
    ])

    st.caption("✏️ Modify Actual Count / Efficiency Base → Conversion Factor auto-updates.")

    edited_df = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        disabled=["id", "mill", "count_name", "conversion_factor"]
    )

    # -------------------------------------------------------
    # SAVE UPDATED TABLE VALUES
    # -------------------------------------------------------
    if st.button("💾 Save Changes"):

        for _, row in edited_df.iterrows():
            c = session.query(CountMaster).filter_by(id=row["id"]).first()
            if c:

                c.actual_count = row["actual_count"]
                c.efficiency_base = row["efficiency_base"]

                # RECALCULATE conversion factor
                c.conversion_factor = calc_conversion_factor(
                    c.actual_count,
                    c.efficiency_base
                )

        session.commit()
        st.success("✅ Count records updated successfully!")
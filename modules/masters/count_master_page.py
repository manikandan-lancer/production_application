import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import CountMaster
from utils.calc_engine import safe_float, calc_conversion_factor


# -------------------------------------------------------
# COUNT MASTER PAGE — UPDATED WITH RESET BUTTON
# -------------------------------------------------------
def count_master_page():
    st.title("🧵 Count Master Setup")

    session: Session = next(get_session())

    # -------------------------------
    # SESSION STATE (RESET SUPPORT)
    # -------------------------------
    if "cm_reset" not in st.session_state:
        st.session_state.cm_reset = False

    if st.session_state.cm_reset:
        st.session_state.cm_name = ""
        st.session_state.cm_actual = 0.0
        st.session_state.cm_spin_eff = 0.0
        st.session_state.cm_std_eff = 0.0
        st.session_state.cm_40s = 0.0
        st.session_state.cm_reset = False

    st.info("""
    Configure count-level constants.
    These values automatically update:
    Machine Master, Daily Entry, and Dashboard.
    """)

    # -------------------------------------------------------
    # ADD / UPDATE COUNT
    # -------------------------------------------------------
    st.subheader("➕ Add / Update Count")

    with st.form("count_form"):
        col1, col2 = st.columns(2)

        with col1:
            count_name = st.text_input(
                "Count Name (e.g. 40s, 60s)",
                key="cm_name"
            )
            actual_count = st.number_input(
                "Actual Count",
                min_value=0.0,
                step=0.01,
                key="cm_actual"
            )

        with col2:
            spinning_eff = st.number_input(
                "Spinning Count Efficiency (%)",
                min_value=0.0,
                step=0.01,
                key="cm_spin_eff"
            )

            std_hank_eff = st.number_input(
                "Std Hank Efficiency (%)",
                min_value=0.0,
                step=0.01,
                key="cm_std_eff"
            )

            conv_40s_factor = st.number_input(
                "40s Conversion Factor",
                min_value=0.0,
                step=0.000001,
                format="%.6f",
                key="cm_40s"
            )

        # LIVE PREVIEW
        preview_cf = calc_conversion_factor(actual_count, spinning_eff)
        st.write(f"📘 **Conversion Factor Preview:** `{preview_cf}`")

        b1, b2 = st.columns(2)

        submit = b1.form_submit_button("💾 Save / Update Count")
        reset = b2.form_submit_button("🔄 Reset")

        # ---------------- RESET ----------------
        if reset:
            st.session_state.cm_reset = True
            st.rerun()

        # ---------------- SAVE ----------------
        if submit:
            name_clean = count_name.strip().upper()

            if not name_clean:
                st.error("Count Name cannot be empty.")
                return

            existing = (
                session.query(CountMaster)
                .filter(CountMaster.count_name == name_clean)
                .first()
            )

            if existing:
                existing.actual_count = actual_count
                existing.spinning_count_eff = spinning_eff
                existing.std_hank_eff = std_hank_eff
                existing.conversion_factor = preview_cf
                existing.conv_40s_factor = conv_40s_factor
                st.success("✔ Count Updated Successfully")

            else:
                session.add(CountMaster(
                    count_name=name_clean,
                    actual_count=actual_count,
                    spinning_count_eff=spinning_eff,
                    std_hank_eff=std_hank_eff,
                    conversion_factor=preview_cf,
                    conv_40s_factor=conv_40s_factor,
                ))
                st.success("✔ New Count Added Successfully")

            session.commit()

    st.divider()

    # -------------------------------------------------------
    # EXISTING COUNTS TABLE
    # -------------------------------------------------------
    st.subheader("📄 Existing Counts")

    counts = (
        session.query(CountMaster)
        .order_by(CountMaster.count_name)
        .all()
    )

    if not counts:
        st.warning("No count records found.")
        return

    df = pd.DataFrame([
        {
            "ID": c.id,
            "Count Name": c.count_name,
            "Actual Count": float(c.actual_count or 0),
            "Spinning Count Efficiency (%)": float(c.spinning_count_eff or 0),
            "Std Hank Efficiency (%)": float(c.std_hank_eff or 0),
            "Conversion Factor": float(c.conversion_factor or 0),
            "40s Conv Factor": float(c.conv_40s_factor or 0),
        }
        for c in counts
    ])

    editor = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ID": st.column_config.NumberColumn(disabled=True),
            "Count Name": st.column_config.TextColumn(disabled=True),
            "Conversion Factor": st.column_config.NumberColumn(
                format="%.6f",
                disabled=True
            ),
            "40s Conv Factor": st.column_config.NumberColumn(
                format="%.6f"
            ),
        }
    )

    # -------------------------------------------------------
    # SAVE GRID UPDATES
    # -------------------------------------------------------
    if st.button("💾 Update Count Records"):
        for _, row in editor.iterrows():
            c = session.get(CountMaster, row["ID"])
            if c:
                c.actual_count = safe_float(row["Actual Count"])
                c.spinning_count_eff = safe_float(row["Spinning Count Efficiency (%)"])
                c.std_hank_eff = safe_float(row["Std Hank Efficiency (%)"])

                c.conversion_factor = calc_conversion_factor(
                    c.actual_count,
                    c.spinning_count_eff
                )

                c.conv_40s_factor = safe_float(row["40s Conv Factor"])

        session.commit()
        st.success("✔ Count Master Updated Successfully")
        st.info("Machine Master, Daily Entry & Dashboard updated automatically.")
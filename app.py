import streamlit as st

from modules.master_page import master_page
from modules.daily_entry_page import daily_entry_page
from modules.dashboard_page import dashboard_page
from modules.monthly_report_page import monthly_report_page

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Production Management System",
    layout="wide"
)

# -------------------------------------------------
# GLOBAL LAYOUT FIX (🔑 GAP REMOVAL)
# -------------------------------------------------
st.markdown(
    """
    <style>
    /* Reduce overall page padding */
    .block-container {
        padding-top: 0.2rem;
        padding-bottom: 0.2rem;
    }

    /* Reduce space after radio nav */
    div[role="radiogroup"] {
        margin-bottom: 0.25rem;
    }

    /* Style top navigation */
    div[role="radiogroup"] > label {
        margin-right: 20px;
        font-size: 16px;
        font-weight: 500;
    }

    /* Reduce space after divider */
    hr {
        margin-top: 0.25rem;
        margin-bottom: 0.25re;
    }

    /* Reduce title spacing */
    h1, h2, h3 {
        margin-top: 0.3rem;
        margin-bottom: 0.3rem;
    }

    div[data-testid="stVerticalBlock"] > div {
        gap: 0.6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# TOP NAVIGATION
# -------------------------------------------------
menu = st.radio(
    "",
    ["🏠 Home", "🧵 Masters", "📝 Daily Entry", "📊 Dashboard", "📅 Monthly Report"],
    horizontal=True,
)

st.divider()

# -------------------------------------------------
# PAGE ROUTING
# -------------------------------------------------
if menu == "🏠 Home":
    st.markdown("## 🏭 SREE KADERI AMBAL MILLS LTD")
    st.markdown("### Shanmuganathapuram")

    st.markdown("""
    #### 📌 Production Management System
    This application helps manage:
    - 🧵 Count Master
    - ⚙️ Machine Master
    - 📝 Daily Production Entry
    - 📊 Production Dashboard
    - 📅 Monthly Reports
    """)

elif menu == "🧵 Masters":
    master_page()

elif menu == "📝 Daily Entry":
    daily_entry_page()

elif menu == "📊 Dashboard":
    dashboard_page()

elif menu == "📅 Monthly Report":
    monthly_report_page()
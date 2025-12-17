import streamlit as st

from modules.master_page import master_page
from modules.daily_entry_page import daily_entry_page
from modules.dashboard_page import dashboard_page
from modules.monthly_report_page import monthly_report_page

st.set_page_config(
    page_title="Production Management System",
    layout="wide"
)

# -------------------------------------------------
# TOP NAVIGATION TABS
# -------------------------------------------------
tabs = st.tabs([
    "🏠 Home",
    "🗂 Masters",
    "📝 Daily Entry",
    "📊 Dashboard",
    "📅 Monthly Report",
])

# -------------------------------------------------
# HOME
# -------------------------------------------------
with tabs[0]:
    st.title("🏭 SREE KADERI AMBAL MILLS LTD")
    st.subheader("Shanmuganathapuram")
    st.divider()

    st.markdown("""
    ### 📌 Production Management System

    This application helps you manage:

    - 🧵 **Count Master**
    - ⚙️ **Machine Master**
    - 📝 **Daily Production Entry**
    - 📊 **Production Dashboard**
    - 📅 **Monthly Reports**

    Please select a module from the top navigation.
    """)

# -------------------------------------------------
# MASTERS
# -------------------------------------------------
with tabs[1]:
    master_page()

# -------------------------------------------------
# DAILY ENTRY
# -------------------------------------------------
with tabs[2]:
    daily_entry_page()

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
with tabs[3]:
    dashboard_page()

# -------------------------------------------------
# MONTHLY REPORT
# -------------------------------------------------
with tabs[4]:
    monthly_report_page()
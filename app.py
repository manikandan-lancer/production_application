import streamlit as st

from modules.master_page import master_page
from modules.daily_entry_page import daily_entry_page
from modules.dashboard_page import dashboard_page
from modules.monthly_report_page import monthly_report_page

st.set_page_config(
    page_title="Production Management System",
    layout="wide"
)

# -------------------------------
# TOP NAVIGATION
# -------------------------------
st.markdown(
    """
    <style>
    div[role="radiogroup"] > label {
        margin-right: 20px;
        font-size: 16px;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

menu = st.radio(
    "",
    ["🏠 Home", "🧵 Masters", "📝 Daily Entry", "📊 Dashboard", "📅 Monthly Report"],
    horizontal=True,
)

st.divider()

# -------------------------------
# PAGE ROUTING
# -------------------------------
if menu == "🏠 Home":
    st.title("🏭 SREE KADERI AMBAL MILLS LTD")
    st.subheader("Shanmuganathapuram")

    st.markdown("""
    ### 📌 Production Management System
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

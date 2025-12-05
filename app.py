import streamlit as st
from modules.master_menu import master_page
from modules.daily_entry_page import daily_entry_page
from modules.dashboard_page import dashboard_page

st.sidebar.title("Navigation")

menu = st.sidebar.radio(
    "Go to:",
    ["Home", "Masters", "Daily Entry", "Dashboard"]
)

if menu == "Home":
    st.title("🏭 Production Application")
    st.write("Welcome to the Production Management System.")

elif menu == "Masters":
    master_page()

elif menu == "Daily Entry":
    daily_entry_page()

elif menu == "Dashboard":
    dashboard_page()

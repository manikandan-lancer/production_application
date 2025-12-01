import streamlit as st
from modules.mill_master_page import mill_master_page
from modules.department_master_page import department_master_page
from modules.employee_master_page import employee_master_page
from modules.machine_master_page import machine_master_page
from modules.daily_entry_page import daily_entry_page

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to:",
    [
        "Mill Master",
        "Department Master",
        "Employee Master",
        "Machine Master",
        "Daily Production Entry",
    ]
)

if page == "Mill Master":
    mill_master_page()

elif page == "Department Master":
    department_master_page()

elif page == "Employee Master":
    employee_master_page()

elif page == "Machine Master":
    machine_master_page()

elif page == "Daily Production Entry":
    daily_entry_page()

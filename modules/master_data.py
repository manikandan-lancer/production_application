import streamlit as st

from modules.mill_master_page import mill_master_page
from modules.department_master_page import department_master_page
from modules.employee_master_page import employee_master_page
from modules.machine_master_page import machine_master_page
from modules.shift_master_page import shift_master_page


def master_data_page():
    st.title("Master Data Management")

    menu = st.selectbox(
        "Select Master",
        [
            "Mill Master",
            "Department Master",
            "Employee Master",
            "Machine Master",
            "Shift Master"
        ]
    )

    if menu == "Mill Master":
        mill_master_page()

    elif menu == "Department Master":
        department_master_page()

    elif menu == "Employee Master":
        employee_master_page()

    elif menu == "Machine Master":
        machine_master_page()

    elif menu == "Shift Master":
        shift_master_page()

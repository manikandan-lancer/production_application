import streamlit as st

from modules.masters.mill_master_page import mill_master_page
from modules.masters.department_master_page import department_master_page
from modules.masters.shift_master_page import shift_master_page
from modules.masters.count_master_page import count_master_page
from modules.masters.machine_master_page import machine_master_page
from modules.masters.employee_master_page import employee_master_page


def master_page():
    st.title("⚙️ Master Data Management")

    menu = st.selectbox(
        "Choose Master Section",
        [
            "Mill Master",
            "Department Master",
            "Shift Master",
            "Count / Product Master",
            "Machine Master",
            "Employee Master",
        ]
    )

    if menu == "Mill Master":
        mill_master_page()

    elif menu == "Department Master":
        department_master_page()

    elif menu == "Shift Master":
        shift_master_page()

    elif menu == "Count / Product Master":
        count_master_page()

    elif menu == "Machine Master":
        machine_master_page()

    elif menu == "Employee Master":
        employee_master_page()

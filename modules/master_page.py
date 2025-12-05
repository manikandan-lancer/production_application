import streamlit as st

from modules.count_master_page import count_master_page
from modules.employee_master_page import employee_master_page
from modules.machine_master_page import machine_master_page
from modules.department_master_page import department_master_page


def master_page():
    st.title("🗂 Master Data")

    choice = st.selectbox(
        "Select Master",
        [
            "Count Master",
            "Employee Master",
            "Machine Master",
            "Department Master"
        ]
    )

    if choice == "Count Master":
        count_master_page()

    elif choice == "Employee Master":
        employee_master_page()

    elif choice == "Machine Master":
        machine_master_page()

    elif choice == "Department Master":
        department_master_page()

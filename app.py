import streamlit as st
from modules.master_data import master_data_page
from modules.daily_entry import daily_entry_page

st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to:", ["Master Data", "Daily Entry"])

if menu == "Master Data":
    master_data_page()

elif menu == "Daily Entry":
    daily_entry_page()
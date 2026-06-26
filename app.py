import streamlit as st

from pages.home import home

nav = st.navigation([
    st.Page(home, title='Home', icon=':material/home:'),
])

nav.run()
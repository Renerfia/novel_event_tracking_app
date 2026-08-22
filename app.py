import streamlit as st
from pages import login_page,chat_page


if "user" not in st.session_state:
    st.session_state.user = None




if st.session_state.user == None:
    pg = st.navigation([st.Page(login_page,title="login")],)

else:
    pg = st.navigation([st.Page(chat_page,title="chat")])

pg.run()
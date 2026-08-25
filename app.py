import streamlit as st
from pages import login_page,chat_page, novel_list_page


if "user" not in st.session_state:
    st.session_state.user = None
if "selected_novel" not in st.session_state:
    st.session_state.selected_novel = None
if "selected_chapter" not in st.session_state:
    st.session_state.selected_chapter = None




if st.session_state.user == None:
    pg = st.navigation([st.Page(login_page,title="login")],)

else:
    pg = st.navigation([st.Page(novel_list_page,title="novel list")])

    if st.session_state.selected_novel and st.session_state.selected_chapter:
        pg = st.navigation([st.Page(chat_page,title="chat")])



pg.run()
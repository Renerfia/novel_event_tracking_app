import streamlit as st
from pages import login_page,chat_page, novel_list_page
import nest_asyncio
from tools.supabase import get_current_user,init_supabase, logout

nest_asyncio.apply()


supabase = init_supabase()


if "user" not in st.session_state:
    current_user = get_current_user(supabase)
    if current_user:
        st.session_state.user = current_user
    else:
        st.session_state.user = None    
if "selected_novel" not in st.session_state:
    st.session_state.selected_novel = None
if "selected_chapter" not in st.session_state:
    st.session_state.selected_chapter = None

 #handles logout logic
logout_status = False
if st.button("Logout"):
    logout_status = logout(supabase=supabase)
    
    if logout_status:
        st.session_state.user = None
        st.rerun()
    
        

if st.session_state.user is None or logout_status:
    pg = st.navigation([st.Page(login_page,title="login")],)

else:
    pg = st.navigation([st.Page(novel_list_page,title="novel list")])

    if st.session_state.selected_novel and st.session_state.selected_chapter:
        pg = st.navigation([st.Page(chat_page,title="chat")])



pg.run()
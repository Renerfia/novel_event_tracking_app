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

st.sidebar.title("AI Novel Event Tracking App")

st.sidebar.divider() # ভিজ্যুয়াল সেপারেটর বর্ডার


st.sidebar.write(f"Welcome, {st.session_state.user.email}!")

if st.session_state.user is None :
    pg = st.navigation([st.Page(login_page,title="login")],)

else:
    pg = st.navigation([st.Page(novel_list_page,title="novel list")])

    if st.session_state.selected_novel:
        if st.sidebar.button("Open Chatbot"):
            pg = st.navigation([st.Page(chat_page,title="chat")])



pg.run()
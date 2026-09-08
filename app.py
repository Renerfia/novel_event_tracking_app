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

if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

st.sidebar.title("NovelMind")

st.sidebar.divider() # ভিজ্যুয়াল সেপারেটর বর্ডার




if st.session_state.user is None:
    st.session_state.current_page = "login"
    pg = st.navigation([st.Page(login_page, title="login")])
else:
    st.sidebar.write(
        f"Welcome, {st.session_state.user.email or 'User'}!"
    )

    if st.session_state.current_page not in ("novel_list", "chat"):
        st.session_state.current_page = "novel_list"

    if st.session_state.selected_novel:
        if st.sidebar.button("Open Chatbot"):
            st.session_state.current_page = "chat"
            st.rerun()

        if st.session_state.current_page == "chat":
            st.sidebar.write(
                f"Selected Novel: "
                f"{st.session_state.selected_novel['novel_name']}"
            )
            pg = st.navigation([st.Page(chat_page, title="chat")])
        else:
            pg = st.navigation([st.Page(novel_list_page, title="novel list")])
    else:
        st.session_state.current_page = "novel_list"
        pg = st.navigation([st.Page(novel_list_page, title="novel list")])


pg.run()
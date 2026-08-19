import streamlit as st
from tools.supabase import init_supabase,user_sign_in, user_sign_up, get_current_user

supabase = init_supabase() #The supabase client object

def login_page():
    """Displays a login page"""

    st.title("Login Section")

    email = st.text_input("Enter email here")
    password = st.text_input("Enter your password here",type="password")

    if st.button("Login"):
        try:
            response = user_sign_in(supabase=supabase, email=email, password=password)
            st.session_state.user = response.user
            print("Login successful!")
            st.rerun()

        except Exception as e:
            st.error(f"Error:{e}")

    if st.button("Sign-up"):
        try:
            response = user_sign_up(supabase,email,password)
            st.session_state.user = response.user
            print("Sign-up successful!")
            st.rerun()

        except Exception as e:
            st.error(f"Error:{e}")

def chat_page():
    """The main chat interface or page"""

    user = st.session_state.user

    if not user:
        st.warning("You can't access this page without login.")

    if st.session_state.messages not in st.session_state:
        st.session_state.messages = [
            {"role":"assistant", "content":f"Hello {user.email}! How can I help you?"}
        ]

    #goes through every role based message in the messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_message = st.chat_input("What you thinking?")

    #handles user message
    if user_message:
        st.session_state.messages.append({"role":"user","content":user_message})
        with st.chat_message("user"):
            st.write(user_message)

        with st.chat_message("assistant"):
            #bot logic here
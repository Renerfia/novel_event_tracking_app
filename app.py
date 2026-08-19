import streamlit as st
from tools.supabase import init_supabase,user_sign_in, user_sign_up, get_current_user

supabase = init_supabase() #The supabase client object

if "user" not in st.session_state:
    st.session_state.user = None



if st.session_state.user == None:
    
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import streamlit as st
load_dotenv()

url:str = str(os.environ.get("SUPABASE_URL"))
public_key:str = str(os.environ.get("SUPABASE_PUBLIC_KEY"))
admin_key:str = str(os.environ.get("SUPABASE_PRIVATE_KEY"))

@st.cache_resource
def init_supabase()->Client:
    """Initializes connection with supabase"""
    supabase: Client = create_client(url,public_key)
    return supabase

#Sign in, login, get current user function
#Start
def user_sign_up(supabase:Client,email,password):
    """Returns newly created user object"""
    response = supabase.auth.sign_up(
        {
            "email":email,
            "password": password
        }
    )
    print(f"User created ID:{response.user.id}")
    return response

def user_sign_in(supabase:Client,email,password):
    response= supabase.auth.sign_in_with_password(
        {
            "email":email,
            "password":password
        }
    )

    print(f"Logged in session token:{response.session.access_token}")
    return response

def get_current_user(supabase:Client):
    """Returns user object"""
    user = supabase.auth.get_user()
    print("Current User:", user)
    return user

def logout(supabase:Client):
    supabase.auth.sign_out()
    print("Logged out successfully!")
#End
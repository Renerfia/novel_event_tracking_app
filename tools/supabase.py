from supabase import create_client, Client
from dotenv import load_dotenv
import os
load_dotenv()


url:str = str(os.environ.get("SUPABASE_URL"))
public_key:str = str(os.environ.get("SUPABASE_PUBLIC_KEY"))
admin_key:str = str(os.environ.get("SUPABASE_PRIVATE_KEY"))

supabase: Client = create_client(url,public_key)

def user_sign_up(email,password):
    response = supabase.auth.sign_up(
        {
            "email":email,
            "password": password
        }
    )
    print(f"User created ID:{response.user.id}")
    return response

def user_sign_in(email,password):
    response= supabase.auth.sign_in_with_password(
        {
            "email":email,
            "password":password
        }
    )

    print(f"Logged in session token:{response.session.access_token}")
    return response

def get_current_user():
    user = supabase.auth.get_user()
    print("Current User:", user)


def logout():
    supabase.auth.sign_out()
    print("Logged out successfully!")
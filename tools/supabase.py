from supabase import create_client, Client
from dotenv import load_dotenv
import os
import streamlit as st
from agent.agent import get_embeddings
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
    response = supabase.auth.get_user()
    print("Current User:", response)
    return response.user

def logout(supabase:Client):
    supabase.auth.sign_out()
    print("Logged out successfully!")
#End

def create_novel(supabase: Client, novel_name: str):
    """Creates a novel entry in Supabase and returns True if successful."""
    
    author = get_current_user(supabase)

    if not author:
        raise ValueError("Author isn't verified.")

    try:
        response = supabase.table("novels").insert(
            {
                "novel_name": novel_name,
                "author_id": author.id
            }
        ).execute()

        # Check if Supabase successfully returned the inserted row
        if response.data:
            return response.data

    except Exception as e:
        print(f"There is a problem with data insertion: {e}")
        return False

async def create_chapter(supabase:Client, chapter_name:str, novel_id:str,content:str, max_tokens:int = 1000) -> bool:
    """Add chapter to the database"""

    author = get_current_user(supabase)

    if not author:
        raise ValueError("The author isn't verified.")

    
    try:
        #Verifying if the novel exist or not
        is_novel = (
            supabase
            .table("novels")
            .select("novel_id")
            .eq("novel_id", novel_id)
            .eq("author_id", author.id)
            .single()
            .execute()
            )
        if not is_novel.data:
            raise ValueError("The novel doesn't exist in the database.")

        # Estimate token count (~1 token per 0.75 words)
        words = content.split()
        estimated_tokens = int(len(words) / 0.75)
        
        if estimated_tokens > max_tokens:
            raise ValueError(
                f"Chapter exceeds token budget. Estimated {estimated_tokens} tokens (limit is {max_tokens})."
            )
        try:
            print("Getting embedding...")
            content_embedding = await get_embeddings(content)
            print("Done!")
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {e}") from e

        if not content_embedding:
            raise ValueError("Embedding generation returned an empty vector.")
                                
        

        response = supabase.table("chapters").insert({
            "novel_id":novel_id,
            "chapter_name": chapter_name,
            "chapter_content": content,
            "chapter_content_embedding":content_embedding
        }).execute()

        return bool(response.data)
    except Exception as e:
        print(f"There is an error:{e}")    
        raise



async def vector_search(supabase:Client, novel_id:str, query:str, top_k:int = 3):
    query_embedding = await get_embeddings(query)

    response = supabase.rpc(
        "match_chapters",
        {
            "query_embedding": query_embedding,
        "match_count": top_k,
        "filter_novel_id": novel_id
        }
    ).execute()

    return response.data

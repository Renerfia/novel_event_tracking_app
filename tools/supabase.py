from supabase import create_client, Client
from dotenv import load_dotenv
import os
import streamlit as st
from agent.agent import get_embeddings
from tools.logger import log
load_dotenv()

url:str = str(os.environ.get("SUPABASE_URL"))
public_key:str = str(os.environ.get("SUPABASE_PUBLIC_KEY"))


@st.cache_resource
def init_supabase()->Client:
    """Initializes connection with supabase"""
    try:
        supabase: Client = create_client(url,public_key)
        log("info", "Supabase initialized successfully.")
    except Exception as e:
        log("error", f"Error initializing Supabase: {e}")
        raise
    return supabase

#Sign in, login, get current user function
#Start
def user_sign_up(supabase:Client,email,password):
    """Returns newly created user object"""
    log("debug","User sign up has been called")
    try:
        response = supabase.auth.sign_up(
            {
                "email":email,
                "password": password
            }
        )
        print(f"User created ID:{response.user.id}")
        log("info", f"User created ID:{response.user.id}")
    except Exception as e:
        log("error", f"Error occurred while signing up user: {e}")
        raise
    return response

def user_sign_in(supabase:Client,email,password):

    log("debug","User sign in has been called")

    try:
        response= supabase.auth.sign_in_with_password(
            {
                "email":email,
                "password":password
            }
        )

        
        log("info", f"Logged in successfully! User ID: {response.user.id}")
    except Exception as e:
        log("error", f"Error occurred while signing in user: {e}")
        raise
    return response

def get_current_user(supabase:Client):
    """Returns user object"""

    log("debug","Fetching current user.")

    try:
        session = supabase.auth.get_session()
        if not session:
            return None
        response = supabase.auth.get_user()
        print("Current User:", response)
        log("info", f"Current User: {response.user.id}")
        return response.user
    except Exception as e:
        log("error", f"Error occurred while fetching current user: {e}")
        raise

def logout(supabase: Client) -> bool:
    log("debug", "Logging out user.")
    try:
        supabase.auth.sign_out()
        log("info", "User logged out successfully.")
        
        return True
    except Exception as error:
        log("error", f"Logout failed: {error}")
        return False



#End

def create_novel(supabase: Client, novel_name: str):
    """Creates a novel entry in Supabase and returns True if successful."""

    log("debug", f"Creating novel with name: {novel_name}")

    log("debug", "Fetching current user for novel creation.")
    author = get_current_user(supabase)

    if not author:
        log("error", "Author isn't verified.")
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
            log("info", f"Novel created successfully: {response.data}")
            return response.data

    except Exception as e:
        log("error", f"Failed to create novel. There is a problem with data insertion: {e}")
        return False

def delete_novel(supabase:Client, author_id:str, novel_id:str)->bool:
    """Deletes novel on the novels database"""

    log("debug", f"Attempting to delete novel with ID: {novel_id} for author: {author_id}")

    check = (
    supabase.table("novels")
    .select("novel_id, author_id")
    .eq("novel_id", novel_id)
    .execute()
)

    log("debug", f"Requested deletion for novel: {novel_id}, author: {author_id}")
    log("debug", f"Found novel data: {check.data}")

    response = (supabase.table("novels")
                .delete()
                .eq("novel_id",novel_id)
                .eq("author_id",author_id)
                .execute())
    log("debug", f"DELETION:{response.data}")

    if response.data == []:
        log("warning", f"delete_novel response:{response}")
    return bool(response.data)

async def create_chapter(supabase:Client, chapter_name:str, novel_id:str,content:str, max_tokens:int = 1000) -> bool:
    """Add chapter to the database"""

    log("debug", f"Creating chapter '{chapter_name}' for novel ID: {novel_id}")

    log("debug", "Fetching current user for chapter creation.")
    author = get_current_user(supabase)

    if not author:
        log("error", "The author isn't verified.")
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
            log("error", "The novel doesn't exist in the database.")
            raise ValueError("The novel doesn't exist in the database.")

       
        try:
            log("debug", "Getting embedding...")
            content_embedding = await get_embeddings(content)
            log("debug", "Done!")
        except Exception as e:
            log("error", f"Failed to generate embedding: {e}")
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
        log("error", f"Failed to create chapter. There is an error: {e}")
        raise

def delete_chapter(supabase:Client,novel_id:str,chapter_id:str)->bool:

    log("debug", f"Attempting to delete chapter with ID: {chapter_id} for novel: {novel_id}")

    try:
        response = (supabase
                    .table("chapters")
                    .delete()
                    .eq("novel_id", novel_id)
                    .eq("chapter_id",chapter_id)
                    .execute())
    except Exception as e:
        log("error", f"Failed to delete chapter. There is an error: {e}")
        raise
    return bool(response.data)
    
async def vector_search(supabase:Client, novel_id:str, query:str, top_k:int = 3):

    log("debug", f"Performing vector search for novel ID: {novel_id} with query: '{query}' and top_k: {top_k}")
    query_embedding = await get_embeddings(query)

    try:
        response = supabase.rpc(
            "match_chapters",
            {
                "query_embedding": query_embedding,
            "match_count": top_k,
            "filter_novel_id": novel_id
            }
        ).execute()
    except Exception as e:
        log("error", f"Vector search failed: {e}")
        raise

    return response.data


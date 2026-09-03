import streamlit as st
from tools.supabase import (init_supabase,user_sign_in, user_sign_up, get_current_user, create_novel, create_chapter,vector_search,logout,delete_novel,delete_chapter)
from tools.converter import extract_epub_text
from agent.agent import get_response, get_embeddings,get_summary,get_full_prompt
import asyncio
from tools.logger import log
from tools.chunk import chunk_text

supabase = init_supabase() #The supabase client object

def login_page():
    """Displays a login page"""

    st.title("Login Section")

    email = st.text_input("Enter email here")
    password = st.text_input("Enter your password here",type="password")

    if st.button("Login"):
        try:
            response = user_sign_in(supabase=supabase, email=email, password=password)
            if response and response.user:
                st.session_state.user = response.user
                st.toast("Login successful!",icon="✅")
                st.rerun()
            else:
                st.write("Login failed.")

        except Exception as e:
            st.error(f"Error:{e}")

    if st.button("Sign-up"):
        try:
            response = user_sign_up(supabase,email,password)

            if response and response.user:
                st.session_state.user = response.user
                st.toast("Sign-up successful!",icon="✅")
                st.rerun()

            else:
                st.error("Sign-up failed.")

        except Exception as e:
            st.error(f"Error:{e}")

def novel_list_page():

     #handles logout logic
    logout_status = False
    if st.sidebar.button("Logout"):
        logout_status = logout(supabase=supabase)
        if logout_status:
            st.session_state.user = None
            st.rerun()
            
    #handles back button
    if st.sidebar.button("back.."):
        st.session_state.selected_novel = None
        st.rerun()


    user = st.session_state.user
   

    #user verification
    if not user:
        st.warning("You can't access this page without login. Please refresh the page.")
        return

    if "selected_novel" not in st.session_state:
        st.session_state.selected_novel = None

    # Get all novels belonging to the current user
    log("debug", f"Fetching novels for user ID: {user.id}") 
    all_novel = (
        supabase
        .table("novels")
        .select("*")
        .eq("author_id", user.id)
        .execute()
    )

    novels = all_novel.data

    st.title("Your Novels")

    #checks if author has existing novel or not
    if not novels:
        st.write("No novel has been found.")
        log("info", "No novels found for the user.")

    log("info", f"Fetched {len(novels)} novels for user ID: {user.id}")

    #selected_novel display  logic
    if st.session_state.selected_novel is not None:
        the_novel = st.session_state.selected_novel

        st.subheader(f"Novel Name: {the_novel['novel_name']}")
        novel_id = the_novel["novel_id"]
        

        #THE CHAPTER LOGIC IS HERE
        #returns chapters of a novel
        log("debug", f"Fetching chapters for novel ID: {novel_id}")
        chapters = supabase.table("chapters").select("*").eq("novel_id",novel_id).execute()
        chapters = chapters.data #so we get List[dict]

        if not chapters:
            st.write("There's no chapter of this novel.")
            log("info", f"No chapters found for novel ID: {novel_id}")
        if "selected_chapter" not in st.session_state:
            st.session_state.selected_chapter = None

        #what happens after selected chapter found. for now this logic is handled by app.py
        if st.session_state.selected_chapter is not None:
            selected_chapter = st.session_state.selected_chapter
            with st.container(border=True):
                

                st.subheader(f"The chapter name:{selected_chapter["chapter_name"]}")
                st.write("\n",selected_chapter["chapter_content"])

        #list of chapters
        else:
            for i, chapter in enumerate(chapters,start=1):
                with st.container(border=True):
                    st.title(chapter["chapter_name"])
                    st.write(f"Total length:{len(chapter["chapter_content"])}")

                    #more option button
                    with st.popover("More option"):
                        if st.button("Delete the chapter.",key=f"delete button for chapter:{i}"):
                            chapter_deletion_status = delete_chapter(supabase=supabase,
                                                                     novel_id=st.session_state.selected_novel["novel_id"],
                                                                     chapter_id=chapter["chapter_id"])
                            if chapter_deletion_status:
                                st.toast("chapter has been deleted.")
                                st.rerun()
                    #open button
                    if st.button(label="Open",key=f"chapter {i} button"):
                        st.session_state.selected_chapter = chapter
                        st.rerun()
                        
            #CREATE NEW CHAPTER LOGIC
            with st.container(border=True):
                st.title("Create a new chapter")
                chapter_name = st.text_input("chapter name")

                #UPLOADED FILE LOGIC
                uploaded_file = st.file_uploader("upload chapter .txt file here",type=["txt"])
                
                
                
                if st.button("Create a new chapter"):

                    if not chapter_name:
                        st.warning("Please enter a name")

                    with st.spinner("Creating a new chapter..."):
                        if uploaded_file is not None:
                        
                            log("info",f"Uploaded file name: {uploaded_file.name}")
                            st.toast("Reading the uploaded file...")
                        
                            if uploaded_file.name.endswith(".txt"):
                                chapter_content = uploaded_file.read().decode("utf-8")
                        
                                chapter_size = len(chapter_content) #getting the size of the chapter
                                log("info",f"Size of the chapter is: {chapter_size} characters")
                        
                                                #chunking if the chapter size is greater than 5000 characters
                                if  not chapter_size > 5000:
                                    chunks = [chapter_content]
                        
                                st.toast("Chunking the chapter content...")
                                log("info","Chunking the chapter content...")
                                chunks = chunk_text(chapter_content,chunk_size=5000)
                        
                                log("info",f"Total chunks created: {len(chunks)}")
                        
                                summarized_chunks = ""
                        
                                st.toast("Starting to summarize each chunk...")
                                log("debug","Starting to summarize each chunk...")
                                for i,chunk in enumerate(chunks,start=1):
                                    log("info",f"Processing chunk {i}...")
                                    summarized_chunk = asyncio.run(get_summary(chunk))

                                    summarized_chunks += summarized_chunk + "\n"

                                    log("info",f"Chunk {i} summarized successfully.")

                                if summarized_chunks == "":
                                    st.warning("Summarization failed. Please check the logs for more details.")
                                    log("error","Summarization failed. No summarized content generated.")
                                
                        
                        #embedding happens inside the create_chapter function
                        response = asyncio.run(create_chapter(supabase,
                                                chapter_name=chapter_name,
                                                novel_id=the_novel["novel_id"],
                                                content=summarized_chunks
                                                ))
                        if response:
                            st.toast("chapter creation is done!")
                            st.rerun()

                
    else:
        # Display novels as cards/list items if not selected_novel
        for novel in novels:
            with st.container(border=True):
                st.subheader(novel["novel_name"])

                with st.popover("⋮"):
                    if st.button("Delete",key=f"delete button for novel_id:{novel['novel_id']}"):
                        status = delete_novel(supabase=supabase,novel_id=novel['novel_id'],author_id=user.id)
                        if status:
                            st.toast(f"{novel['novel_name']} has been deleted")
                            st.rerun()

                #opens the novel
                if st.button(
                    "Open",
                    key=f"open_{novel['novel_id']}"
                ):
                    st.session_state.selected_novel = novel #here we select our novel
                    st.rerun()
                

        #create a new novel logic
        with st.container(border=True):
            st.subheader("Create a novel")
            new_novel_name = st.text_input("The novel name")

            #the new novel create button
            if st.button("Create"):
                if new_novel_name:
                    st.write(f"{new_novel_name} has been created!")
                    create_novel(supabase,new_novel_name)
                    st.rerun()
                else:
                    st.error("Please enter a valid name")

            


def chat_page():
    """The main chat interface or page"""

    if st.button("Back.."):
        st.session_state.selected_chapter = None
        st.rerun()

    user = get_current_user(supabase=supabase)


    if not user:
        st.warning("You can't access this page without login.")
        st.session_state.user = None
        
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role":"assistant", "content":f"Hello {user.email}! How can I help you?"}
        ]

    #goes through every role based message in the messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    

    #handles user message
    user_message = st.chat_input("What you thinking?")
    if user_message:
        st.session_state.messages.append({"role":"user","content":user_message})
        with st.chat_message("user"):
            st.write(user_message)

        #LLM response
        the_novel = st.session_state.selected_novel
        memories = asyncio.run(vector_search(supabase=supabase,novel_id=the_novel["novel_id"],query=user_message))
        print(f"The memories:\n{memories}")
        full_prompt = get_full_prompt(user_query=user_message,memories=memories)
        with st.chat_message("assistant"):
            response = get_response(full_prompt)
            st.write(response)
            st.session_state.messages.append({"role":"assistant","content":response})
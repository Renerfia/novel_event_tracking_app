import streamlit as st
from tools.supabase import init_supabase,user_sign_in, user_sign_up, get_current_user, create_novel
from agent.agent import get_response

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
                print("Login successful!")
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
                print("Sign-up successful!")
                st.rerun()

            else:
                st.error("Sign-up failed.")

        except Exception as e:
            st.error(f"Error:{e}")

def novel_list_page():

    user = st.session_state.user

    #user verification
    if not user:
        st.warning("You can't access this page without login.")
        return

    if "selected_novel" not in st.session_state:
        st.session_state.selected_novel = None

    # Get all novels belonging to the current user
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
        

    #selected_novel display  logic
    if st.session_state.selected_novel is not None:
        the_novel = st.session_state.selected_novel

        st.subheader(f"Novel Name: {the_novel['novel_name']}")
        novel_id = the_novel["novel_id"]
        

        #THE CHAPTER LOGIC IS HERE
        #returns chapters of a novel
        chapters = supabase.table("chapters").select("*").eq("novel_id",novel_id).execute()
        chapters = chapters.data #so we get List[dict]

        if not chapters:
            st.write("There's no chapter of this novel.")
        if "selected_chapter" not in st.session_state:
            st.session_state.selected_chapter = None

        if st.session_state.selected_chapter is not None:
            selected_chapter = st.session_state.selected_chapter
            with st.container(border=True):
                

                st.subheader(f"The chapter name:{selected_chapter["chapter_name"]}")
                st.write("\n",selected_chapter["chapter_content"])

        else:
            for i, chapter in enumerate(chapters,start=1):
                with st.container(border=True):
                    st.title(chapter["name"])
                    st.write(f"Total length:{len(chapter["chapter_content"])}")
                    if st.button(label="Open",key=f"chapter {i} button"):
                        st.session_state.selected_chapter = chapter
                        st.rerun()
                        

            with st.container(border=True):
                st.title("Create a new chapter")
                chapter_name = st.text_input("chapter name")

                if not chapter_name:
                    st.warning("Please enter a name")

                pass #for later
                

        


        

    else:
        # Display novels as cards/list items if not selected_novel
        for novel in novels:
            with st.container(border=True):
                st.subheader(novel["novel_name"])


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
            if st.button("Create"):
                if new_novel_name:
                    st.write(f"{new_novel_name} has been created!")
                    create_novel(supabase,new_novel_name)
                    st.rerun()

                else:
                    st.error("Please enter a valid name")

def chat_page():
    """The main chat interface or page"""

    user = st.session_state.user

    if not user:
        st.warning("You can't access this page without login.")

    if "messages" not in st.session_state:
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

        #LLM response
        
        with st.chat_message("assistant"):
            response = get_response(user_message)
            st.write(response)
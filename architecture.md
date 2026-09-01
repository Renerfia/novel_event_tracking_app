# Project Architecture

## Overview

This project is a small AI-assisted library for remembering the contents of a novel.
It is built for a writer who wants to ask questions about earlier chapters without manually searching through the whole manuscript.

The application stores each chapter as a shortened summary and a vector embedding.
When the writer asks a question, the application turns the question into an embedding, searches for the most relevant chapter summaries, and gives those results to a language model to produce an answer.

The application is currently a Streamlit web app backed by Supabase.

## Main Technologies

- **Python 3.13 or newer**: The application language.
- **Streamlit**: Builds the web interface and manages the interactive page reruns.
- **Supabase**: Provides authentication and the database.
- **Pydantic AI**: Connects the application to language models and the embedding model.
- **Groq**: Runs the chapter-summary model.
- **Google Gemini**: Runs the response model and creates vector embeddings.
- **nest-asyncio**: Allows asynchronous AI/database-related functions to be called from Streamlit's execution environment.

The package dependencies and minimum Python version are defined in `pyproject.toml`.

## Directory Structure

```text
.
├── app.py                 Application entry point and navigation
├── pages.py               Streamlit page functions and user workflows
├── agent/
│   └── agent.py           AI agents, embeddings, prompts, and AI helpers
├── tools/
│   └── supabase.py        Supabase client, authentication, CRUD, and vector search
├── README.md              Short project description
└── pyproject.toml         Project metadata and dependencies
```

## Runtime Flow

When Streamlit starts the application, `app.py` performs the following work:

1. It enables nested asyncio support with `nest_asyncio`.
2. It creates or retrieves a cached Supabase client.
3. It checks Supabase for the currently authenticated user.
4. It initializes session-state values for the current user, selected novel, and selected chapter.
5. It shows the login page when there is no authenticated user.
6. It shows the novel list page for an authenticated user.
7. If both a novel and a chapter are selected, it shows the chat page instead.

Streamlit reruns the script after most button and form interactions. The values in `st.session_state` preserve the selected user, novel, chapter, and chat messages across those reruns.

## Application Layers

### `app.py`: Entry Point and Routing

`app.py` is the application entry point. It does not implement novel or AI behavior itself. Its main responsibilities are:

- Configure nested asyncio support.
- Initialize Supabase.
- Restore the authenticated user from Supabase.
- Initialize navigation-related session state.
- Select and run the appropriate Streamlit page.

Navigation is conditional:

- Unauthenticated users can access only `login_page`.
- Authenticated users normally access `novel_list_page`.
- Selecting a novel and a chapter switches the active page to `chat_page`.

### `pages.py`: User Interface and Workflows

This file contains the three user-facing page functions.

#### Login and sign-up

`login_page` collects an email and password. The Login button calls `user_sign_in`; the Sign-up button calls `user_sign_up`. When Supabase returns a user, that user is stored in session state and the application reruns.

#### Novel and chapter management

`novel_list_page` first loads novels belonging to the current user from the `novels` table.
The writer can:

- Create a novel.
- Open a novel.
- Delete a novel.
- View the chapters belonging to the selected novel.
- Open a chapter.
- Delete a chapter.
- Upload a chapter as a UTF-8 `.txt` file.

When a chapter file is uploaded, its text is sent to `get_summary`. The resulting summary is passed to `create_chapter`, which generates the embedding and stores the summary and embedding in Supabase.

#### Chat

`chat_page` displays a chat interface for the selected novel and chapter context. The current implementation searches by the selected novel, not by the selected chapter.

For each user question, it:

1. Creates an embedding for the question.
2. Calls the Supabase `match_chapters` RPC function.
3. Requests up to three matching chapter records.
4. Formats the returned content and similarity scores into a prompt.
5. Sends that prompt to the response agent.
6. Displays the response in the chat.

The conversation is stored in `st.session_state.messages` for the current Streamlit session.

### `agent/agent.py`: AI Services

This module defines three Pydantic AI components:

- `summary_agent`: Uses `groq:openai/gpt-oss-120b` to reduce a long chapter to a summary of no more than 700 words.
- `response_agent`: Uses `google:gemini-3.6-flash` to answer questions using the retrieved memories.
- `embedding_agent`: Uses Google's `gemini-embedding-2` model with 768 dimensions.

The helper functions provide the application-facing AI API:

- `get_summary(text)` asynchronously summarizes chapter text.
- `get_embeddings(text)` asynchronously returns the first embedding vector for text.
- `get_full_prompt(user_query, memories)` combines a question with retrieved chapter memories.
- `get_response(text)` synchronously runs the response agent and returns its output.

The response model does not search the database itself. Retrieval happens before the response model is called, and the retrieved content is included in the prompt as context.

### `tools/supabase.py`: Data and Authentication Access

This module owns the Supabase client and most database operations.

#### Client setup

The module loads environment variables with `python-dotenv` and expects:

- `SUPABASE_URL`
- `SUPABASE_PUBLIC_KEY`

`init_supabase` is cached with `st.cache_resource`, so the application reuses the client during Streamlit's lifetime.

#### Authentication operations

- `user_sign_up` creates a Supabase Auth account.
- `user_sign_in` signs a user in with email and password.
- `get_current_user` reads the current Supabase session and returns its user.
- `logout` signs the user out.

#### Novel operations

- `create_novel` verifies the current user and inserts a row into `novels` with the novel name and the user's ID.
- `delete_novel` deletes a novel only when both its ID and author ID match the request.

#### Chapter operations

- `create_chapter` verifies the author owns the target novel, checks an estimated token limit, generates an embedding, and inserts the chapter.
- `delete_chapter` deletes a chapter using its chapter ID and novel ID.

#### Retrieval

`vector_search` embeds the question and calls the Supabase RPC function `match_chapters`. It passes the question embedding, a result limit, and the novel ID filter. The RPC is expected to perform vector similarity search against stored chapter embeddings and return chapter content with similarity information.

## Data Model and Database Contract

The Python code expects at least these database structures.

### `novels` table

- `novel_id`: Novel identifier.
- `novel_name`: Display name.
- `author_id`: Supabase Auth user ID of the owner.

### `chapters` table

- `chapter_id`: Chapter identifier.
- `novel_id`: Identifier of the parent novel.
- `chapter_name`: Display name.
- `chapter_content`: Stored chapter summary.
- `chapter_content_embedding`: Vector embedding with 768 dimensions.

### `match_chapters` RPC function

The application calls this function with:

- `query_embedding`: The 768-dimensional embedding for the question.
- `match_count`: Maximum number of results.
- `filter_novel_id`: Novel whose chapters should be searched.

The returned records are expected to include `chapter_content` and `similarity`, because both fields are used to build the response prompt.

Row-level security, foreign keys, indexes, vector extension setup, and the SQL definition of `match_chapters` are not present in this repository. They must be configured in the Supabase project for the application to work securely and completely.

## End-to-End Data Flows

### Adding a chapter

```text
Writer uploads .txt file
        |
        v
pages.py reads and decodes UTF-8 text
        |
        v
summary_agent creates a short summary
        |
        v
create_chapter verifies user and novel ownership
        |
        v
embedding_agent creates a 768-dimensional vector
        |
        v
Supabase stores chapter name, summary, and vector
```

### Asking a question

```text
Writer submits a question
        |
        v
embedding_agent embeds the question
        |
        v
match_chapters performs filtered vector search in Supabase
        |
        v
get_full_prompt combines the question and matching summaries
        |
        v
response_agent generates the answer
        |
        v
Streamlit displays the answer and stores the message in session state
```

## Important Current Behavior

- The application summarizes chapters before storing them, so retrieval currently searches summaries rather than the original uploaded text.
- The uploaded file must be a UTF-8 `.txt` file. PDF and DOCX support is not implemented.
- Chapter creation has a default estimated token limit of 1,000 tokens after summarization.
- The chat page searches all chapters in the selected novel. The selected chapter controls navigation but is not used as a search filter.
- Chat messages live only in Streamlit session state and are not persisted to Supabase.
- The response is generated synchronously after retrieval, while summary and embedding calls are asynchronous and bridged with `asyncio.run`.
- The application depends on external credentials and model availability at runtime.

## Security and Reliability Notes

Authentication is handled through Supabase Auth, and the novel list is filtered by the authenticated user's ID. Novel creation and chapter creation also verify ownership in Python.

The database should still enforce ownership with Supabase Row Level Security policies. Client-side or Python-side checks alone are not sufficient protection if the public Supabase key can be used by another client.

The application currently surfaces many exceptions directly in Streamlit or the console. Production hardening would normally add structured error handling, validation for missing environment variables, upload-size limits, and clearer handling for model/API failures.

## Typical Startup

Install the dependencies declared in `pyproject.toml`, provide the required Supabase and model-provider credentials in the environment, and start Streamlit with:

```bash
streamlit run app.py
```

The browser UI is then used to create an account, create a novel, upload chapters, and ask questions about the stored material.
from pydantic_ai import Agent,AgentRunError, Embedder,ModelHTTPError,RunContext
from pydantic_ai.embeddings import EmbeddingSettings
from pydantic_ai.embeddings.google import GoogleEmbeddingModel
from dotenv import load_dotenv
from tools.logger import log
import asyncio
from supabase import Client


from dataclasses import dataclass



load_dotenv()

#response agent and its functions
@dataclass
class ChatDeps:
    supabase: Client
    novel_id: str

response_agent = Agent(
    model="google:gemini-3.5-flash-lite",
    instructions="You are a novel assistant. Your work is to answer user queries about the novel. You will answer the user queries based on the novel content and your knowledge. If you don't know the answer, you will say 'I don't know'. You will not make up answers.",
    deps_type = ChatDeps
)

#tools for response agent
@response_agent.tool
async def search_novel_memory(
    ctx: RunContext[ChatDeps],
    query: str,
) -> str:
    """Search the selected novel for relevant memories."""

    from tools.supabase import vector_search
    log("info", f"response_agent called search_novel_memory tool with query: {query}")
    memories = await vector_search(
        supabase=ctx.deps.supabase,
        novel_id=ctx.deps.novel_id,
        query=query,
        top_k=3,
    )

    if not memories:
        return "No relevant novel memory was found."

    return "\n".join(
        f"Content: {memory['chapter_content']}\n"
        f"Similarity: {memory['similarity']}"
        for memory in memories
    )

summary_agent = Agent(
    model="groq:openai/gpt-oss-120b",
    instructions="You are a summary agent. You will summarize large novel chapter or text into short summary not more than 500 words. The summary should contain useful info from the large text."
)

# Embedding model and its  settings
settings = EmbeddingSettings(dimensions=768)
model = GoogleEmbeddingModel(
    "gemini-embedding-2",
    settings=settings
)
embedding_agent = Embedder(model)

def get_full_prompt(user_query: str,message_history:list[dict]) -> str:

    """Construct the full prompt for the response agent."""
    
    message_history = message_history[-5:]  # Keep only the last 5 messages
    history_str = "\n".join(
       f"{msg['role']}: {msg['content']}" for msg in message_history
    )

    full_prompt = (
        f"User query: {user_query}\n"
        f"Message History:\n{history_str}\n")
    return full_prompt

#def get_response(text:str)->str:
    #"""Get response from LLM"""
    #try:
        #response = response_agent.run_sync(text)
        #log("info", f"Response from LLM: {response.output}")
        #return response.output
    #except Exception as e:
        #log("error", f"Error occurred while fetching response: {e}")
        #raise 

async def get_embeddings(text:str):
    """Get embeddings of text"""

    
    log("debug", f"Getting embeddings for text: {text}")
    print("Getting embeddings...")
    try:
        embeddings = await embedding_agent.embed_query(text)
        return embeddings.embeddings[0]
    except Exception as e:
        log("error", f"Error occurred while fetching embeddings: {e}")
        raise

async def get_summary(text:str)->str:
    log("debug", f"Getting summary for text: {text}")
    try:
        response = await summary_agent.run(text)
        return response.output
    except Exception as e:
        log("error", f"Error occurred while fetching summary: {e}")
        if "429" in str(e):
            log("error", "Rate limit exceeded. Please try again later.")
            await asyncio.sleep(2)
        raise

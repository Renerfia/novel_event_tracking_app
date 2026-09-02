from pydantic_ai import Agent,AgentRunError, Embedder,ModelHTTPError
from pydantic_ai.embeddings import EmbeddingSettings
from pydantic_ai.embeddings.google import GoogleEmbeddingModel
from dotenv import load_dotenv
from tools.logger import log
import asyncio

load_dotenv()

response_agent = Agent(
    model="google:gemini-3.5-flash-lite",
    instructions="You are a novel assistant. Your work is to read the 'memory' section give correct answer to the user."

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

def get_full_prompt(user_query: str, memories) -> str:

    log("debug", "preparing user prompt")
    joined_memories = "".join(
        f"memory-{i} contains:content:{memory["chapter_content"]},similarity_score:{memory["similarity"]}\n"
        for i, memory in enumerate(memories, start=1)
    )
    log("info", f"joined memories: {joined_memories}")
    return f"Question:{user_query}\n\nmemories:\n{joined_memories}"

def get_response(text:str)->str:
    """Get response from LLM"""
    try:
        response = response_agent.run_sync(text)
        log("info", f"Response from LLM: {response.output}")
        return response.output
    except Exception as e:
        log("error", f"Error occurred while fetching response: {e}")
        raise 

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

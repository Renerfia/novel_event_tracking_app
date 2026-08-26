from pydantic_ai import Agent,AgentRunError, Embedder
from pydantic_ai.embeddings import EmbeddingSettings
from pydantic_ai.embeddings.google import GoogleEmbeddingModel
from dotenv import load_dotenv

load_dotenv()

response_agent = Agent(
    model="google:gemini-3.6-flash",
    instructions="You are a novel assistant. Your work is to read the 'memory' section give correct answer to the user."

)

summary_agent = Agent(
    model="groq:openai/gpt-oss-120b",
    instructions="You are a summary agent. You will summarize large novel chapter or text into short summary not more than 700 words. The summary should contain usefull info from the large text."
)

# Embedding model and its  settings
settings = EmbeddingSettings(dimensions=768)
model = GoogleEmbeddingModel(
    "gemini-embedding-2",
    settings=settings
)
embedding_agent = Embedder(model)

def get_full_prompt(user_query: str, memories) -> str:
    joined_memories = "".join(
        f"memory-{i} contains:content:{memory["chapter_content"]},similarity_score:{memory["similarity"]}\n"
        for i, memory in enumerate(memories, start=1)
    )
    return f"Question:{user_query}\n\nmemories:\n{joined_memories}"

def get_response(text:str)->str:
    """Get response from LLM"""
    response = response_agent.run_sync(text)

    return response.output

async def get_embeddings(text:str):
    """Get embeddings of text"""

    text = text.strip()
    print("Getting embeddings...")
    embeddings = await embedding_agent.embed_query(text)

    return embeddings.embeddings[0]

async def get_summary(text:str)->str:
    response = await summary_agent.run(text)
    return response.output


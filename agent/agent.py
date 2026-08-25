from pydantic_ai import Agent,AgentRunError, Embedder
from pydantic_ai.embeddings import EmbeddingSettings
from pydantic_ai.embeddings.google import GoogleEmbeddingModel
from dotenv import load_dotenv

load_dotenv()

response_agent = Agent(
    model="google:gemini-3.6-flash",
    instructions="You are a novel assistant. Your work is to read the 'memory' section give correct answer to the user."

)



# Embedding model and its  settings
settings = EmbeddingSettings(dimensions=768)
model = GoogleEmbeddingModel(
    "gemini-embedding-2",
    settings=settings
)
embedding_agent = Embedder(model)

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

def get_summary()
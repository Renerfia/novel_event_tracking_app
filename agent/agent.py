from pydantic_ai import Agent,AgentRunError
from dotenv import load_dotenv

load_dotenv()

response_agent = Agent(
    model="google:gemini-3.6-flash",
    instructions="You are a novel assistant. Your work is to read the 'memory' section give correct answer to the user."

)

def get_response(text:str)->str:
    """Get response from LLM"""
    response = response_agent.run_sync(text)

    return response.output

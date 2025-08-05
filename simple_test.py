# agent_invoke.py

import os
from utils.state import QueryState
from agents.external_agent import ExternalAgent
from dotenv import load_dotenv

load_dotenv()   

def run_agent():
    # Create the state
    state = QueryState(
        role="admin",       # You can change this to "developer", "analyst", etc.
        mode="external",      # Must match your agent's design
        query="What is the latest news on the stock market?"  # Sample query
    )

    # Create and run the agent
    agent = ExternalAgent(state)
    response = agent.get_response()

    # Print the response
    print("\n=== Agent Response ===")
    print(response)

if __name__ == "__main__":
    run_agent()

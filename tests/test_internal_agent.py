# test_internal_agent.py
from utils.state import QueryState
from agents.internal_agent import InternalAgent

def test_internal_agent():
    """Test the internal agent functionality"""
    print("Testing Internal Agent...")
    
    # Create a test state
    state = QueryState("learner", "internal", "Explain about autonomous AI Agents?")
    
    # Initialize the internal agent
    agent = InternalAgent(state)
    
    # Get response
    response = agent.get_response()
    
    print(f"Query: {state.query}")
    print(f"Role: {state.role}")
    print(f"Mode: {state.mode}")
    print(f"Response: {response}")
    print("-" * 50)


if __name__ == "__main__":
    print("ICLeaf-P1 Internal Agent Test Suite")
    print("=" * 50)
    
    test_internal_agent()
        
    print("Test suite completed!") 
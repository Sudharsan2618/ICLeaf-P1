# test_relevant_query.py
import json
from utils.state import QueryState
from agents.internal_agent import InternalAgent

def test_relevant_queries():
    """Test the internal agent with relevant queries"""
    
    # Test queries that should match our inserted data
    test_queries = [
        "Explain about autonomous AI Agents?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        # Create state and agent
        state = QueryState("learner", "internal", query)
        agent = InternalAgent(state)
        
        # Get response
        response = agent.get_response()
        
        # Parse and display the response
        try:
            response_data = json.loads(response)
            print(f"Answer: {response_data['answer'][:200]}...")
            print(f"Confidence: {response_data['confidence_score']:.3f}")
            print(f"Sources: {response_data['sources_used']}")
            print(f"Related Topics: {response_data['related_topics']}")
            
            if response_data['internal_documents']:
                print(f"\nTop Document: {response_data['internal_documents'][0]['title']}")
                print(f"Relevance Score: {response_data['internal_documents'][0]['relevance_score']:.3f}")
        
        except json.JSONDecodeError:
            print(f"Raw Response: {response}")

if __name__ == "__main__":
    print("ICLeaf-P1 Internal Agent - Relevant Query Test")
    print("=" * 60)
    test_relevant_queries() 
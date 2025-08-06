# test_structured_output.py
import json
from utils.state import QueryState
from agents.external_agent import ExternalAgent

def test_structured_output():
    """Test the new structured JSON output from external agent"""
    
    # Create a test state
    state = QueryState("learner", "external", "Python machine learning libraries")
    
    # Initialize the external agent
    agent = ExternalAgent(state)
    
    print("Testing structured output from External Agent")
    print("=" * 50)
    print(f"Query: {state.query}")
    print("\nGenerating response...")
    
    # Get the structured response
    response = agent.get_response()
    
    print("\n✅ Structured JSON Response:")
    print(response)
    
    # Parse and display the JSON nicely
    try:
        parsed_response = json.loads(response)
        print("\n📋 Parsed Response Summary:")
        print(f"Answer: {parsed_response.get('answer', 'N/A')[:200]}...")
        print(f"Web Results: {len(parsed_response.get('web_results', []))}")
        print(f"YouTube Results: {len(parsed_response.get('youtube_results', []))}")
        print(f"GitHub Repositories: {len(parsed_response.get('github_repositories', []))}")
        print(f"GitHub Code Files: {len(parsed_response.get('github_code', []))}")
        print(f"Sources Used: {parsed_response.get('sources_used', [])}")
        
        # Display some sample results
        if parsed_response.get('youtube_results'):
            print("\n🎥 Sample YouTube Result:")
            youtube = parsed_response['youtube_results'][0]
            print(f"  Title: {youtube['title']}")
            print(f"  Channel: {youtube['channel']}")
            print(f"  URL: {youtube['url']}")
        
        if parsed_response.get('github_repositories'):
            print("\n📦 Sample GitHub Repository:")
            repo = parsed_response['github_repositories'][0]
            print(f"  Repository: {repo['repository']}")
            print(f"  Stars: {repo['stars']}")
            print(f"  URL: {repo['url']}")
            
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print("Raw response:", response)

if __name__ == "__main__":
    test_structured_output() 
# test_internal_agent.py
import json
from utils.state import QueryState
from agents.internal_agent import InternalAgent
from retrievers.pinecone_retriever import PineconeRetriever

def test_pinecone_retriever():
    """Test the Pinecone retriever functionality"""
    print("Testing Pinecone Retriever...")
    
    retriever = PineconeRetriever()
    
    # Test structured retrieval
    query = "give me the summary of the movie 'Avatar: The Way of Water'"
    results = retriever.retrieve_structured(query)
    
    print(f"Query: {query}")
    print(f"Results: {json.dumps(results, indent=2)}")
    print(f"Number of documents: {len(results['internal_documents'])}")
    print(f"Confidence score: {results['confidence_score']}")
    print(f"Related topics: {results['related_topics']}")
    print(f"Sources used: {results['sources_used']}")
    print("-" * 50)

def test_internal_agent():
    """Test the internal agent functionality"""
    print("Testing Internal Agent...")
    
    # Create a test state
    state = QueryState("learner", "internal", "What are the best practices for Python development?")
    
    # Initialize the internal agent
    agent = InternalAgent(state)
    
    # Get response
    response = agent.get_response()
    
    print(f"Query: {state.query}")
    print(f"Role: {state.role}")
    print(f"Mode: {state.mode}")
    print(f"Response: {response}")
    print("-" * 50)

def test_document_addition():
    """Test adding documents to Pinecone"""
    print("Testing Document Addition...")
    
    retriever = PineconeRetriever()
    
    # Sample documents to add
    sample_documents = [
        {
            "id": "doc_001",
            "title": "Python Best Practices",
            "content": "Python best practices include using virtual environments, following PEP 8 style guidelines, writing docstrings, and using type hints. Always use meaningful variable names and write clean, readable code.",
            "source": "knowledge_base",
            "category": "programming",
            "tags": ["python", "best-practices", "coding"]
        },
        {
            "id": "doc_002", 
            "title": "Machine Learning Fundamentals",
            "content": "Machine learning fundamentals include supervised learning, unsupervised learning, and reinforcement learning. Key concepts include feature engineering, model selection, and evaluation metrics.",
            "source": "training_material",
            "category": "ai",
            "tags": ["machine-learning", "ai", "algorithms"]
        }
    ]
    
    for doc in sample_documents:
        success = retriever.add_document(
            document_id=doc["id"],
            title=doc["title"],
            content=doc["content"],
            source=doc["source"],
            category=doc["category"],
            tags=doc["tags"]
        )
        print(f"Added document '{doc['title']}': {'Success' if success else 'Failed'}")
    
    print("-" * 50)

if __name__ == "__main__":
    print("ICLeaf-P1 Internal Agent Test Suite")
    print("=" * 50)
    
    # Test Pinecone retriever
    test_pinecone_retriever()
    
    # Test internal agent
    # test_internal_agent()
    
    # Test document addition (uncomment when you have Pinecone configured)
    # test_document_addition()
    
    print("Test suite completed!") 
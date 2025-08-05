# test_github_api.py
import os
from dotenv import load_dotenv
from retrievers.web_retriever import WebRetriever

def test_github_search():
    """Test the GitHub search functionality"""
    load_dotenv()
    
    # Initialize the web retriever
    retriever = WebRetriever()
    
    # Test query - using a programming-related query to ensure GitHub search is triggered
    test_query = "Python machine learning library"
    
    print(f"Testing GitHub search for: '{test_query}'")
    print("=" * 50)
    
    # Test GitHub search specifically
    github_results = retriever._github_search(test_query)
    
    if github_results:
        print("✅ GitHub search successful!")
        print("Results:")
        print(github_results)
    else:
        print("❌ GitHub search failed or returned no results")
        print("This could be due to:")
        print("- Missing GITHUB_TOKEN in .env file")
        print("- Invalid GitHub token")
        print("- Token doesn't have search permissions")
        print("- Network issues")
        print("- Query not programming-related (GitHub search only works for programming queries)")

def test_github_search_with_non_programming_query():
    """Test GitHub search with a non-programming query to show filtering"""
    load_dotenv()
    
    retriever = WebRetriever()
    test_query = "cooking recipes"
    
    print(f"\nTesting GitHub search for non-programming query: '{test_query}'")
    print("=" * 60)
    
    github_results = retriever._github_search(test_query)
    
    if github_results:
        print("✅ GitHub search returned results (unexpected for non-programming query)")
        print("Results:")
        print(github_results)
    else:
        print("✅ GitHub search correctly filtered out non-programming query")
        print("This is expected behavior - GitHub search only works for programming-related queries")

if __name__ == "__main__":
    test_github_search()
    test_github_search_with_non_programming_query()

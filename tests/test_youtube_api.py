# test_youtube_api.py
import os
from dotenv import load_dotenv
from retrievers.web_retriever import WebRetriever

def test_youtube_search():
    """Test the YouTube search functionality"""
    load_dotenv()
    
    # Initialize the web retriever
    retriever = WebRetriever()
    
    # Test query
    test_query = "Python programming tutorial"
    
    print(f"Testing YouTube search for: '{test_query}'")
    print("=" * 50)
    
    # Test YouTube search specifically
    youtube_results = retriever._youtube_search(test_query)
    
    if youtube_results:
        print("✅ YouTube search successful!")
        print("Results:")
        print(youtube_results)
    else:
        print("❌ YouTube search failed or returned no results")
        print("This could be due to:")
        print("- Missing YOUTUBE_API_KEY in .env file")
        print("- Invalid API key")
        print("- API quota exceeded")
        print("- Network issues")

if __name__ == "__main__":
    test_youtube_search() 
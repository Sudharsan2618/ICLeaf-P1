#!/usr/bin/env python3
# test_import.py
import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all the imports needed for the external agent"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        from utils.state import QueryState
        print("✓ QueryState imported")
        
        from config.settings import GEMINI_API_KEY, GEMINI_MODEL
        print("✓ Settings imported")
        
        from config.prompts import ROLE_PROMPTS
        print("✓ Prompts imported")
        
        from agents.base_agent import BaseAgent
        print("✓ BaseAgent imported")
        
        # Test LangChain imports
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✓ ChatGoogleGenerativeAI imported")
        
        from langchain_core.messages import HumanMessage, SystemMessage
        print("✓ LangChain messages imported")
        
        # Test web retriever imports
        from retrievers.web_retriever import WebRetriever
        print("✓ WebRetriever imported")
        
        # Test external agent import
        from agents.external_agent import ExternalAgent
        print("✓ ExternalAgent imported")
        
        print("\nAll imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    test_imports() 
# tests/test_external_agent.py
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure the parent directory is in sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.state import QueryState
from agents.external_agent import ExternalAgent

class TestExternalAgent(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        # Mock API keys for testing
        self.patcher1 = patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'})
        self.patcher2 = patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
        self.patcher1.start()
        self.patcher2.start()
    
    def tearDown(self):
        """Clean up after tests"""
        self.patcher1.stop()
        self.patcher2.stop()
    
    @patch('agents.external_agent.ChatGoogleGenerativeAI')
    @patch('retrievers.web_retriever.WebRetriever')
    def test_external_agent_basic(self, mock_retriever, mock_model):
        """Test external agent with basic functionality"""
        # Mock the retriever response
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = "Python is a programming language with web search results"
        mock_retriever.return_value = mock_retriever_instance
        
        # Mock the model response
        mock_model_instance = MagicMock()
        mock_model_instance.invoke.return_value.content = "Python is a high-level programming language that is widely used for web development, data science, and automation."
        mock_model.return_value = mock_model_instance
        
        # Test with learner role
        state = QueryState(role="learner", mode="external", query="What is Python?")
        agent = ExternalAgent(state)
        response = agent.get_response()
        
        # Assertions
        self.assertIsInstance(response, str)
        self.assertIn("Python", response)
        self.assertIn("programming", response)

if __name__ == "__main__":
    unittest.main()